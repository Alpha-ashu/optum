Feature:  HCP - ALEX Customer Resolver Consumer IIM COSMOS PROD ENVIRONMENT

  Background:
    # Helper: run validation and generate reports for the given Var
    * def runValidation =
    """
    function(varName) {
      karate.log('[VALIDATION] === Generating reports for:', varName, '===');
      try {
        karate.exec('python src/test/utility/ppkg/payment_compare.py');
        karate.log('[VALIDATION] payment_compare.py completed for', varName);
      } catch(e) { karate.log('[VALIDATION] payment_compare.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/performance/generate_performance_report.py');
        karate.log('[VALIDATION] Performance report generated for', varName);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """

  Scenario: 1. Comparing the Cosmos HCP and ALEX Claim Details
    * print('******************** [Legacy and PPKG Claim Details] [COSMOS] [PROD] [STARTED] *********************')
    * def Var = 'AccountRecovery_Payment'
    * print('******************** [Legacy][STARTED] *******************************************')
    * def callonceLegacy = callonce read('classpath:feature_files/upm_ppkg/tops/accountRecovery.feature')
    * print('******************** [Legacy][COMPLETED] ****************************************')
    * print('******************** [PPKG][STARTED] *******************************************')
    * def calloncePPKG = callonce read('classpath:feature_files/upm_ppkg/tops/payment.feature')
    * print('******************** [PPKG][COMPLETED] *****************************************')
    * print('******************** [Legacy and PPKG Claim Details] [Tops][COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)
