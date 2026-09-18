
import json
import pandas as pd
import re
import logging
from collections import defaultdict
from itertools import chain, groupby

# def get_dynamic_json_value(data, path):
#     # Get the attribute name (e.g., 'deductibleNumber')
#     attr_name = get_json_value(data, path)
#     # Get the parent object
#     parent_path = '/'.join(path.strip('/').split('/')[:-1])
#     parent_obj = get_json_value(data, parent_path)
#     # Fetch the value using the attribute name
#     if isinstance(parent_obj, dict) and attr_name in parent_obj:
#         return parent_obj[attr_name]
#     return ''
def get_value_from_pointer(json_data, pointer):
    keys = [k for k in pointer.strip('/').split('/') if k]
    value = json_data
    try:
        for key in keys:
            if isinstance(value, list):
                key = int(key)
                value = value[key]
            elif isinstance(value, dict):
                value = value.get(key, '')
            else:
                return ''
        return value if value is not None else ''
    except (KeyError, IndexError, ValueError, TypeError):
        return ''

def get_json_value(json_data, combined_pointer):
    pointers = combined_pointer.split('+')
    combined_value = ''
    for pointer in pointers:
        value = get_value_from_pointer(json_data, pointer)
        if value not in [None, '', 'null']:
            combined_value += str(value)
    return combined_value

def update_value_at_pointer(json_data, pointer, new_value):
    keys = [k for k in pointer.strip('/').split('/') if k]
    value = json_data
    try:
        for i, key in enumerate(keys):
            if isinstance(value, list):
                key = int(key)
            if i == len(keys) - 1:
                value[key] = new_value
            else:
                value = value[key]
        return True
    except (KeyError, IndexError, ValueError, TypeError):
        return False

def create_object(obj):
    new_obj = defaultdict(lambda: "Not present in upm")
    if not isinstance(obj, dict):
        logging.warning("Expected dict in create_object, got %s", type(obj).__name__)
        return new_obj
    for key, value in obj.items():
        if isinstance(value, list):
            new_obj[key] = [create_object(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, dict):
            new_obj[key] = create_object(value)
        else:
            new_obj[key] = "Not present in upm"
    return new_obj

def update_object(mappings, fileA, fileB, new_json):
    for i in range(len(mappings)):
        upm_value = get_json_value(fileB, list(mappings.values())[i])
        pp_claim_value = get_json_value(fileA, list(mappings.keys())[i])
        if '/0/' not in list(mappings.values())[i] or '/0/' not in list(mappings.keys())[i]:
            if upm_value == pp_claim_value:
                update_value_at_pointer(new_json, list(mappings.keys())[i], upm_value)
    return new_json

def get_paths(json_obj, current_path=""):
    paths = []
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            new_path = f"{current_path}.{key}" if current_path else key
            paths.extend(get_paths(value, new_path))
    elif isinstance(json_obj, list):
        for index, item in enumerate(json_obj):
            new_path = f"{current_path}[{index}]"
            paths.extend(get_paths(item, new_path))
    else:
        paths.append(current_path)
    return paths

def get_all_pointers(original_paths):
    all_pointers = []
    for text in original_paths:
        text = '/' + text.replace('.', r'/').replace('[', r'/').replace(']', r'/') + '/'
        text = text.replace('//', r'/')
        all_pointers.append(text)
    return all_pointers

def group_pointers(all_pointers):
    grouped_all_pointers = []
    for item in all_pointers:
        parts = re.split(r'(/\d+/)', item)
        digits = parts[1::2]
        text_parts = parts[::2]
        comparer = text_parts[:-1]
        if len(digits) != 0:
            grouped_all_pointers.append([comparer, text_parts, digits])
    return grouped_all_pointers

def find_matching_elements(lst, base_pattern):
    base_parts = re.split(r'(/\d+/)', base_pattern)
    matching_elements = []
    for element in lst:
        parts = re.split(r'(/\d+/)', element)
        if len(parts) == len(base_parts):
            for i in range(1, len(parts), 2):
                parts[i] = base_parts[i]
            if ''.join(parts) == base_pattern:
                matching_elements.append(element)
    return matching_elements

def update_report(upm_path, ppkg_path, upm_value, pp_claim_value, match_status, df):
    new_row = pd.DataFrame([{
        'UPM Path': upm_path,
        'PPPKG Path': ppkg_path,
        'UPM Value': upm_value,
        'PPKG Value': pp_claim_value,
        'Match': match_status
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    return df

if __name__ == '__main__':
    print('inmain')