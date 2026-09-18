import os
import json
import logging
import pandas as pd
import sys
from collections import defaultdict

# Import custom modules
from extract_and_save_claims import extract_and_save_claims
from get_single_claim import get_claim, filter_claim_by_number
from canonical_transform import (
    get_paths,
    get_all_pointers,
    create_object,
    update_object,
    get_json_value,
    update_value_at_pointer,
    find_matching_elements,
    group_pointers,
    # get_dynamic_json_value  # <-- Uncommented
)
from mapping_path_resolver import get_mapping_file_path

# Setup logging
logging.basicConfig(level=logging.INFO)

# Define directories
dir = os.getcwd().split("src")[0]

# Define consumer type
consumer = sys.argv[1]
logging.info(f"Consumer argument: {consumer}")

# Extract consumer name and scenario type (e.g., 'ACET' and 'Summary' from 'ACET_Summary')
consumer_name = consumer.split('_')[0]
scenario_type = consumer.split('_')[1] if '_' in consumer else 'Summary'

upm_dir = os.path.join(dir, 'target', 'All_Responses', consumer_name, 'UPM_Responses', scenario_type)
ppkg_dir = os.path.join(dir, 'target', 'All_Responses', consumer_name, 'PPKG_Responses', scenario_type)
output_dir = os.path.join(dir, 'target', 'All_Responses', consumer_name, 'Filtered_Responses', scenario_type)
os.makedirs(output_dir, exist_ok=True)

# Match UPM and PPKG files
results = []
if not os.path.exists(upm_dir):
    logging.warning(f"UPM directory not found: {upm_dir}")
elif not os.path.exists(ppkg_dir):
    logging.warning(f"PPKG directory not found: {ppkg_dir}")
else:
    for upm_file in os.listdir(upm_dir):
        if upm_file.endswith('_upm.json'):
            # Validate JSON is not empty/corrupt before adding
            upm_file_path = os.path.join(upm_dir, upm_file)
            try:
                with open(upm_file_path) as f:
                    content = f.read().strip()
                    if not content:
                        logging.warning(f"Empty UPM file skipped: {upm_file}")
                        continue
                    import json as json_check
                    json_check.loads(content)
            except Exception as e:
                logging.warning(f"Invalid UPM JSON skipped: {upm_file} - {e}")
                continue

            memberid_claimnumber = upm_file.replace('_upm.json', '')
            ppkg_claim_file = f"{memberid_claimnumber}_ppkg.json"
            if ppkg_claim_file in os.listdir(ppkg_dir):
                ppkg_file_path = os.path.join(ppkg_dir, ppkg_claim_file)
                # Validate PPKG JSON too
                try:
                    with open(ppkg_file_path) as f:
                        pcontent = f.read().strip()
                        if not pcontent:
                            logging.warning(f"Empty PPKG file skipped: {ppkg_claim_file}")
                            continue
                        pdata = json_check.loads(pcontent)
                        # Skip error responses (404, etc.)
                        if isinstance(pdata, dict) and 'error' in pdata and 'status' in pdata:
                            logging.warning(f"PPKG error response skipped: {ppkg_claim_file} (status={pdata.get('status')})")
                            continue
                        # Skip 'no records found' warnings (meta.warnings[].code == 404)
                        if isinstance(pdata, dict) and not pdata.get('data') and not pdata.get('claim'):
                            warnings = (pdata.get('meta') or {}).get('warnings') or []
                            if warnings:
                                w = warnings[0]
                                logging.warning(
                                    f"PPKG returned no records: {ppkg_claim_file} "
                                    f"(code={w.get('code')}, detail={w.get('detail')})"
                                )
                            else:
                                logging.warning(f"PPKG response has no claim data: {ppkg_claim_file}")
                            continue
                except Exception as e:
                    logging.warning(f"Invalid PPKG JSON skipped: {ppkg_claim_file} - {e}")
                    continue

                claim_number = memberid_claimnumber.split('_')[1]
                results.append({
                    'upm_file_path': upm_file_path,
                    'ppkg_file_path': ppkg_file_path,
                    'claim_number': claim_number,
                    # Full file stem (e.g. '03_BNA2419074500') keeps output files
                    # unique when two testcases share the same claim number.
                    'file_key': memberid_claimnumber
                })

logging.info(f"Found {len(results)} valid UPM/PPKG pairs for validation")

# Extract and save filtered claims
extract_and_save_claims(results, consumer, output_dir, get_claim, filter_claim_by_number)

# Initialize report data
summary_data = []
consolidated_data = []
all_differences = defaultdict(lambda: {'matched': 0, 'total': 0})

# Compare and consolidate claims
for result in results:
    claim_detail = result['file_key']
    try:
        upm_path = result['upm_file_path']
        pp_claim_path = result['ppkg_file_path']

        with open(os.path.join(output_dir, f"{claim_detail}_ppkg.json")) as f:
            fileA = json.load(f)
        if not isinstance(fileA, dict):
            logging.error(f"Malformed or empty JSON for claim {claim_detail} (PPKG)")
            continue

        with open(os.path.join(output_dir, f"{claim_detail}_upm.json")) as f:
            fileB = json.load(f)
        if not isinstance(fileB, dict):
            logging.error(f"Malformed or empty JSON for claim {claim_detail} (UPM)")
            continue

        mapping_path = get_mapping_file_path(consumer, dir)
        excel_data = pd.read_excel(mapping_path)
        excel_data.dropna(subset=[excel_data.columns[0], excel_data.columns[1]], inplace=True)

        # Create mapping dictionary
        mapping = {
            str(excel_data.iloc[i, 1]) + "/": str(excel_data.iloc[i, 0])
            for i in range(len(excel_data))
        }

        new_json = create_object(fileA)
        updated_json = update_object(mapping, fileA, fileB, new_json)

        original_paths_A = get_paths(fileA)
        all_pointers_A = get_all_pointers(original_paths_A)
        original_paths_B = get_paths(fileB)
        all_pointers_B = get_all_pointers(original_paths_B)
        grouped_all_pointers_B = group_pointers(all_pointers_B)
        grouped_all_pointers_A = group_pointers(all_pointers_A)

        lookup = [[key, value + '/'] for key, value in mapping.items()]
        list_mappings = defaultdict(list)
        for items in lookup:
            item = find_matching_elements(all_pointers_B, items[1])
            if not item:
                item = [items[1]]
            for val in item:
                list_mappings[val].extend(find_matching_elements(all_pointers_A, items[0]))

        total_comparisons = 0
        matches = 0

        for key, value in list_mappings.items():
            upm_value = get_json_value(fileB, key)
            for pp_ptrx in value:
                # NOTE: get_dynamic_json_value is not exported by canonical_transform,
                # so fall back to the standard lookup instead of raising NameError
                # (which previously discarded the whole claim silently).
                if pp_ptrx.strip().endswith('attributeName') and 'get_dynamic_json_value' in globals():
                    ptr_val = get_dynamic_json_value(fileA, pp_ptrx)
                else:
                    ptr_val = get_json_value(fileA, pp_ptrx)

                upm_value_str = str(upm_value) if upm_value is not None else ''
                ptr_val_str = str(ptr_val) if ptr_val is not None else ''
                print(f"UPM Path: {key}, UPM Value: {upm_value_str}")
                print(f"PPKG Path: {pp_ptrx}, PPKG Value: {ptr_val_str}")
                if not upm_value_str or upm_value_str.lower() in ["null", "invalid", ""]:
                    match_status = "Not Matched"
                elif upm_value_str == ptr_val_str:
                    match_status = "Matched"
                    matches += 1
                elif upm_value_str in ptr_val_str or ptr_val_str in upm_value_str:
                    match_status = "Partially Matched"
                else:
                    match_status = "Not Matched"
                consolidated_data.append({
                    'Claim Number': claim_detail,
                    'UPM Path': key,
                    'PPKG Path': pp_ptrx,
                    'UPM Value': upm_value_str,
                    'PPKG Value': ptr_val_str,
                    'Match Status': match_status
                })
                total_comparisons += 1
                if upm_value_str == ptr_val_str:
                    update_value_at_pointer(new_json, pp_ptrx, upm_value)
                all_differences[pp_ptrx]['total'] += 1
                if match_status == "Matched":
                    all_differences[pp_ptrx]['matched'] += 1

        coverage_percentage = (matches / total_comparisons) * 100 if total_comparisons > 0 else 0
        summary_data.append({
            'Claim Number': claim_detail,
            'Coverage Percentage': f"{coverage_percentage:.2f}%",
            'Matched Values': f"{matches}/{total_comparisons}"
        })

        with open(os.path.join(output_dir, f"{claim_detail}_transformed_output.json"), 'w') as f:
            json.dump(new_json, f, indent=4)

        logging.info(f"Processed claim: {claim_detail}")

    except Exception as e:
        logging.error(f"Error processing claim number {claim_detail}: {e}")

# Final report
summary_df = pd.DataFrame(summary_data)
consolidated_df = pd.DataFrame(consolidated_data)

report_path = os.path.join(output_dir, f"{consumer}_Report.xlsx")
with pd.ExcelWriter(report_path, engine='xlsxwriter') as writer:
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    consolidated_df.to_excel(writer, sheet_name='Consolidated Data', index=False)

    workbook = writer.book
    worksheet = workbook.add_worksheet("Stats By Element")
    headers = [
        "Common Element Path/Name",
        "# of Occurrences in all testcases",
        "# of Matched Occurrences in all testcases",
        "% of Matched in all testcases"
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)
    row_num = 1
    for right_field, stats in all_differences.items():
        matched = stats['matched']
        total = stats['total']
        percent_matched = (matched / total) * 100 if total > 0 else 0
        worksheet.write(row_num, 0, right_field)
        worksheet.write(row_num, 1, total)
        worksheet.write(row_num, 2, matched)
        worksheet.write(row_num, 3, percent_matched)
        row_num += 1

logging.info("Consolidated report created successfully.")
print("Consolidated report created successfully.")
print(f"Total consolidated rows: {len(consolidated_data)}")
print(f"Total summary rows: {len(summary_data)}")