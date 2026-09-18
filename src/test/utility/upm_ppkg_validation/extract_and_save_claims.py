# extract_and_save_claims.py
import os
import json
import logging

def extract_and_save_claims(results, var, output_dir, get_claim, filter_claim_by_number):
    matched_count = 0
    for result in results:
        upm_path = result['upm_file_path']
        ppkg_path = result['ppkg_file_path']
        claim_number = result['claim_number']
        # Unique output name so testcases sharing a claim number don't overwrite
        claim_detail = result.get('file_key', claim_number)
        upm, pp_claim = get_claim(upm_path, ppkg_path)

        # Determine the path to UPM claims based on var
        path_to_upm_claims = None
        try:
            if var in ["MYUHC_Summary_V1", "MYUHC_Summary_V2", "MYUHC_Hospital_V1", "MYUHC_Hospital_V2", "MYUHC_Physician_V1", "MYUHC_Physician_V2"]:
                path_to_upm_claims = ["searchResult", "searchOutput", "claims"]
            elif var in ["IIM_Summary", "IIM_MRCP_Summary", "VETSS_Summary", "ISET_Summary", "ACET_Summary", "OHBSPE_Summary", "PTRCR_Summary"]:
                path_to_upm_claims = ["searchResult", "searchOutput", "claims", "claimReference"]
            elif var in ["IIM_Hospital", "IIM_Physician"]:
                path_to_upm_claims = upm.get("soap:Envelope", {}).get("_", {}).get("soap:Body", {}).get("ns2:invokeServiceResponse", {}).get("_", {}).get("return", {}).get("claim", [])

            elif var in ["IIM_MRCP_Physician"]:
                path_to_upm_claims = upm.get("soap:Envelope", {}).get("_", {}).get("soap:Body", {}).get("ns2:invokeServiceResponse", {}).get("_", {}).get("return", {}).get("claim", [])
            elif var in ["IIM_MRCP_Hospital"]:
                path_to_upm_claims = upm.get("soap:Envelope", {}).get("_", {}).get("soap:Body", {}).get("ns2:invokeServiceResponse", {}).get("_", {}).get("return", {}).get("claim", [])

            elif var in ["ISET_Physician", "ISET_Hospital", "ACET_Hospital", "ACET_Physician", "PTRCR_Hospital", "PTRCR_Physician", "VETSS_Physician"]:
                path_to_upm_claims = ["readResult", "readOutput", "claims", "claim"]
            elif var in ["VETSS_Physician","VETSS_Hospital"]:
                path_to_upm_claims = ["readResult", "readOutput", "claims", "claim"]
            elif var == "OHBSPE_Physician":
                path_to_upm_claims = ["readOutput", "readCosmosPhysicianClaimDetailResponse", "claimReference"]
            elif var == "MEDICA_Summary":
                path_to_upm_claims = ["readResult", "readCosmosMemberClaimSummaryResponse","memberClaim"]
            else:
                logging.error(f"Invalid var value: {var}")
                continue
        except Exception as e:
            logging.error(f"Error while extracting upm claim path for {claim_detail}: {e}")
            continue

        # Filter PPKG claim
        filtered_ppkg_claim = None
        if isinstance(pp_claim, dict):
            if "data" in pp_claim and pp_claim["data"]:
                filtered_ppkg_claim = pp_claim["data"][0]
            elif "claim" in pp_claim and pp_claim["claim"]:
                filtered_ppkg_claim = pp_claim["claim"][0]

        # Filter UPM claim
        filtered_claim_upm = None
        if path_to_upm_claims:
            if isinstance(path_to_upm_claims, list):
                filtered_claim_upm = filter_claim_by_number(upm, path_to_upm_claims, claim_number, var)
            else:
                filtered_claim_upm = path_to_upm_claims
        else:
            logging.warning(f"No valid path to upm claims for claim number {claim_number}")

        if filtered_claim_upm is None:
            logging.error(f"UPM claim NOT matched for {claim_detail} (claim number '{claim_number}') - validation will be skipped")
        elif filtered_ppkg_claim is None:
            logging.error(f"PPKG claim NOT found for {claim_detail} - validation will be skipped")
        else:
            matched_count += 1

        os.makedirs(output_dir, exist_ok=True)

        upm_file_path = os.path.join(output_dir, f"{claim_detail}_upm.json")
        with open(upm_file_path, 'w') as f:
            json.dump(filtered_claim_upm, f, indent=4)

        ppkg_file_path = os.path.join(output_dir, f"{claim_detail}_ppkg.json")
        with open(ppkg_file_path, 'w') as f:
            json.dump(filtered_ppkg_claim, f, indent=4)

        logging.debug(f"Claims fetched and saved for claim number {claim_detail}")

    logging.info(f"Extracted {matched_count}/{len(results)} claim pairs successfully")
