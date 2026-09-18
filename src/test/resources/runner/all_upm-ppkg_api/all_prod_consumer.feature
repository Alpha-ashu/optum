Feature: Executing All Cosmos UPM/PPKG API PROD ENVIRONMENT

  Background:
    # Helper to safely call a runner - catches errors so one failure doesn't stop the rest
    * def safeCall =
    """
    function(featurePath) {
      try {
        karate.call(featurePath);
        return { success: true, error: null };
      } catch(e) {
        karate.log('[WARN] Runner failed:', featurePath, '-', e.message);
        return { success: false, error: e.message };
      }
    }
    """

  Scenario: calling the Cosmos UPM/PPKG API
    * print('******************** [COSMOS UPM/PPKG API] [PROD] [STARTED] *********************')

    # Each consumer runner has 3 scenarios (Summary, Hospital, Physician)
    # Each scenario: beforeScenario(clean) -> execute -> afterScenario(validate+report+clean)
    # No overlap possible between scenarios

    * print('>>> [ACET] Starting...')
    * def ACET = safeCall('classpath:runner/upm_ppkg_cosmos/ACET/acet_upm_ppkg.feature')
    * print('>>> [ACET] Done. Success:', ACET.success)

    * print('>>> [IIM] Starting...')
    * def IIM = safeCall('classpath:runner/upm_ppkg_cosmos/IIM/iim_upm_ppkg.feature')
    * print('>>> [IIM] Done. Success:', IIM.success)

    * print('>>> [ISET] Starting...')
    * def ISET = safeCall('classpath:runner/upm_ppkg_cosmos/ISET/iset_upm_ppkg.feature')
    * print('>>> [ISET] Done. Success:', ISET.success)

    * print('>>> [MEDICA] Starting...')
    * def MEDICA = safeCall('classpath:runner/upm_ppkg_cosmos/MEDICA/medica_upm_ppkg.feature')
    * print('>>> [MEDICA] Done. Success:', MEDICA.success)

    * print('>>> [MYUHC-V1] Starting...')
    * def myuhcV1 = safeCall('classpath:runner/upm_ppkg_cosmos/MYUHC/myuhc_upm_ppkg_v1.feature')
    * print('>>> [MYUHC-V1] Done. Success:', myuhcV1.success)

    * print('>>> [MYUHC-V2] Starting...')
    * def myuhcV2 = safeCall('classpath:runner/upm_ppkg_cosmos/MYUHC/myuhc_upm_ppkg_v2.feature')
    * print('>>> [MYUHC-V2] Done. Success:', myuhcV2.success)

    * print('>>> [OHBSPE] Starting...')
    * def OHBSPE = safeCall('classpath:runner/upm_ppkg_cosmos/OHBSPE/ohbspe_upm_ppkg.feature')
    * print('>>> [OHBSPE] Done. Success:', OHBSPE.success)

    * print('>>> [PTRCR] Starting...')
    * def PTRCR = safeCall('classpath:runner/upm_ppkg_cosmos/PTRCR/ptrcr_upm_ppkg.feature')
    * print('>>> [PTRCR] Done. Success:', PTRCR.success)

    * print('>>> [VETSS] Starting...')
    * def VETSS = safeCall('classpath:runner/upm_ppkg_cosmos/VETSS/vetss_upm_ppkg.feature')
    * print('>>> [VETSS] Done. Success:', VETSS.success)

    * print('******************** [COSMOS UPM/PPKG API] [PROD] [COMPLETED] *********************')

    # Final consolidated reports across ALL consumers
    * print('******************** [GENERATING FINAL PERFORMANCE REPORT] ***********************')
    * print('>>> Output: target/All_Responses/ALL_COSMOS_CONSUMER_PROD_API_PERFORMANCE_REPORT.xlsx')
    * karate.exec('python src\\test\\utility\\performance\\generate_performance_report.py --output target\\All_Responses\\ALL_COSMOS_CONSUMER_PROD_API_PERFORMANCE_REPORT.xlsx')
    * print('******************** [PERFORMANCE REPORT COMPLETED] ***********************')

    * print('******************** [GENERATING CONSOLIDATED VALIDATION REPORTS] ***********************')
    * print('>>> Output: target/All_Responses/ALL_COSMOS_CONSUMER_PROD_API_CONSOLIDATE_REPORT.xlsx')
    * karate.exec('python src\\test\\utility\\upm_ppkg_validation\\consolidate_consumer_reports.py')
    * print('******************** [CONSOLIDATED VALIDATION REPORTS COMPLETED] ***********************')
