Feature: Request Cosmos MYUHC_V1 consumer OBAPI PayerPackage PROD Physician Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def searchtype = row.searchtype
    * def claimtype = row.claimtype
    * def claimIdentifier = row.payerClaimControlNumber
    * def memberId = row.memberNumber
    * def claimNumber = row.claimNumber
    * def testcase = row.testcase
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')

  Scenario Outline: Get PayerPackage Summary Details
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_physician', scenario: 'Get PayerPackage Summary Details', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/MYUHC/PPKG_Responses/Physician/' + memberId + '_' + claimNumber + '_ppkg.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/MYUHC/cosmosnicerouter-V1/details/physician_TestData.csv') |
