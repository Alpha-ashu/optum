Feature:  PPKG - ALEX IIM COSMOS PROD And QAE ENVIRONMENT Physician claim details

  Background:
    # Helper: run validation and generate reports for the given Var. Uses the
    # generic, config-driven engine (Schema_Validation.py + validation_config/)
    # instead of the removed ppkg_alex_compare.py / ppkg_alex_report.py scripts.
    * def runValidation =
    """
    function(varName) {
      karate.log('[VALIDATION] === Generating reports for:', varName, '===');
      try {
        karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py ' + varName);
        karate.log('[VALIDATION] Schema_Validation.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] Schema_Validation.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter Physician_Prod --feature-filter alex_qae_physician,ppkg_prod_physician --output target/All_Responses/Physician_Prod/' + varName + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', varName);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. callonceing the Cosmos ALEX Claim Details Physician
    * print('******************** [ALEX Claim Details] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'HCPvsAlex_Physician_Prod'
    * print('******************** [Alex Physician][STARTED] *******************************************')
    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_prod_vs_alex_qae/alex_qae_physician.feature')
    * print('******************** [Alex Physician][COMPLETED] *****************************************')
    * print('******************** [PPKG Physician][STARTED] ******************************************')
    * def calloncePayer = callonce read('classpath:feature_files/ppkg_alex/alex/hcp_prod_vs_alex_qae/ppkg_prod_physician.feature')
    * print('******************** [PPKG Physician][COMPLETED] ****************************************')
    * print('******************** [ALEX Claim Details] [COSMOS] [PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)
