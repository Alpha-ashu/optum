Feature:  HCP GQL - Alex claimServiceAccumulators
  Scenario: 1. Comparing the Cosmos HCP and Alex Claim Details
    * print('******************** [HCP and Alex Claim Details] [COSMOS] [PROD] [STARTED] *********************')
    * def canonical = 'claimServiceAccumulators'
    * print('******************** [HCP Physician][STARTED] ******************************************')
    * def callonceHCP = callonce read('classpath:feature_files/ppkg_alex/hcp_alex_gql/hcp_dev_vs_alex_qae/claimServiceAccumulator/hcp_claimServiceAccumulator.feature')
    * print('******************** [HCP Physician][COMPLETED] ****************************************')
    * print('******************** [Alex Physician][STARTED] *******************************************')
    * def callonceAlex = callonce read('classpath:feature_files/ppkg_alex/hcp_alex_gql/hcp_dev_vs_alex_qae/claimServiceAccumulator/alex_claimServiceAccumulator.feature')
    * print('******************** [Alex Physician][COMPLETED] *****************************************')
    * print('******************** [callonceing Python Functions to Generate Reports] *******************')
    * def Main = karate.exec('python src\\test\\utility\\DMV_Index_Schema_Validation\\Schema_Validation.py ' + canonical)
    * print('******************** [HCP and Alex Claim Details] [COSMOS] [PROD] [COMPLETED] *******************')
    * print('******************** [GENERATING PERFORMANCE EXCEL REPORT] *******************************')
    * def perfReport = karate.exec('python src\\test\\utility\\performance\\generate_performance_report.py')
    * print('******************** [PERFORMANCE EXCEL REPORT COMPLETED] ********************************')
