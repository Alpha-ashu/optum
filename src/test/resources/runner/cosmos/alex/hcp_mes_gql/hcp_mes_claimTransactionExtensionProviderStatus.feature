Feature:  HCP GQL - ALEX claimTransactionExtensionProviderStatus
  Scenario: 1. Comparing the Cosmos HCP and ALEX Claim Details
    * print('******************** [HCP and ALEX Claim Details] [COSMOS] [PROD] [STARTED] *********************')
    * def canonical = 'claimTransactionExtensionProviderStatus'
    * print('******************** [PPKG Physician][STARTED] ******************************************')
    * def callonceHCP = callonce read('classpath:feature_files/ppkg_alex/hcp_mes_gql/claimTransaction-extension-provider-status/hcp_claimTransaction-extension-provider-status.feature')
    * print('******************** [PPKG Physician][COMPLETED] ****************************************')
    * print('******************** [ALEX Physician][STARTED] *******************************************')
    * def callonceALEX = callonce read('classpath:feature_files/ppkg_alex/hcp_mes_gql/claimTransaction-extension-provider-status/mes_claimTransaction-extension-provider-status.feature')
    * print('******************** [ALEX Physician][COMPLETED] *****************************************')
    * print('******************** [callonceing Python Functions to Generate Reports] *******************')
    * def Main = karate.exec('python src\\test\\utility\\DMV_Index_Schema_Validation\\Schema_Validation.py ' + canonical)
    * print('******************** [HCP and ALEX Claim Details] [COSMOS] [PROD] [COMPLETED] *******************')
    * print('******************** [GENERATING PERFORMANCE EXCEL REPORT] *******************************')
    * def perfReport = karate.exec('python src\\test\\utility\\performance\\generate_performance_report.py')
    * print('******************** [PERFORMANCE EXCEL REPORT COMPLETED] ********************************')
