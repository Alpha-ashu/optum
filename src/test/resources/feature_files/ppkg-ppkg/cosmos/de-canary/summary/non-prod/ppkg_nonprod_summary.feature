Feature: Request Cosmos Cosmos PayerPackage Non-prod Summary Details

  Background:

    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken =  callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def ICN = row.internalReferenceIdentifier
#    * def Claimidentifiers = row.claimNumber
    * def searchtype = row.searchtype
    * def testcase = row.testcase
    * print('********************', [testcase], [ICN], '[STARTED] **************************')

  Scenario Outline: Getting Single Record Based on Claim-identifiers
    Given url 'https://api-stg.uhg.com/api/clm/med/claims360/2.0.0'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'TEST'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 100}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_np'
    And header search-type = searchtype
    And header claim-identifier = ICN
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'ppkg_nonprod_summary', scenario: 'Getting Single Record Based on Claim-identifiers', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************', [testcase],[ICN], '[COMPLETED] **************************')
    * def filename = 'All_Responses/TOPS/PPKG_Responses/Summary/' + testcase + '_' + ICN + '_ppkgResponse.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/decanary/decanary_summary.csv') |


