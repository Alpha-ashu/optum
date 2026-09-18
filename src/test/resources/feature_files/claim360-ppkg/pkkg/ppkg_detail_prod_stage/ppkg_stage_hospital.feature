Feature: Request Cosmos PayerPackage Non-PROD Claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * eval new java.io.File('target/All_Responses/PPKG_Negative').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def internalclaimindentifier = row.ICN
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def testcase = row.testcase
    * print('********************',[testcase],[internalclaimindentifier],'[STARTED] ********************************')
  Scenario Outline: Get PayerPackage claim Details to compare with Alex
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + internalclaimindentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'Get PayerPackage claim Details to compare with Ale', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[internalclaimindentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/Hospital/PPKG_Stage_Detail_Responses/' + testcase + '_' + internalclaimindentifier + '_ppkgResponse.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/ppkg/sample_testdata.csv') |

