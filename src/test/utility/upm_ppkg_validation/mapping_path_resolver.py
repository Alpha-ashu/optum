import os

def get_mapping_file_path(consumer: str, base_dir: str) -> str:
    """
    Returns the full path to the Excel mapping file based on the consumer type.
    Raises ValueError if the consumer type is unknown.
    """
    mapping_paths = {
        "MYUHC_Summary_V1": "MYUHC/MYUHC_Summary_mapping.xlsx",
        "MYUHC_Summary_V2": "MYUHC/MYUHC_Summary_mapping.xlsx",
        "MYUHC_Hospital_V1": "MYUHC/MYUHC_Hospital_mapping.xlsx",
        "MYUHC_Hospital_V2": "MYUHC/MYUHC_Hospital_mapping.xlsx",
        "MYUHC_Physician_V1": "MYUHC/MYUHC_Physician_mapping.xlsx",
        "MYUHC_Physician_V2": "MYUHC/MYUHC_Physician_mapping.xlsx",
        "IIM_Summary": "IIM/IIM_summary_mapping.xlsx",
        "IIM_MRCP_Summary": "IIM/IIM_mrcp_summary_mapping.xlsx",
        "IIM_Hospital": "IIM/IIM_Hospital_mapping.xlsx",
        "IIM_Physician": "IIM/IIM_Physician_mapping.xlsx",
        "VETSS_Summary": "VETSS/VETSS_Summary_mapping.xlsx",
        "VETSS_Physician": "VETSS/VETSS_Physician_mapping.xlsx",
        "VETSS_Hospital": "VETSS/VETSS_Hospital_mapping.xlsx",
        "ISET_Hospital": "ISET/ISET_Hospital_mapping.xlsx",
        "ISET_Physician": "ISET/ISET_Physician_mapping.xlsx",
        "ISET_Summary": "ISET/ISET_Summary_mapping.xlsx",
        "ACET_Physician": "ACET/ACET_Physician_mapping.xlsx",
        "ACET_Hospital": "ACET/ACET_Hospital_mapping.xlsx",
        "ACET_Summary": "ACET/ACET_Summary_mapping.xlsx",
        "OHBSPE_Summary": "OHBSPE/OHBSPE_Summary_mapping.xlsx",
        "OHBSPE_Physician": "OHBSPE/OHBSPE_Physician_mapping.xlsx",
        "PTRCR_Summary": "PTRCR/PTRCR_Summary_mapping.xlsx",
        "PTRCR_Hospital": "PTRCR/PTRCR_Hospital_mapping.xlsx",
        "PTRCR_Physician": "PTRCR/PTRCR_Physician_mapping.xlsx",
        "MEDICA_Summary": "MEDICA/MEDICA_Summary_mapping.xlsx",
        "IIM_MRCP_Physician": "IIM/IIM_mrcp_details_mapping.xlsx",
        "IIM_MRCP_Hospital": "IIM/IIM_mrcp_details_mapping.xlsx"
    }

    if consumer not in mapping_paths:
        raise ValueError(f"Invalid consumer type: {consumer}")

    relative_parts = mapping_paths[consumer].split("/")

    # Current location of the mapping workbooks
    primary = os.path.join(
        base_dir, "src", "test", "resources", "json_mapping",
        "legacy_ppkg", "upm_ppkg", *relative_parts
    )
    if os.path.exists(primary):
        return primary

    # Legacy location kept as a fallback for older checkouts
    legacy = os.path.join(
        base_dir, "src", "test", "utility",
        "validation_mapping", "upm_ppkg_cosmos", *relative_parts
    )
    if os.path.exists(legacy):
        return legacy

    raise FileNotFoundError(
        f"Mapping file for '{consumer}' not found. Looked in:\n  {primary}\n  {legacy}"
    )
