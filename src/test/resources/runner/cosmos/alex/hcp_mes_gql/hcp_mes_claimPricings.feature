Feature:  HCP GQL - ALEX Claimserviceline

  Scenario: 1. Comparing the Cosmos HCP and ALEX Claim Details
    * print('******************** [HCP and ALEX Claim Details] [COSMOS] [PROD] [STARTED] *********************')

    * def canonical = 'claimPricings'
    * print('******************** [PPKG Physician][STARTED] ******************************************')
    * def callonceHCP = callonce read('classpath:feature_files/ppkg_alex/hcp_mes_gql/claimPricing/hcp_claimPricing.feature')
    * print('******************** [PPKG Physician][COMPLETED] ****************************************')
    * print('******************** [ALEX Physician][STARTED] *******************************************')
    * def callonceALEX = callonce read('classpath:feature_files/ppkg_alex/hcp_mes_gql/claimPricing/mes_claimPricing.feature')
    * print('******************** [ALEX Physician][COMPLETED] *****************************************')
    * print('******************** [callonceing Python Functions to Generate Reports] *******************')
    * def Main = karate.exec('python src\\test\\utility\\DMV_Index_Schema_Validation\\hcp_mes_compare.py' + canonical)
    * print('******************** [HCP and ALEX Claim Details] [COSMOS] [PROD] [COMPLETED] *******************')
    * print('******************** [GENERATING PERFORMANCE EXCEL REPORT] *******************************')
    * def perfReport = karate.exec('python src\\test\\utility\\performance\\generate_performance_report.py')
    * print('******************** [PERFORMANCE EXCEL REPORT COMPLETED] ********************************')
