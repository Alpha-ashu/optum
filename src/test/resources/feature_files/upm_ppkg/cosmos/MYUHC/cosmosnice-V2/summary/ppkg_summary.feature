Feature: Request Cosmos PayerPackage PROD Summary Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://api.uhg.com/api/clm/med/claims360/2.0.0'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def memberId = row.memberNumber
    * def searchtype = row.searchtype
    * def testcase = row.testcase
    * print('********************', [testcase], [memberId], [claimIdentifier], '[STARTED] ****************************')
  Scenario Outline: Getting Single Record Based on Claim-identifiers
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_summary', scenario: 'Getting Single Record Based on Claim-identifiers', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************', [testcase], [memberId], [claimIdentifier], '[COMPLETED] **************************')
    * def filename = 'All_Responses/MYUHC/PPKG_Responses/Summary/' + memberId + '_' + claimNumber + '_ppkg.json'
    * karate.write(response, filename)
    Examples:
      |read('classpath:testdata/upm_ppkg_cosmos/MYUHC/cosmosnice-V2/summary/summary_TestData.csv')|
