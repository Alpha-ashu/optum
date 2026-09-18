import os
import pandas as pd
import sys


import hardcoding


def calculate_matched_percentage(df):
    grouped = df.groupby('Claim Number').apply(lambda x: pd.Series({
        'Matched Percentage': ((x['Match Status'] == 'Matched') | (x['Match Status'] == 'Partially Matched')).mean() * 100
    }))
    return grouped

def stats_by_element(df):
    grouped = df.groupby('UPM Path').apply(lambda x: pd.Series({
        'Total Count': len(x),
        'Matched Count': (x['Match Status'] == 'Matched').sum(),
        'Partially Matched Count': (x['Match Status'] == 'Partially Matched').sum(),
        'Not Matched Count': (x['Match Status'] == 'Not Matched').sum(),
        'Total Matched Percentage': (((x['Match Status'] == 'Matched') | (x['Match Status'] == 'Partially Matched')).sum() / len(x)) * 100,
        # 'Validated Paths': ', '.join(x.loc[x['Match Status'] == 'Matched', 'UPM Path'].unique())
    }))
    return grouped

# Access the passed variables
# var = "IIM_Hospital"

var = sys.argv[1] # Corrected indentation here
# Define the base directory

dir = os.getcwd().split("src")[0]

# Extract consumer name (e.g., 'ACET' from 'ACET_Summary')
consumer_name = var.split('_')[0]
scenario_type = var.split('_')[1] if '_' in var else 'Summary'

reports_dir = os.path.join(dir, 'target', 'All_Responses', consumer_name, 'ConsolidateReports')

# Ensure the directory exists
if not os.path.exists(reports_dir):
    os.makedirs(reports_dir)

# Define the report directory (consumer-specific with scenario type)
report_dir = os.path.join(dir, 'target', 'All_Responses', consumer_name, 'Filtered_Responses', scenario_type)
if not os.path.exists(report_dir):
    os.makedirs(report_dir)

# Find the summary report file
report_path = None
for file in os.listdir(report_dir):
    if file.endswith('.xlsx'):
        report_path = os.path.join(report_dir, file)
        break

# Load the summary report
if report_path:
    excel_file = pd.ExcelFile(report_path, engine='openpyxl')
    sheet_names = excel_file.sheet_names
    print(sheet_names)
else:
    print(f"Report not found for {var}. Generating empty consolidated report...")
    # Create empty report
    empty_df = pd.DataFrame(columns=['Match Status', 'Claim Number', 'UPM Path', 'PPKG Path', 'UPM Value', 'PPKG Value'])
    empty_match = pd.DataFrame(columns=['Claim Number', 'Matched Percentage'])
    empty_stats = pd.DataFrame(columns=['UPM Path', 'Total Count', 'Matched Count', 'Partially Matched Count', 'Not Matched Count', 'Total Matched Percentage'])
    combined_report_path = os.path.join(reports_dir, f"{var}_report.xlsx")
    with pd.ExcelWriter(combined_report_path, engine='openpyxl') as writer:
        empty_df.to_excel(writer, sheet_name="Final Consolidated Data", index=False)
        empty_match.to_excel(writer, sheet_name="Matched Percentage", index=False)
        empty_stats.to_excel(writer, sheet_name="Stats by Element", index=False)
    print(f"Empty report generated: '{combined_report_path}'")
    sys.exit(0)

# Read the second sheet (index 1)
df1 = pd.read_excel(excel_file, sheet_name=sheet_names[1], engine='openpyxl')

# Check if the required column exists
required_columns = ['Match Status', 'Claim Number', 'UPM Path', 'PPKG Path']
missing_columns = [col for col in required_columns if col not in df1.columns]

if missing_columns or df1.empty:
    print(f"Warning: No validation data available for {var} (missing columns: {missing_columns}, rows: {len(df1)})")
    print(f"Generating empty consolidated report...")
    # Create empty report with proper structure
    empty_df = pd.DataFrame(columns=required_columns + ['UPM Value', 'PPKG Value'])
    empty_match = pd.DataFrame(columns=['Claim Number', 'Matched Percentage'])
    empty_stats = pd.DataFrame(columns=['UPM Path', 'Total Count', 'Matched Count', 'Partially Matched Count', 'Not Matched Count', 'Total Matched Percentage'])
    combined_report_path = os.path.join(reports_dir, f"{var}_report.xlsx")
    with pd.ExcelWriter(combined_report_path, engine='openpyxl') as writer:
        empty_df.to_excel(writer, sheet_name="Final Consolidated Data", index=False)
        empty_match.to_excel(writer, sheet_name="Matched Percentage", index=False)
        empty_stats.to_excel(writer, sheet_name="Stats by Element", index=False)
    print(f"Empty report generated: '{combined_report_path}'")
    sys.exit(0)

# Proceed with the rest of the code
df_matched = df1[df1['Match Status'] == "Matched"]
df_matched_unique = df_matched.drop_duplicates(subset=['Claim Number', 'UPM Path'])
df_matched_unique_final = df_matched_unique.drop_duplicates(subset=['Claim Number', 'PPKG Path'])

df_P_matched = df1[df1['Match Status'] == "Partially Matched"]
df_P_matched_unique = df_P_matched.drop_duplicates(subset=['Claim Number', 'UPM Path'])
df_P_matched_unique_final = df_P_matched_unique.drop_duplicates(subset=['Claim Number', 'PPKG Path'])

df_not_matched = df1[df1['Match Status'] == "Not Matched"]
df_not_matched_unique = df_not_matched.drop_duplicates(subset=['Claim Number', 'UPM Path'])
df_not_matched_unique_final = df_not_matched_unique.drop_duplicates(subset=['Claim Number', 'PPKG Path'])


status_order = {'Matched': 0, 'Partially Matched': 1, 'Not Matched': 2}

df_M_P_match = pd.concat([df_matched_unique_final, df_P_matched_unique_final], ignore_index=True)
df_M_P_match['Status Order'] = df_M_P_match['Match Status'].map(status_order)
df_sorted = df_M_P_match.sort_values(by=['Claim Number', 'UPM Path', 'Status Order'])
df_M_P_match_unique = df_sorted.drop_duplicates(subset=['Claim Number', 'UPM Path'], keep='first')
df_M_P_match_final = df_M_P_match_unique.drop_duplicates(subset=['Claim Number', 'PPKG Path'], keep='first')
df_M_P_match_final = df_M_P_match_final.drop(columns=['Status Order'])

df_final = pd.concat([df_M_P_match_final, df_not_matched_unique_final], ignore_index=True)
df_final['Status Order'] = df_final['Match Status'].map(status_order)
df_sorted = df_final.sort_values(by=['Claim Number', 'UPM Path', 'Status Order'])
df_final = df_sorted.drop_duplicates(subset=['Claim Number', 'UPM Path'], keep='first')
df_final = df_final.drop_duplicates(subset=['Claim Number', 'PPKG Path'], keep='first')
df_final = df_final.drop(columns=['Status Order'])

df_final = hardcoding.validate_match(df_final, var=var)
df_final = df_final.sort_values(by=['Claim Number'])

match = calculate_matched_percentage(df_final)
stats = stats_by_element(df_final)

# Save the combined report in the specified directory
combined_report_path = os.path.join(reports_dir, f"{var}_report.xlsx")

# Create a new Excel writer object
with pd.ExcelWriter(combined_report_path, engine='openpyxl') as writer:
    # Write each DataFrame to a separate sheet
    df_final.to_excel(writer, sheet_name="Final Consolidated Data", index=False)
    match.to_excel(writer, sheet_name="Matched Percentage", index=True)
    stats.to_excel(writer, sheet_name="Stats by Element", index=True)

print(f"The DataFrames have been successfully combined into a single Excel file '{combined_report_path}'.")