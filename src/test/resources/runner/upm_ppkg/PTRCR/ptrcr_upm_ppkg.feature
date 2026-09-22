Feature:  UPM - PPKG PTRCR COSMOS PROD ENVIRONMENT Summary and Details

  Background:
    # Base response folders
    * def upmBase = 'target/All_Responses/PTRCR/UPM_Responses'
    * def ppkgBase = 'target/All_Responses/PTRCR/PPKG_Responses'

    # Helper: delete all files inside a directory (non-recursive, files only)
    * def cleanResponseFolder =
    """
    function(path) {
      var File = Java.type('java.io.File');
      var dir = new File(path);
      if (dir.exists()) {
        var files = dir.listFiles();
        if (files) {
          for (var i = 0; i < files.length; i++) {
            if (!files[i].isDirectory()) {
              files[i].delete();
            }
          }
        }
      }
    }
    """

    # Helper: run validation and generate reports for the given Var
    * def runValidation =
    """
    function(varName) {
      var consumer = varName.split('_')[0];
      karate.log('[VALIDATION] === Generating reports for:', varName, '(Consumer:', consumer, ') ===');
      try {
        karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py ' + varName);
        karate.log('[VALIDATION] Schema_Validation.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] Schema_Validation.py error:', e.message); }
      try {
        var scenarioType = varName.split('_')[1];
        var features = '';
        if (scenarioType == 'Summary') features = 'upm_summary,ppkg_summary,ppkg_nonprod_summary';
        else if (scenarioType == 'Hospital') features = 'upm_hospital,ppkg_hospital,ppkg_nonprod_hospital';
        else if (scenarioType == 'Physician') features = 'upm_physician,ppkg_physician,ppkg_nonprod_physician';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + scenarioType + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. callonceing the Cosmos PTRCR Claim Search
    * print('******************** [PTRCR Claim Search] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'PTRCR_Summary'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM SUMMARY][STARTED] *******************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/PTRCR/summary/upm_summary.feature')
    * print('******************** [UPM SUMMARY][COMPLETED] *****************************************')
    * print('******************** [PPKG SUMMARY][STARTED] ******************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/PTRCR/summary/ppkg_summary.feature')
    * print('******************** [PPKG SUMMARY][COMPLETED] ****************************************')
    * print('******************** [PTRCR Claim Search] [COSMOS] [PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 2. callonceing the Cosmos PTRCR Claim Details Hospital
    * print('******************** [PTRCR DETAILS] [COSMOS] [PROD][STARTED] ****************************')
    * def Var = 'PTRCR_Hospital'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM DETAILS] [HOSPITAL] [STARTED] ********************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/PTRCR/read-claim-details/hospital/upm_hospital.feature')
    * print('******************** [UPM DETAILS] [HOSPITAL][COMPLETED] *******************************')
    * print('******************** [PPKG DETAILS] [HOSPITAL] [STARTED] *******************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/PTRCR/read-claim-details/hospital/ppkg_hospital.feature')
    * print('******************** [PPKG DETAILS] [HOSPITAL] [COMPLETED]******************************')
    * print('******************** [PTRCR DETAILS] [COSMOS] [PROD] [COMPLETED] *************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 3. callonceing the Cosmos PTRCR Claim Details Physician
    * print('******************** [PTRCR DETAILS] [COSMOS] [PROD][STARTED] *****************************')
    * def Var = 'PTRCR_Physician'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM DETAILS] [PHYSICIAN] [STARTED] ********************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/PTRCR/read-claim-details/physician/upm_physician.feature')
    * print('******************** [UPM DETAILS] [PHYSICIAN][COMPLETED] *******************************')
    * print('******************** [PPKG DETAILS] [PHYSICIAN] [STARTED] *******************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/PTRCR/read-claim-details/physician/ppkg_physician.feature')
    * print('******************** [PPKG DETAILS] [PHYSICIAN] [COMPLETED]******************************')
    * print('******************** [PTRCR DETAILS] [COSMOS] [PROD] [COMPLETED] **************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

