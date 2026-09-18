Feature: UPM - PPKG ISET COSMOS for PROD ENVIRONMENT V2

  Background:
    # Base response folders
    * def upmBase = 'target/All_Responses/ISET/UPM_Responses'
    * def ppkgBase = 'target/All_Responses/ISET/PPKG_Responses'

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
      var failures = [];
      karate.log('[VALIDATION] === Generating reports for:', varName, '(Consumer:', consumer, ') ===');
      try {
        karate.exec('python src/test/utility/upm_ppkg_validation/Main.py ' + varName);
        karate.log('[VALIDATION] Main.py completed for', varName);
      } catch(e) { failures.push('Main.py: ' + e.message); karate.log('[VALIDATION][ERROR] Main.py failed:', e.message); }
      try {
        karate.exec('python src/test/utility/upm_ppkg_validation/report.py ' + varName);
        karate.log('[VALIDATION] report.py completed for', varName);
      } catch(e) { failures.push('report.py: ' + e.message); karate.log('[VALIDATION][ERROR] report.py failed:', e.message); }
      try {
        var scenarioType = varName.split('_')[1];
        var features = '';
        if (scenarioType == 'Summary') features = 'upm_summary,ppkg_summary,ppkg_nonprod_summary';
        else if (scenarioType == 'Hospital') features = 'upm_hospital,ppkg_hospital,ppkg_nonprod_hospital';
        else if (scenarioType == 'Physician') features = 'upm_physician,ppkg_physician,ppkg_nonprod_physician';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + scenarioType + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION][WARN] performance report error:', e.message); }

      // Fail loudly instead of silently reporting success
      if (failures.length > 0) {
        karate.fail('[VALIDATION] Validation step(s) failed: ' + failures.join(' | '));
      }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. ISET COSMOS PROD ENVIRONMENT Summary
    * print('******************** [ISET Claim Search] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'ISET_Summary'
    * def scenarioType = Var.split('_')[1]
    # Actually delete stale responses from the previous run (was previously never invoked)
    * eval cleanResponseFolder(upmBase + '/' + scenarioType)
    * eval cleanResponseFolder(ppkgBase + '/' + scenarioType)
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM SUMMARY][STARTED] *******************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/ISET/summary/upm_summary.feature')
    * print('******************** [UPM SUMMARY][COMPLETED] *****************************************')
    * print('******************** [PPKG SUMMARY][STARTED] ******************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/ISET/summary/ppkg_summary.feature')
    * print('******************** [PPKG SUMMARY][COMPLETED] ****************************************')
    * print('******************** [IIM Claim Search] [COSMOS] [PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

#  Scenario: 2. ISET COSMOS PROD ENVIRONMENT HOSPITAL
#    * print('******************** [ISET HOSPITAL] [COSMOS] [PROD] [STARTED] *********************')
#    * def Var = 'ISET_Hospital'
#    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
#    * print('******************** [UPM SUMMARY][STARTED] *******************************************')
#    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/ISET/read-claim-details/hospital/upm_hospital.feature')
#    * print('******************** [UPM SUMMARY][COMPLETED] *****************************************')
#    * print('******************** [PPKG SUMMARY][STARTED] ******************************************')
#    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/ISET/read-claim-details/hospital/ppkg_hospital.feature')
#    * print('******************** [PPKG SUMMARY][COMPLETED] ****************************************')
#    * print('******************** [IIM HOSPITAL] [COSMOS] [PROD] [COMPLETED] *******************')
#    # --- Validation and Report Generation ---
#    * eval runValidation(Var)
#    * print('[DONE] Scenario completed, validated, and cleaned:', Var)
#
#  Scenario: 3. ISET COSMOS PROD ENVIRONMENT PHYSICIAN
#    * print('******************** [ISET PHYSICIAN] [COSMOS] [PROD] [STARTED] *********************')
#    * def Var = 'ISET_Physician'
#    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
#    * print('******************** [UPM SUMMARY][STARTED] *******************************************')
#    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/ISET/read-claim-details/physician/upm_physician.feature')
#    * print('******************** [UPM SUMMARY][COMPLETED] *****************************************')
#    * print('******************** [PPKG SUMMARY][STARTED] ******************************************')
#    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/ISET/read-claim-details/physician/ppkg_physician.feature')
#    * print('******************** [PPKG SUMMARY][COMPLETED] ****************************************')
#    * print('******************** [IIM PHYSICIAN] [COSMOS] [PROD] [COMPLETED] *******************')
#    # --- Validation and Report Generation ---
#    * eval runValidation(Var)
#    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

