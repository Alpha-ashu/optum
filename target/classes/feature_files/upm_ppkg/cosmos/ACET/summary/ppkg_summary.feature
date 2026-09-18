Feature: NEG – Request Cosmos ACET PPKG PROD Summary Claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://api.uhg.com/api/clm/med/claims360/2.0.0'


  Scenario Outline: Request for PPKG Summary claim details validation
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def memberId = row.memberNumber
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def testcase = row.testcase

    * print('********************', testcase, memberId, claimIdentifier, '[STARTED] ****************************')

    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ACET', feature: 'ppkg_summary', scenario: 'Request for PPKG Summary claim details validation', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    * karate.write(response, 'All_Responses/ACET/PPKG_Responses/Summary/' + memberId + '_' + claimNumber + '_ppkg.json')
    * print('********************', testcase, memberId, claimIdentifier, '[COMPLETED] **************************')

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/ACET/summary_TestData.csv') |
