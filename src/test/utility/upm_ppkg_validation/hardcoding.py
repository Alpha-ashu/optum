import sys
import re
import pandas as pd



def validate_match(df, var):

    if var in ["MYUHC_Summary_V1", "MYUHC_Summary_V2"]:
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'].str.lower() == 'hospital') &
               (df['PPKG Value'].str.lower() == 'institutional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'

    if var in ["MYUHC_Hospital_V1", "MYUHC_Hospital_V2", "MYUHC_Physician_V1", "MYUHC_Physician_V2"]:
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'].str.lower() == 'hospital') &
               (df['PPKG Value'].str.lower() == 'institutional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':0:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0::0:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'FINALIZED PAID'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'DENIED') &
               (df['PPKG Value'] == 'FINALIZED DENIED'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'

    if var in ["IIM_Summary", "VETSS_Summary"]:
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'].str.lower() == 'hospital') &
               (df['PPKG Value'] .str.lower() == 'institutional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':0:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/npi/') &
               (df['UPM Value'] == '0000000000') &
               (df['PPKG Value'].apply(lambda x: x.isnumeric())), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/detail508Status/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == '104'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'True'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/eftFlag/') &
               (df['UPM Value'] == 'E') &
               (df['PPKG Value'] == 'EDI'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/ambulancePickupZip/') &
               (df['UPM Value'] == '000000000') &
               (df['PPKG Value'] == 'financialLegalEnityNumber'), 'Match Status'] = 'Matched'
        # VETSS
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'].str.lower() == 'hospital') &
               (df['PPKG Value'] .str.lower() == 'institutional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/typeOfClaim/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'

    if var in ["VETSS_Physician"]:
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/checks/0/checkProcessTime/') &
               (df['PPKG Value'].apply(lambda x: x.split('T')[1][:8] if isinstance(x, str) and 'T' in x and len(x.split('T')[1]) >= 8 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/encounterFlag/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/siteId/') &
               (df['PPKG Value'].apply(lambda x: x[:3] if isinstance(x, str) and len(x) >= 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'approved'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'DENIED') &
               (df['PPKG Value'] == 'denied'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatus/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'ORIGINAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/poolLedgerCategoryNumber/') &
               (df['UPM Value'] == '00') &
               (df['PPKG Value'] == 'deductibleCode'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/memberSexCategory/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'Female'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/memberSexCategory/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'Male'), 'Match Status'] = 'Matched'

    if var in ["VETSS_Hospital"]:
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'FINALIZED PAID'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'DENIED') &
               (df['PPKG Value'] == 'FINALIZED DENIED'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'].str.lower() == 'hospital') &
               (df['PPKG Value'].str.lower() == 'institutional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimsSplit/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'True'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimsSplit/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/enteredDate/') &
               (df['PPKG Value'].apply(
                   lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/admissionDate/') &
               (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationDivCode/') &
               (df['PPKG Value'].apply(lambda x: x[:3] if isinstance(x, str) and len(x) >= 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/adjustmentReasonCode/') &
               (df['UPM Value'] == '0000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'

        pattern = re.compile(r'^/lineItems/\d+/revenueCode/$')
        mask1 = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
            df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
            df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)
        )
        df.loc[mask1, 'Match Status'] = 'Matched'
        pattern = re.compile(r'^/reviews/\d+/reviewReasonCode/$')
        mask1 = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
                df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
                df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)
        )
        df.loc[mask1, 'Match Status'] = 'Matched'
        pattern = re.compile(r'^/lineItems/\d+/bpl/$')
        mask2 = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
            df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
            df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)
        )
        df.loc[mask2, 'Match Status'] = 'Matched'
        pattern = re.compile('/systemDrg/')
        mask3 = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
            df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
            df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)
        )
        df.loc[mask3, 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/dischargeHour/') &
            (df['PPKG Value'].apply(lambda x: (str(x).split('T')[1].split(':')[2].split('.')[0]
                if isinstance(x, str) and 'T' in x and len(str(x).split('T')) > 1 and len(str(x).split('T')[1].split(':')) > 2 and '.' in str(x).split('T')[1].split(':')[2]
                    else '')) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/notificationDays/') &
               (df['UPM Value'].str.lower() == '000') &
               (df['PPKG Value'].str.lower() == '0'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/provider/providerNumberHospital/') &
               (df['PPKG Value'].apply(lambda x: str(x)[-7:] if pd.notnull(x) else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/provider/serviceFacilityAddress/zip/') &(df['UPM Value'] == '00000') &
               (df['PPKG Value'].notna()) &(df['PPKG Value'] != ''),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordId/') &
               (df['PPKG Value'].apply(lambda x: (''.join(x.replace(':', ''))[11:13]) if isinstance(x, str) and len(x.replace(':', '')) >= 13 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/reviews/0/reviewDescription/') &
               (df['PPKG Value'].apply(lambda x: x.split(':', 2)[-1] if isinstance(x, str) and x.count(':') >= 2 else '') == df['UPM Value']),'Match Status'] = 'Matched'


    if var in ["IIM_MRCP_Summary"]:
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'].str.lower() == 'physician') &
               (df['PPKG Value'].str.lower() == 'professional'),'Match Status'] = 'Matched'

    # IIM (Maestro)
    if var in ["IIM_Hospital"]:
        df.loc[(df['UPM Path'] == '/claim/claimTypeDescription/') &
               (df['UPM Value'] == 'HOSPITAL') &
               (df['PPKG Value'] == 'Hospital'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/cobLetter/letterNumber/') &
               (df['UPM Value'] == '00') &
               (df['PPKG Value'] == '0{:0{:0{:0{'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'FINALIZED PAID'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimStatusDescription/') &
               (df['UPM Value'] == 'DENIED') &
               (df['PPKG Value'] == 'FINALIZED DENIED'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/postalCodeForDistrict/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'].apply(lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and x.isnumeric()))), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/inventoryControlNumber/') &
               (df['UPM Value'] == '0000000   0000000') &
               (df['PPKG Value'].apply(lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and x.isnumeric()))), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimsSplit/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'True'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimsSplit/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/checks/paymentType/') &
               (df['UPM Value'] == 'E') &
               (df['PPKG Value'] == 'EDI'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/networkManagementFeePercent/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == '0.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/originalAuditControlNumber/') &
               (df['UPM Value'] == '000000000'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/lineItems/0/revenueCode/') &
               (df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) == df['PPKG Value']), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/lineItems/0/reservePercent/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == '0.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'Medical'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/checks/paymentType/') &
               (df['UPM Value'] == 'E') &
               (df['PPKG Value'] == 'EDI'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/notificationNumber/') &
               (df['UPM Value'] == '0000000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'

    if var in ["IIM_Physician"]:
        df.loc[(df['UPM Path'] == '/claim/claimTypeDescription/') &
               (df['UPM Value'] == 'PHYSICIAN') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimsSplit/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'True'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimsSplit/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0::0:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimTypeDescription/') &
               (df['UPM Value'] == 'HOSPITAL') &
               (df['PPKG Value'] == 'INSTITUTIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/reviews/0/reviewPriority/') &
               (df['UPM Value'] == '000') &
               (df['PPKG Value'] == 'E:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'FINALIZED PAID'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/claimStatusDescription/') &
               (df['UPM Value'] == 'DENIED') &
               (df['PPKG Value'] == 'FINALIZED DENIED'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/encounterFlag/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/encounterFlag/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'True'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/checks/paymentType/') &
               (df['UPM Value'] == 'E') &
               (df['PPKG Value'] == 'EDI'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/interestAmount/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == '0.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/reviews/0/reviewPriority/') &
               (df['UPM Value'] == '000') &
               (df['PPKG Value'] == 'I:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claim/reviews/0/reviewReasonCode/') &
               (df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) == df['PPKG Value']), 'Match Status'] = 'Matched'

    #     ISET
    if var in ["ISET_Summary"]:

        df.loc[(df['UPM Path'] == '/detail508Status/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == '104'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/eftFlag/') &
               (df['UPM Value'] == 'E') &
               (df['PPKG Value'] == 'ELECTRONIC'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == 'True'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/ambulancePickupZip/') &
               (df['UPM Value'].isin(['000000000', '0000000'])),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'] == 'Physician') &
               (df['PPKG Value'] == 'Professional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'] == 'Hospital') &
               (df['PPKG Value'] == 'Institutional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/npi/') &
               (df['UPM Value'] == '0000000000') &
               (df['PPKG Value'].apply(lambda x: x.isnumeric())), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimSystemTime/') &
                (df['PPKG Value'].apply(lambda x: x.split('T')[1][:2] + x.split('T')[1][3:5] + x.split('T')[1][6:8] + x.split('.')[-1][:2]if isinstance(x, str) and 'T' in x and '.' in x else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordId/') &
                (df['PPKG Value'].apply(lambda x: (''.join(x.replace(':', ''))[11:13]) if isinstance(x, str) and len(x.replace(':', '')) >= 13 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/reviewDate/') &
                (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/revisedAuditControlNumber/') &
                (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'

    if var in ["ISET_Hospital", "ISET_Physician"]:
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'] == 'PHYSICIAN') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'] == 'HOSPITAL') &
               (df['PPKG Value'] == 'INSTITUTIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/notificationNumber/') &
               (df['UPM Value'].isin(['000000000', '0000000'])),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/notificationNumber/') &
               (df['UPM Value'] == '0000000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'FINALIZED PAID'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimsSplit/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/reserveUsed/') &
               (df['UPM Value'] == '0.00') &
               (df['PPKG Value'] == '99999.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/originalAuditControlNumber/') &
                (df['UPM Value'] == '00000000') &(df['PPKG Value'].notna()) &(df['PPKG Value'] != ''),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/provider/benefitCode/') &
                (df['UPM Value'].isnull()) &(df['PPKG Value'].notna()) &(df['PPKG Value'] != ''),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/systemTime/') &
                (df['PPKG Value'].apply(lambda x: (
                            ':'.join([x.split(':')[3][0:2], x.split(':')[3][2:4], x.split(':')[3][4:6]])
                            if isinstance(x, str) and len(x.split(':')) > 3 and len(x.split(':')[3]) >= 6
                            else None)) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/checks/0/checkProcessTime/') &
                (df['PPKG Value'].apply(lambda x: x.split('T')[1][:8] if isinstance(x, str) and 'T' in x and len(x.split('T')[1]) >= 8 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/siteId/') &
                (df['PPKG Value'].apply(lambda x: x[:3] if isinstance(x, str) and len(x) >= 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/reservePercent/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == '0.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'DENIED') &
               (df['PPKG Value'] == 'FINALIZED DENIED'), 'Match Status'] = 'Matched'
        pattern = re.compile(r'^/lineItems/\d+/revenueCode/$')
        mask =  df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
                df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
                df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x))
        df.loc[mask, 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/notificationNumber/') &
                (df['PPKG Value'].apply(
                        lambda x: x.split(':')[1] if isinstance(x, str) and x.count(':') >= 2 else ''
                    ) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/originalAuditControlNumber/') &
                (df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) == df['PPKG Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/pointOfupm_ppkg/0/code/') &
               (df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) == df['PPKG Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/admitHour/') &
                (df['PPKG Value'].apply(
                        lambda x: x.split('T')[1][6:8] if isinstance(x, str) and 'T' in x and len(x.split('T')[1]) >= 8 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/calculationDate/') &
                (df['PPKG Value'].apply(
                        lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/enteredDate/') &
               (df['PPKG Value'].apply(
                   lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/adjustmentReasonCode/') &
               (df['UPM Value'] == '0000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/closeFlag/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == '000'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/notificationDays/') &
               (df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)
                == df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)),
        'Match Status'
        ] = 'Matched'
        df.loc[(df['UPM Path'] == '/checks/0/paymentTypeDescription/') &
               (df['UPM Value'] == 'ELECTRONIC') &
               (df['PPKG Value'] == 'KEYED'), 'Match Status'] = 'Matched'


    if var == "ACET_Summary":
        pattern = re.compile(r'^/lineItems/\d+/revenueCode/$')
        mask =  df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
                df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
                df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x))
        df.loc[mask, 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'] == 'Physician') &
               (df['PPKG Value'] == 'Professional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/npi/') &
               (df['UPM Value'] == '0000000000') &
               (df['PPKG Value'].apply(lambda x: x.isnumeric())), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/detail508Status/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == '104'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/typeOfClaim/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/systemTime/') &
               (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/recordId/') &
               (df['PPKG Value'].apply(lambda x: (''.join(x.replace(':', ''))[11:13]) if isinstance(x, str) and len(x.replace(':', '')) >= 13 else '') == df['UPM Value']),'Match Status'] = 'Matched'

        df.loc[(df['UPM Path'] == '/claimDetailReference/0/reasonCode/') &
                (df['UPM Value'].apply(lambda x: isinstance(x, str) and x.isnumeric())) &
                (df['PPKG Value'] == '0'),'Match Status'] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/hmoId/') &
            (df.apply(
                lambda row: isinstance(row['PPKG Value'], str)
                            and isinstance(row['UPM Value'], str)
                            and row['PPKG Value'].startswith(row['UPM Value']),
                axis=1
            )),
            'Match Status'
        ] = 'Matched'


    if var == "ACET_Physician":
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'] == 'PHYSICIAN') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[
               (df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'].isin(['PAID', 'DENIED'])) &
               (df['PPKG Value'].isin(['FINALIZED PAID', 'FINALIZED DENIED'])),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatus/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'approved'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/encounterFlag/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[
               (df['UPM Path'] == '/lineItems/0/feeSchedule/') &
               (df['UPM Value'].isin(['HCFA', 'HIAA'])) &
               (df['PPKG Value'].isin(['HCFA*', 'HIAA*'])),'Match Status'] = 'Matched'
        pattern = re.compile(r'^/lineItems/\d+/feeSchedule/$')
        mask = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
               (df['UPM Value'] == 'DISC') & (df['PPKG Value'] == 'DISCOUNT'))
        df.loc[mask, 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/reservePercent/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == 'deductibleCode'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/openReview/') &
               (df['UPM Value'] == '00000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/openReview/') &
               (df['UPM Value'] == '00000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        pattern = re.compile(r'^/reviews/\d+/reviewReasonCode/$')
        mask = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
               df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
               df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x))
        df.loc[mask, 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/reviews/0/reviewPriority/') &
               (df['UPM Value'] == '000') &
               (df['PPKG Value'] == 'I:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/reasonCode/') &
               (df['PPKG Value'] == '0000'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/dciLetterDate/') &
               (df['UPM Value'].isnull()) &(df['PPKG Value'] == '0'),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/planNumber/') &
               (df['UPM Value'] == '0999') &
               (df['PPKG Value'] == '999'), 'Match Status'] = 'Matched'


    if var == "ACET_Hospital":
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'] == 'HOSPITAL') &
               (df['PPKG Value'] == 'Hospital'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimsSplit/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/hospitalNetwork/') &
               (df['UPM Value'] == '000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/recordId/') &
            (df['PPKG Value'].apply(
                lambda x: x.split(':')[2].lstrip('0') if isinstance(x, str) and x.count(':') >= 2 else ''
            ) == df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)),
            'Match Status']= 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['PPKG Value'].apply(
                   lambda x: x.split(':')[1] if isinstance(x, str) and x.count(':') >= 2 else ''
               ) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/calculationDate/') &
            (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),
            'Match Status'
        ] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'


    if var == "OHBSPE_Summary":
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'] == 'Physician') &
               (df['PPKG Value'] == 'Professional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/detail508Status/') &
               (df['UPM Value'] == '1') &
               (df['PPKG Value'] == '104'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/revisedAuditControlNumber/') &
              (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimSystemTime/') &
               (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/typeOfClaim/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/reviewDate/') &
            (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),
            'Match Status'
        ] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/auditControlNumber/') &
            (
                    df['PPKG Value'].apply(
                        lambda x: (re.search(r'^[A-Z]{3}:(\d{8})', x).group(1) + '00') if isinstance(x, str) and re.search(r'^[A-Z]{3}:(\d{8})', x) else ''
                    ) == df['UPM Value']
            ),
            'Match Status'
        ] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/claimSystemTime/') &
            (
                    df['PPKG Value'].apply(
                        lambda x: (
                                x.split('T')[1][:2] + x.split('T')[1][3:5] + x.split('T')[1][6:8] + x.split('.')[1][:2]
                        ) if isinstance(x, str) and 'T' in x and '.' in x else ''
                    ) == df['UPM Value']
            ),
            'Match Status'
        ] = 'Matched'


    if var == "OHBSPE_Physician":
        df.loc[(df['UPM Path'] == '/splitClaimInd/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimStatus/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'ORIGINAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/encounterFlag/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/openReview/') &
               (df['UPM Value'] == '00000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/pfaAmount/') &
               (df['UPM Value'] == '0.00') &
               (df['PPKG Value'] == 'deductibleCode'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/feeSchedule/') &
               (df['UPM Value'] == 'HCFA') &
               (df['PPKG Value'] == 'HCFA*'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/reviews/0/reviewPriority/') &
               (df['UPM Value'] == '000') &
               (df['PPKG Value'] == 'I:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/reservePercent/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == '0.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['PPKG Value'].apply(
                   lambda x: x.split(':')[1] if isinstance(x, str) and x.count(':') >= 2 else ''
               ) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[
            (df['UPM Path'] == '/systemDate/') &
            (
                    df['PPKG Value'].apply(
                        lambda x: f"upm value {x.split(':')[2]}" if isinstance(x, str) and x.count(':') >= 2 else ''
                    ) == df['UPM Value']
            ),
            'Match Status'
        ] = 'Matched'
        pattern = re.compile(r'^/reviews/\d+/reasonCode/$')
        mask = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
                df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
                df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x))
        df.loc[mask, 'Match Status'] = 'Matched'


    if var == "PTRCR_Physician":
        df.loc[(df['UPM Path'] == '/claimStatusDescription/') &
               (df['UPM Value'] == 'PAID') &
               (df['PPKG Value'] == 'approved'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'] == 'PHYSICIAN') &
               (df['PPKG Value'] == 'Professional'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/encounterFlag/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'




    if var == "PTRCR_Hospital":
        df.loc[(df['UPM Path'] == '/claimType/') &
               (df['UPM Value'] == 'M') &
               (df['PPKG Value'] == 'MEDICAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/claimTypeDescription/') &
               (df['UPM Value'] == 'HOSPITAL') &
               (df['PPKG Value'] == 'Hospital'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitIndicator/') &
               (df['UPM Value'] == 'N') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/authorizationNumber/') &
               (df['UPM Value'] == '00000000') &
               (df['PPKG Value'] == ':00000000:0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'

        df.loc[
            (df['UPM Path'] == '/dischargeHour/') &
            (
                df['PPKG Value'].apply(
                    lambda x: (
                        str(x).split('T')[1].split(':')[2].split('.')[0]
                        if isinstance(x, str)
                        and 'T' in x
                        and len(str(x).split('T')) > 1
                        and len(str(x).split('T')[1].split(':')) > 2
                        and '.' in str(x).split('T')[1].split(':')[2]
                        else ''
                    )
                ) == df['UPM Value']
            ),
            'Match Status'
        ] = 'Matched'
        df.loc[(df['UPM Path'] == '/enteredDate/') &
               (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']),'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/adjustmentReasonCode/') &
               (df['UPM Value'] == '0000') &
               (df['PPKG Value'] == '0'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/bpl/') &
               (df['PPKG Value'].apply(lambda x: x.split(':')[2].lstrip('0') if isinstance(x, str) and x.count(':') >= 2 else '') == df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x)),'Match Status']= 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/detailNumber/') &
               (df['UPM Value'] == '01') &
               (df['PPKG Value'] == '1'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/lineItems/0/reservePercent/') &
               (df['UPM Value'] == '0.0') &
               (df['PPKG Value'] == '0.00'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/provider/providerNumberHospital/') &
            (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'
        pattern = re.compile(r'^/reviews/\d+/reviewReasonCode/$')
        mask = df['UPM Path'].apply(lambda x: bool(pattern.match(x))) & (
                df['UPM Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x) ==
                df['PPKG Value'].apply(lambda x: x.lstrip('0') if isinstance(x, str) else x))
        df.loc[mask, 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/siteId/') &
               (df.apply(lambda row: isinstance(row['PPKG Value'], str)and isinstance(row['UPM Value'], str)and row['PPKG Value'].startswith(row['UPM Value']),axis=1)),'Match Status'] = 'Matched'

    if var == "PTRCR_Summary":
        df.loc[(df['UPM Path'] == '/recordTypeDescription/') &
               (df['UPM Value'] == 'Physician') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'

    if var == "MEDICA_Summary":
        df.loc[ (df['UPM Path'] == '/entryDate/') &
                (df['PPKG Value'].apply(lambda x: x.split('T')[0] if isinstance(x, str) and 'T' in x else x) == df['UPM Value']), 'Match Status' ] = 'Matched'


        df.loc[
            (df['UPM Path'].isin(['/providerTin/', '/providerMpin/'])) &
            (df['PPKG Value'].apply(lambda x: str(x).lstrip('0') if pd.notnull(x) else '0') == df['UPM Value'].astype(str)),
            'Match Status'
        ] = 'Matched'

        df.loc[(df['UPM Path'] == '/recordType/') &
               (df['UPM Value'] == 'D') &
               (df['PPKG Value'] == 'PROFESSIONAL'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/splitClaimIndicator/') &
               (df['UPM Value'] == '0') &
               (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/encounterIndicator/') &
                (df['UPM Value'] == '0') &
                (df['PPKG Value'] == 'False'), 'Match Status'] = 'Matched'
        df.loc[(df['UPM Path'] == '/auditControlNumber/') &
               (df['PPKG Value'].apply(lambda x: x[3:] if isinstance(x, str) and len(x) > 3 else '') == df['UPM Value']),'Match Status'] = 'Matched'


    return df
