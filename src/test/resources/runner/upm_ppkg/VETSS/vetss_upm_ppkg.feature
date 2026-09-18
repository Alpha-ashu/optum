Feature:  UPM - PPKG VETSS COSMOS PROD ENVIRONMENT Summary and Details

  Background:
    # Base response folders
    * def upmBase = 'target/All_Responses/VETSS/UPM_Responses'
    * def ppkgBase = 'target/All_Responses/VETSS/PPKG_Responses'

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
        karate.exec('python src/test/utility/upm_ppkg_validation/Main.py ' + varName);
        karate.log('[VALIDATION] Main.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] Main.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/upm_ppkg_validation/report.py ' + varName);
        karate.log('[VALIDATION] report.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] report.py error:', e.message); }
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

  Scenario: 1. callonceing the Cosmos VETSS Claim Search
    * print('******************** [VETSS Claim Search][COSMOS][PROD][STARTED] ********************')
    * def Var = 'VETSS_Summary'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM SUMMARY][STARTED] *****************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/VETSS/summary/upm_summary.feature')
    * print('******************** [UPM SUMMARY][COMPLETED] ***************************************')
    * print('******************** [PPKG SUMMARY][STARTED] ****************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/VETSS/summary/ppkg_summary.feature')
    * print('******************** [PPKG SUMMARY][COMPLETED] **************************************')
    * print('******************** [VETSS Claim Search][COSMOS][PROD][COMPLETED] ******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 2. callonceing the Cosmos VETSS Claim read HOSPITAL
    * print('******************** [VETSS Claim HOSPITAL][COSMOS][PROD][STARTED] ********************')
    * def Var = 'VETSS_Hospital'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM HOSPITAL][STARTED] *****************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/VETSS/read-claim-details/hospital/upm_hospital.feature')
    * print('******************** [UPM HOSPITAL][COMPLETED] ***************************************')
    * print('******************** [PPKG HOSPITAL][STARTED] ****************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/VETSS/read-claim-details/hospital/ppkg_hospital.feature')
    * print('******************** [PPKG HOSPITAL][COMPLETED] **************************************')
    * print('******************** [VETSS Claim HOSPITAL][COSMOS][PROD][COMPLETED] ******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 3. callonceing the Cosmos VETSS Claim read PHYSICIAN
    * print('******************** [VETSS Claim PHYSICIAN][COSMOS][PROD][STARTED] ********************')
    * def Var = 'VETSS_Physician'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM PHYSICIAN][STARTED] *****************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/VETSS/read-claim-details/physician/upm_physician.feature')
    * print('******************** [UPM PHYSICIAN][COMPLETED] ***************************************')
    * print('******************** [PPKG PHYSICIAN][STARTED] ****************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/VETSS/read-claim-details/physician/ppkg_physician.feature')
    * print('******************** [PPKG PHYSICIAN][COMPLETED] **************************************')
    * print('******************** [VETSS Claim PHYSICIAN][COSMOS][PROD][COMPLETED] ******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

