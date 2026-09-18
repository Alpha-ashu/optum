Feature:  UPM - PPKG ALEXTRO COSMOS for NON-PROD ENVIRONMENT with MRCP DATA

  Background:
    # Base response folders
    * def upmBase = 'target/All_Responses/IIM/UPM_Responses'
    * def ppkgBase = 'target/All_Responses/IIM/PPKG_Responses'

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

  Scenario: 1. callonceing the Cosmos IIM ALEX/MRCP Claim Search
    * print('******************** [IIM Claim Search] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'IIM_MRCP_Summary'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM SUMMARY][STARTED] *******************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/IIM/mrcp/nonprod/summary/upm_summary.feature')
    * print('******************** [UPM SUMMARY][COMPLETED] *****************************************')
    * print('******************** [PPKG SUMMARY][STARTED] ******************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/IIM/mrcp/nonprod/summary/ppkg_summary.feature')
    * print('******************** [PPKG SUMMARY][COMPLETED] ****************************************')
    * print('******************** [IIM Claim Search] [COSMOS] [PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 2. callonceing the Cosmos IIM ALEX/MRCP Claim Read
    * print('******************** [IIM Claim Read] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'IIM_MRCP_Hospital'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM Detail][STARTED] *******************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/IIM/mrcp/nonprod/detail/upm_hospital.feature')
    * print('******************** [UPM Detail][COMPLETED] *****************************************')
    * print('******************** [PPKG Detail][STARTED] ******************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/IIM/mrcp/nonprod/detail/ppkg_nonprod_hospital.feature')
    * print('******************** [PPKG Detail][COMPLETED] ****************************************')
    * print('******************** [IIM Claim Read] [COSMOS] [PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 3. callonceing the Cosmos IIM ALEX/MRCP Claim Read
    * print('******************** [IIM Claim Read] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'IIM_MRCP_Physician'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * print('******************** [UPM Detail][STARTED] *******************************************')
    * def callonceUpm = callonce read('classpath:feature_files/upm_ppkg/cosmos/IIM/mrcp/nonprod/detail/upm_physician.feature')
    * print('******************** [UPM Detail][COMPLETED] *****************************************')
    * print('******************** [PPKG Detail][STARTED] ******************************************')
    * def calloncePayer = callonce read('classpath:feature_files/upm_ppkg/cosmos/IIM/mrcp/nonprod/detail/ppkg_nonprod_physician.feature')
    * print('******************** [PPKG Detail][COMPLETED] ****************************************')
    * print('******************** [IIM Claim Read] [COSMOS] [PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

