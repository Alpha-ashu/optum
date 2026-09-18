import json
from openpyxl import Workbook

def extract_json_pointers(obj, path=""):
    pointers = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}/{k}"
            pointers.extend(extract_json_pointers(v, new_path))
    elif isinstance(obj, list):
        # Only process the first element (index 0) to avoid repeated paths
        if obj:
            new_path = f"{path}/0"
            pointers.extend(extract_json_pointers(obj[0], new_path))
    else:
        pointers.append(path)
    return pointers

# Use the absolute path to your JSON file
json_file_path = r'C:\Users\sashra19\Documents\Intellij\Main\ppkg-claims-dark-mode-validator\mapping\mapping.json'

with open(json_file_path, 'r') as f:
    data = json.load(f)

pointers = extract_json_pointers(data)

# Keep only unique pointer paths (preserve first-seen order)
unique_pointers = list(dict.fromkeys(pointers))

wb = Workbook()
ws = wb.active
ws.title = "JSON Pointers"
for idx, pointer in enumerate(unique_pointers, 1):
    ws.cell(row=idx, column=1, value=pointer)

wb.save('json_pointers.xlsx')