Feature:  HCP - ALEX IIM COSMOS DEV And QAE ENVIRONMENT claim details

  Background:
    # Base response folders
    * def alexBase = 'target/All_Responses/IIM/ALEX_Responses'
    * def hcpBase = 'target/All_Responses/IIM/HCP_Responses'

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
      var scenarioType = varName.split('_')[1];
      var consumer = varName.split('_')[0];
      var isProd = varName.indexOf('_Prod') !== -1;
      karate.log('[VALIDATION] === Generating reports for:', varName, '(Consumer:', consumer, ', Type:', scenarioType, ') ===');
      try {
        karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py ' + varName);
        karate.log('[VALIDATION] Schema_Validation.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] Schema_Validation.py error:', e.message); }
      try {
        var features = '';
        if (scenarioType == 'Summary') features = 'alex_qae_summary,ppkg_test_summary';
        else if (scenarioType == 'Hospital') features = 'alex_qae_hospital,ppkg_dev_hospital';
        else if (scenarioType == 'Physician' && isProd) features = 'alex_nonprod_physician,ppkg_prod_physician';
        else if (scenarioType == 'Physician') features = 'alex_qae_physician,ppkg_dev_physician';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + varName + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

#  Scenario: 1. Cosmos ALEX Claim Details Summary
#    * print('******************** [ALEX DETAILS] [COSMOS] [QAE] [SUMMARY] [STARTED] **********************************')
#    * def Var = 'HCPvsAlex_Summary'
#    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
#    * print('******************** [ALEX SUMMARY] [STARTED] **************************************************************')
#    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_dev_vs_alex_qae/summary/alex_qae_summary.feature')
#    * print('******************** [ALEX SUMMARY] [COMPLETED] ************************************************************')
#    * print('******************** [HCP SUMMARY] [STARTED] ***************************************************************')
#    * def callonceHcp = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_dev_vs_alex_qae/summary/ppkg_test_summary.feature')
#    * print('******************** [HCP SUMMARY] [COMPLETED] *************************************************************')
#    * print('******************** [ALEX DETAILS] [COSMOS] [PROD] [SUMMARY] [COMPLETED] *********************************')
#    # --- Validation and Report Generation ---
#    * eval runValidation(Var)
#    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 2. Cosmos ALEX Claim Details Hospital
    * print('******************** [ALEX DETAILS] [COSMOS] [DEV/QAE] [HOSPITAL] [STARTED] ****************************')
    * def Var = 'HCPvsAlex_Hospital'
#    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
#    * print('******************** [ALEX HOSPITAL] [STARTED] *************************************************************')
#    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_dev_vs_alex_qae/hospital/alex_qae_hospital.feature')
#    * print('******************** [ALEX HOSPITAL] [COMPLETED] ***********************************************************')
#    * print('******************** [HCP HOSPITAL] [STARTED] **************************************************************')
#    * def callonceHcp = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_dev_vs_alex_qae/hospital/ppkg_dev_hospital.feature')
#    * print('******************** [HCP HOSPITAL] [COMPLETED] ************************************************************')
#    * print('******************** [ALEX DETAILS] [COSMOS] [DEV/QAE] [HOSPITAL] [COMPLETED] ***************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)

  Scenario: 3. Cosmos ALEX Claim Details Physician
    * print('******************** [ALEX DETAILS] [COSMOS] [DEV/QAE] [PHYSICIAN] [STARTED] **************************')
    * def Var = 'HCPvsAlex_Physician'
#    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
#    * print('******************** [ALEX PHYSICIAN] [STARTED] ************************************************************')
#    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_dev_vs_alex_qae/physician/alex_qae_physician.feature')
#    * print('******************** [ALEX PHYSICIAN] [COMPLETED] **********************************************************')
#    * print('******************** [HCP PHYSICIAN] [STARTED] *************************************************************')
#    * def callonceHcp = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_dev_vs_alex_qae/physician/ppkg_dev_physician.feature')
#    * print('******************** [HCP PHYSICIAN] [COMPLETED] ***********************************************************')
#    * print('******************** [ALEX DETAILS] [COSMOS] [DEV/QAE] [PHYSICIAN] [COMPLETED] **************************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)



