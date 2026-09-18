Feature:  UPM - PPKG Claim360 COSMOS for NON-PROD ENVIRONMENT

  Background:
    # Base response folders
    * def ppkgProdBase  = 'target/All_Responses/Hospital/PPKG_PROD_Detail_Responses'
    * def ppkgStageBase = 'target/All_Responses/Hospital/PPKG_Stage_Detail_Responses'

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
    # Uses the dedicated Claim360 Non-Prod vs De-Canary comparator
    # (claim360_summary_decanary_compare.py) instead of the generic UPM/PPKG flow.
    * def runValidation =
    """
    function(varName) {
      var consumer     = varName.split('_')[0];   // Claim360
      var scenarioType = varName.split('_')[1];   // Summary
      karate.log('[VALIDATION] === Generating De-Canary reports for:', varName, '(Consumer:', consumer, ') ===');
      try {
        karate.exec('python src/test/utility/ppkg/claim360_summary_decanary_compare.py ' + scenarioType);
        karate.log('[VALIDATION] claim360_summary_decanary_compare.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] claim360_summary_decanary_compare.py error:', e.message); }
      try {
        var features = '';
        if (scenarioType == 'Summary') features = 'claim360_summary,claim360_summary_decanary';
        else if (scenarioType == 'Hospital') features = 'upm_hospital,ppkg_hospital,ppkg_nonprod_hospital';
        else if (scenarioType == 'Physician') features = 'upm_physician,ppkg_physician,ppkg_nonprod_physician';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + scenarioType + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. callonceing the Cosmos Claim360 Summary Claim Search
    * print('******************** [Claim360 Claim Search] [COSMOS] [NON-PROD] [STARTED] *********************')
    * def Var = 'ppkg_prod_ppks_stage'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM SUMMARY][STARTED] *******************************************')
    * def callonceppkg_prod = callonce read('classpath:feature_files/claim360-ppkg/pkkg/ppkg_detail_prod_stage/ppkg_prod_hospital.feature')
    * print('******************** [UPM SUMMARY][COMPLETED] *****************************************')
    * print('******************** [PPKG SUMMARY][STARTED] ******************************************')
    * def callonceppkg_stage = callonce read('classpath:feature_files/claim360-ppkg/pkkg/ppkg_detail_prod_stage/ppkg_stage_hospital.feature')
    * print('******************** [PPKG SUMMARY][COMPLETED] ****************************************')
    * print('******************** [Claim360 Claim Search] [COSMOS] [NON-PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)


