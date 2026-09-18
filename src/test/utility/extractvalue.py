import os
import json
import pandas as pd

# Folder containing all JSON response files
folder_path = r"C:\Users\sashra19\Documents\Intellij\Main\ppkg-claims-dark-mode-validator\target\All_Responses\ISET\UPM_Responses\Summary"

# Fields you want to extract
required_fields = [
    "recordTypeDescription",
    "claimSiteId",
    "auditControlNumber",
    "subscriberNumber",
    "groupNumber",
    "dependentCode",
    "firstName",
    "lastName",
    "serviceStartDate",
    "serviceEndDate"
]

def get_claim_references(json_data):
    """Return the list of claimReference records from a UPM response."""
    claim_references = (
        json_data
        .get("searchResult", {})
        .get("searchOutput", {})
        .get("claims", {})
        .get("claimReference", [])
    )

    # A single claimReference can come back as an object instead of a list
    if isinstance(claim_references, dict):
        claim_references = [claim_references]

    return claim_references or []


def get_error_note(json_data):
    """Return a readable note when a response contains no claims."""
    errors = json_data.get("searchResult", {}).get("errors", [])
    if errors:
        return errors[0].get("name") or errors[0].get("description") or "No claims found"
    return "No claims found"


data = []

# Sort so output rows follow the 01_, 02_, 03_ ... file order
json_files = sorted(f for f in os.listdir(folder_path) if f.endswith(".json"))

files_with_claims = 0
files_without_claims = 0

for file_name in json_files:
    file_path = os.path.join(folder_path, file_name)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        claim_references = get_claim_references(json_data)

        # ---- ONE ROW PER RESPONSE FILE ----
        row = {"File Name": file_name}

        if claim_references:
            files_with_claims += 1

            # Member-level values are identical across every claim in the file,
            # so take them from the first claim record (avoids duplicate rows).
            first_claim = claim_references[0]
            for field in required_fields:
                # Keep as text so IDs keep leading zeros (e.g. dependentCode "00")
                row[field] = str(first_claim.get(field, ""))

            row["Claim Count"] = len(claim_references)
            row["Status"] = "OK"
        else:
            files_without_claims += 1

            for field in required_fields:
                row[field] = ""

            row["Claim Count"] = 0
            row["Status"] = get_error_note(json_data)

        data.append(row)

    except Exception as e:
        print(f"Error processing {file_name}: {e}")

# Create DataFrame with a stable column order
columns = ["File Name"] + required_fields + ["Claim Count", "Status"]
df = pd.DataFrame(data, columns=columns)

# Keep identifier columns as text so Excel does not strip leading zeros
for field in required_fields:
    df[field] = df[field].astype(str)

# Export to Excel
output_file = r"C:\Users\sashra19\Documents\Intellij\Main\ppkg-claims-dark-mode-validator\target\All_Responses\ISET\UPM_Responses\Summary.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Summary")

    worksheet = writer.sheets["Summary"]

    # Force text format on the identifier columns
    for col_idx, col_name in enumerate(columns, start=1):
        if col_name in required_fields:
            for row_idx in range(2, len(df) + 2):
                worksheet.cell(row=row_idx, column=col_idx).number_format = "@"

    # Auto-size columns for readability
    for col_idx, col_name in enumerate(columns, start=1):
        width = max([len(str(col_name))] + [len(str(v)) for v in df[col_name]]) + 2
        worksheet.column_dimensions[
            worksheet.cell(row=1, column=col_idx).column_letter
        ].width = min(width, 40)

print(f"Total response files : {len(json_files)}")
print(f"Files with claims    : {files_with_claims}")
print(f"Files without claims : {files_without_claims}")
print(f"Rows written         : {len(df)}")
print(f"Excel created successfully: {output_file}")