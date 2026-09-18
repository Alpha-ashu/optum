Feature:  PPKG - Decanary non-prod claim details / summary

  Background:
    # Base response folders. These MUST match the karate.write() paths inside
    # the called feature files AND the response_base / sources.folder values in
    # validation_config/d-canary/ppkg_non-prod_ppkg_decanary.json:
    #   PPKG     -> target/All_Responses/TOPS/PPKG_Responses/<Var>
    #   Decanary -> target/All_Responses/TOPS/Decanary_Responses/<Var>
    * def ppkgBase = 'target/All_Responses/TOPS/PPKG_Responses'
    * def decanaryBase = 'target/All_Responses/TOPS/Decanary_Responses'

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
      } else {
        dir.mkdirs();
      }
      karate.log('[CLEANUP] Cleaned response folder:', path);
    }
    """

    # Helper: wipe BOTH sides for the given Var so every run starts fresh.
    # Without this, stale JSON from a previous run is silently re-validated.
    * def cleanAll =
    """
    function(varName) {
      cleanResponseFolder(ppkgBase + '/' + varName);
      cleanResponseFolder(decanaryBase + '/' + varName);
    }
    """

    # Maps the scenario Var to the DMV validation consumer registered under
    # validation_config/. Add an entry here when a Hospital / Physician
    # config.json is created - no other change is needed.
    * def dmvConsumerByType =
    """
    {
      "Summary": "ppkg_non-prod_ppkg_decanary"
    }
    """

    # Karate feature names used to filter the performance report per scenario.
    * def perfFeaturesByType =
    """
    {
      "Summary":   "ppkg_nonprod_summary,ppkg_decanary_summary",
      "Hospital":  "ppkg_nonprod_hospital,ppkg_decanary_hospital",
      "Physician": "ppkg_nonprod_physician,ppkg_decanary_physician"
    }
    """

    # Helper: run validation and generate reports for the given Var
    * def runValidation =
    """
    function(varName) {
      var scenarioType = varName;
      var consumer = 'TOPS';
      karate.log('[VALIDATION] === Generating reports for:', varName, '(Consumer:', consumer, ', Type:', scenarioType, ') ===');

      // ---- DMV Index Schema Validation (generic, config-driven engine) ----
      var dmvConsumer = dmvConsumerByType[scenarioType];
      if (dmvConsumer) {
        try {
          var out = karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py ' + dmvConsumer);
          karate.log('[VALIDATION] Schema_Validation.py completed for', dmvConsumer, '->', out);
        } catch (e) {
          karate.log('[VALIDATION] Schema_Validation.py error:', e.message);
        }
      } else {
        karate.log('[VALIDATION] No DMV config registered for type', scenarioType, '- skipping schema validation.');
      }

      // ---- Performance report ----
      try {
        var features = perfFeaturesByType[scenarioType] || '';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + scenarioType + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch (e) {
        karate.log('[VALIDATION] performance report error:', e.message);
      }

      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. PPKG - Decanary Claim Details Summary
    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [SUMMARY] [STARTED] ****************************')
    * def Var = 'Summary'
#    * eval cleanAll(Var)
#    * print('******************** [PPKG SUMMARY] [STARTED] *************************************************************')
#    * def ppkgResult = call read('classpath:feature_files/ppkg-ppkg/cosmos/de-canary/summary/non-prod/ppkg_nonprod_summary.feature')
#    * print('******************** [PPKG SUMMARY] [COMPLETED] ***********************************************************')
#    * print('******************** [Decanary SUMMARY] [STARTED] *********************************************************')
#    * def decanaryResult = call read('classpath:feature_files/ppkg-ppkg/cosmos/de-canary/summary/non-prod/ppkg_decanary_summary.feature')
#    * print('******************** [Decanary SUMMARY] [COMPLETED] *******************************************************')
#    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [SUMMARY] [COMPLETED] **************************')
#    # --- Validation and Report Generation ---
    * eval runValidation(Var)
#    * print('[DONE] Scenario completed and validated:', Var)
#
#  Scenario: 2. PPKG - Decanary Claim Details Hospital
#    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [HOSPITAL] [STARTED] ***************************')
#    * def Var = 'Hospital'
#    * eval cleanAll(Var)
#    * print('******************** [PPKG HOSPITAL] [STARTED] ************************************************************')
#    * def ppkgResult = call read('classpath:feature_files/ppkg-ppkg/cosmos/de-canary/detail/hospital/non-prod/ppkg_nonprod_hospital.feature')
#    * print('******************** [PPKG HOSPITAL] [COMPLETED] **********************************************************')
#    * print('******************** [Decanary HOSPITAL] [STARTED] ********************************************************')
#    * def decanaryResult = call read('classpath:feature_files/ppkg-ppkg/cosmos/de-canary/detail/hospital/non-prod/ppkg_decanary_hospital.feature')
#    * print('******************** [Decanary HOSPITAL] [COMPLETED] ******************************************************')
#    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [HOSPITAL] [COMPLETED] *************************')
#    # --- Validation and Report Generation ---
#    * eval runValidation(Var)
#    * print('[DONE] Scenario completed and validated:', Var)
#
#  Scenario: 3. PPKG - Decanary Claim Details Physician
#    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [PHYSICIAN] [STARTED] **************************')
#    * def Var = 'Physician'
#    * eval cleanAll(Var)
#    * print('******************** [PPKG PHYSICIAN] [STARTED] ***********************************************************')
#    * def ppkgResult = call read('classpath:feature_files/ppkg-ppkg/cosmos/de-canary/detail/physician/non-prod/ppkg_nonprod_physician.feature')
#    * print('******************** [PPKG PHYSICIAN] [COMPLETED] *********************************************************')
#    * print('******************** [Decanary PHYSICIAN] [STARTED] *******************************************************')
#    * def decanaryResult = call read('classpath:feature_files/ppkg-ppkg/cosmos/de-canary/detail/physician/non-prod/ppkg_decanary_physician.feature')
#    * print('******************** [Decanary PHYSICIAN] [COMPLETED] *****************************************************')
#    * print('******************** [PPKG - Decanary] [TOPS] [DEV/Decanary] [PHYSICIAN] [COMPLETED] ************************')
#    # --- Validation and Report Generation ---
#    * eval runValidation(Var)
#    * print('[DONE] Scenario completed and validated:', Var)
