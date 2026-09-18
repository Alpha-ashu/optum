Feature: TOPS - COB Hospital UPM Legacy vs PPKG COB API Comparison PROD ENVIRONMENT

  Background:
    # Base response folders
    * def upmHospitalBase = 'target/All_Responses/TOPS/UPM_Responses/Hospital'
    * def ppkgHospitalBase = 'target/All_Responses/TOPS/PPKG_Responses/Hospital'

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
      karate.log('[VALIDATION] === Generating reports for:', varName, '===');
      try {
        karate.exec('python src/test/utility/ppkg/cob_compare.py');
        karate.log('[VALIDATION] cob_compare.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] cob_compare.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/performance/generate_performance_report.py');
        karate.log('[VALIDATION] Performance report generated for', varName);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. Comparing the TOPS COB Hospital UPM Legacy and PPKG COB API Claim Details
    * print('******************** [Legacy and PPKG COB Hospital Claim Details] [TOPS] [PROD] [STARTED] *********************')
    * def Var = 'Hospital'
    * eval cleanResponseFolder(upmHospitalBase)
    * eval cleanResponseFolder(ppkgHospitalBase)
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)

    * print('******************** [UPM Legacy COB Hospital][STARTED] *******************************************')
    * def callonceUPM = callonce read('classpath:feature_files/upm_ppkg/tops/cob/hospital/upm_hospital.feature')
    * print('******************** [UPM Legacy COB Hospital][COMPLETED] ****************************************')
    * print('******************** [PPKG COB Hospital][STARTED] *********************************************')
    * def calloncePPKG = callonce read('classpath:feature_files/upm_ppkg/tops/cob/hospital/ppkg_hospital.feature')
    * print('******************** [PPKG COB Hospital][COMPLETED] *******************************************')
    * print('******************** [Legacy and PPKG COB Hospital Claim Details] [TOPS] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

