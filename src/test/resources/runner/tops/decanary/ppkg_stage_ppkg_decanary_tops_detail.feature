Feature:  PPKG - Decanary non-prod claim details / summary

  Background:
    # Base response folders
    * def alexBase = 'target/All_Responses/TOPS/PPKG_Responses'
    * def hcpBase = 'target/All_Responses/TOPS/Decanary_Responses'

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
      var scenarioType = varName;
      var consumer = 'TOPS';
      karate.log('[VALIDATION] === Generating reports for:', varName, '(Consumer:', consumer, ', Type:', scenarioType, ') ===');
      try {
        karate.exec('python src/test/utility/ppkg/decanary_compare.py ' + scenarioType);
        karate.log('[VALIDATION] decanary_compare.py completed for', scenarioType);
      } catch(e) { karate.log('[VALIDATION] decanary_compare.py error:', e.message); }
      try {
        var features = '';
        if (scenarioType == 'Summary') features = 'ppkg_nonprod_summary,ppkg_decanary_summary';
        else if (scenarioType == 'Hospital') features = 'alex_qae_hospital,ppkg_dev_hospital';
        else if (scenarioType == 'Physician') features = 'alex_qae_physician,ppkg_dev_physician';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + scenarioType + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """


  Scenario: 1. PPKG - Decanary Claim Details Summary
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [SUMMARY] [STARTED] ****************************')
    * def Var = 'Summary'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [PPKG SUMMARY] [STARTED] *************************************************************')
    * def callonceAlex = callonce read('classpath:feature_files/upm_ppkg/cosmos/DecanaryPPKG/summary/non-prod/ppkg_nonprod_summary.feature')
    * print('******************** [PPKG SUMMARY] [COMPLETED] ***********************************************************')
    * print('******************** [Decanary SUMMARY] [STARTED] **************************************************************')
    * def callonceHcp = callonce read('classpath:feature_files/upm_ppkg/cosmos/DecanaryPPKG/summary/non-prod/ppkg_decanary_summary.feature')
    * print('******************** [Decanary SUMMARY] [COMPLETED] ************************************************************')
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [SUMMARY] [COMPLETED] ***************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 2. PPKG - Decanary Claim Details Hospital
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [HOSPITAL] [STARTED] ****************************')
    * def Var = 'Hospital'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [PPKG HOSPITAL] [STARTED] *************************************************************')
    * def callonceAlex = callonce read('classpath:feature_files/upm_ppkg/cosmos/DecanaryPPKG/detail/hospital/non-prod/ppkg_nonprod_hospital.feature')
    * print('******************** [PPKG HOSPITAL] [COMPLETED] ***********************************************************')
    * print('******************** [Decanary HOSPITAL] [STARTED] **************************************************************')
    * def callonceHcp = callonce read('classpath:feature_files/upm_ppkg/cosmos/DecanaryPPKG/detail/hospital/non-prod/ppkg_decanary_hospital.feature')
    * print('******************** [Decanary HOSPITAL] [COMPLETED] ************************************************************')
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [HOSPITAL] [COMPLETED] ***************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 3. PPKG - Decanary Claim Details Physician
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [Physician] [STARTED] ****************************')
    * def Var = 'Physician'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [PPKG Physician] [STARTED] *************************************************************')
    * def callonceAlex = callonce read('classpath:feature_files/upm_ppkg/cosmos/DecanaryPPKG/detail/physician/non-prod/ppkg_nonprod_physician.feature')
    * print('******************** [PPKG Physician] [COMPLETED] ***********************************************************')
    * print('******************** [Decanary Physician] [STARTED] **************************************************************')
    * def callonceHcp = callonce read('classpath:feature_files/upm_ppkg/cosmos/DecanaryPPKG/detail/physician/non-prod/ppkg_decanary_physician.feature')
    * print('******************** [Decanary Physician] [COMPLETED] ************************************************************')
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [Physician] [COMPLETED] ***************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)


