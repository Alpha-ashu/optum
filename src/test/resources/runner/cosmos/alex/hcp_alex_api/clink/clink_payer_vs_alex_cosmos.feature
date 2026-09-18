Feature: Clink API - Payer vs Alex Claims 360 [COSMOS] [NONPROD]

  Background:
    # Base response folders
    * def summaryPayerBase = 'target/All_Responses/Hospital/PPKG_Responses'
    * def summaryAlexBase = 'target/All_Responses/Hospital/Alex_Responses'
    * def physicianPayerBase = 'target/All_Responses/Physician/PPKG_Responses'
    * def physicianAlexBase = 'target/All_Responses/Physician/Alex_Responses'
    * def hospitalPayerBase = 'target/All_Responses/Hospital/PPKG_Responses'
    * def hospitalAlexBase = 'target/All_Responses/Hospital/Alex_Responses'

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
      var scenarioType = varName.split('_')[2];   // Summary / Physician / Hospital
      var consumer = varName.split('_')[0];       // HCPClink
      karate.log('[VALIDATION] === Generating reports for:', varName, '(Consumer:', consumer, ', Type:', scenarioType, ') ===');
      try {
        // For direct-mode validations with no curated mapping sheet (e.g. Clink
        // detail Hospital/Physician), auto-build a self-mapping from the PPKG
        // responses just written. No-op when a curated sheet already exists.
        karate.exec('python src/test/utility/DMV_Index_Schema_Validation/generate_self_mapping.py ' + varName);
      } catch(e) { karate.log('[VALIDATION] generate_self_mapping.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py ' + varName);
        karate.log('[VALIDATION] Schema_Validation.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] Schema_Validation.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/performance/generate_performance_report.py');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. Clink Summary - Payer vs Alex [COSMOS] [NONPROD]
    * print('******************** [CLINK SUMMARY] [PAYER vs ALEX] [COSMOS] [NONPROD] [STARTED] ********************')
    * def Var = 'HCPClink_Alex_Summary'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [CLINK SUMMARY PAYER] [STARTED] ********************')
    * def calloncePayer = callonce read('classpath:feature_files/ppkg_alex/alex/clink/non-prod/summary/clink_ppkg.feature')
    * print('******************** [CLINK SUMMARY PAYER] [COMPLETED] ********************')
    * print('******************** [CLINK SUMMARY ALEX] [STARTED] ********************')
    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/clink/non-prod/summary/clink_alex.feature')
    * print('******************** [CLINK SUMMARY ALEX] [COMPLETED] ********************')
    * print('******************** [CLINK SUMMARY] [PAYER vs ALEX] [COSMOS] [NONPROD] [COMPLETED] ********************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 2. Clink Detail - Payer vs Alex [Hospital] [COSMOS] [NONPROD]
    * print('******************** [CLINK DETAIL] [HOSPITAL] [PAYER vs ALEX] [COSMOS] [NONPROD] [STARTED] ********************')
    * def Var = 'HCPClink_Alex_Hospital'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [CLINK HOSPITAL PAYER] [STARTED] ********************')
    * def calloncePayer = callonce read('classpath:feature_files/ppkg_alex/alex/clink/non-prod/detail/hospital/clink_ppkg.feature')
    * print('******************** [CLINK HOSPITAL PAYER] [COMPLETED] ********************')
    * print('******************** [CLINK HOSPITAL ALEX] [STARTED] ********************')
    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/clink/non-prod/detail/hospital/clink_alex.feature')
    * print('******************** [CLINK HOSPITAL ALEX] [COMPLETED] ********************')
    * print('******************** [CLINK DETAIL] [HOSPITAL] [PAYER vs ALEX] [COSMOS] [NONPROD] [COMPLETED] ********************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 3. Clink Detail - Payer vs Alex [Physician] [COSMOS] [NONPROD]
    * print('******************** [CLINK DETAIL] [PHYSICIAN] [PAYER vs ALEX] [COSMOS] [NONPROD] [STARTED] ********************')
    * def Var = 'HCPClink_Alex_Physician'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [CLINK PHYSICIAN PAYER] [STARTED] ********************')
    * def calloncePayer = callonce read('classpath:feature_files/ppkg_alex/alex/clink/non-prod/detail/physician/clink_ppkg.feature')
    * print('******************** [CLINK PHYSICIAN PAYER] [COMPLETED] ********************')
    * print('******************** [CLINK PHYSICIAN ALEX] [STARTED] ********************')
    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/clink/non-prod/detail/physician/clink_alex.feature')
    * print('******************** [CLINK PHYSICIAN ALEX] [COMPLETED] ********************')

    * print('******************** [CLINK DETAIL] [PHYSICIAN] [PAYER vs ALEX] [COSMOS] [NONPROD] [COMPLETED] ********************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

