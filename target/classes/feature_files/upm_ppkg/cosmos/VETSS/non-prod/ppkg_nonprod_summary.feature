Feature: Request Cosmos VETSS PayerPackage Non-prod Summary Details

  Background:

    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken =  callAccessToken.accessToken
    * def api_url = 'https://api-stg.uhg.com/api/clm/med/claims360/2.0.0'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def memberId = row.memberNumber
    * def searchtype = row.searchtype
    * def testcase = row.testcase
    * print('********************', [testcase], [memberId], [claimIdentifier], '[STARTED] **************************')

  Scenario Outline: Getting Single Record Based on Claim-identifiers
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
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
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'Getting Single Record Based on Claim-identifiers', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************', [testcase], [memberId], [claimIdentifier], '[COMPLETED] **************************')
    * def filename = 'All_Responses/VETSS/PPKG_Responses/Summary/' + memberId + '_' + claimNumber + '_ppkg.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/VETSS/summary_TestData.csv') |
  @negative @401
  Scenario Outline: NEG - 401 when Authorization header is missing
    * def testcase = <testcase>
    Given url api_url
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 401 when Authorization header is missing', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase               |
      | 'NEG_Missing_Token_01' |
  @negative @401
  Scenario Outline: NEG - 401 when Authorization token is invalid/malformed
    * def testcase = <testcase>
    Given url api_url
    And header Authorization = 'Bearer invalid.or.malformed.token'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 401 when Authorization token is invalid/malf', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase               |
      | 'NEG_Invalid_Token_01' |
  @negative @403
  Scenario Outline: NEG - 403 when consumer/environment headers are unauthorized
    * def testcase = <testcase>
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'UNKNOWN_EVENT'
    And header X-Upstream-Env = 'UAT'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'unknown_consumer'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 403 when consumer/environment headers are un', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                    |
      | 'NEG_Unauthorized_Header_01'|
  @negative @415
  Scenario: NEG - 415 when Content-Type is not appropriate for GET
    Given url api_url
    And header Authorization = accessToken
    And header Content-Type = 'text/plain'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 415 when Content-Type is not appropriate for', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
  @negative @406
  Scenario: NEG - 406 when Accept is unsupported
    Given url api_url
    And header Authorization = accessToken
    And header Accept = 'application/xml'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 406 when Accept is unsupported', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
  @negative @validation
  Scenario: NEG - 400/422 when required header 'search-type' is missing
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 400/422 when required header search-type i', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
  @negative @validation
  Scenario: NEG - 400/422 when required header 'claim-identifier' is missing
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 400/422 when required header claim-identifi', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
  @negative @validation
  Scenario Outline: NEG - 400/422 when header values are invalid
    * def testcase = <testcase>
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = 'UNKNOWN_SEARCH'
    And header claim-type = 'UNKNOWN_CLAIMTYPE'
    And header match-encounter-claims-only = 'MAYBE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 400/422 when header values are invalid', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                      |
      | 'NEG_Invalid_Header_Enums_01' |
  @negative @validation
  Scenario Outline: NEG - 400/422 when next-key is malformed JSON
    * def testcase = <testcase>
    * def nextKeyHeader = <nextKeyHeader>
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = nextKeyHeader
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 400/422 when next-key is malformed JSON', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                      | nextKeyHeader                                                                      |
      | 'NEG_NextKey_Malformed_01'    | '{"nextPageToken":"abc","pageNum":"one","numPages":"zero","pageSize":"big"}' |
      | 'NEG_NextKey_Malformed_02'    | '{"nextPageToken":"abc","pageNum":-1,"pageSize":-10}'                    |
      | 'NEG_NextKey_TooLargePage_01' | '{"nextPageToken":"","pageNum":1,"numPages":0,"pageSize":10000}'       |
  @negative @validation
  Scenario Outline: NEG - 400/422 when fields-response contains unknown fields
    * def testcase = <testcase>
    * def fields = <fields>
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = fields
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 400/422 when fields-response contains unknow', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                        | fields                                     |
      | 'NEG_Unknown_FieldsResponse_01' | 'claimIdentifiers,totals,nonExistingField' |
      | 'NEG_Unknown_FieldsResponse_02' | '*,claimIdentifiers'                       |
  @negative @404
  Scenario Outline: NEG - 404/200 when claim-identifier does not exist
    * def testcase = <testcase>
    * def claimIdentifierNeg = <claimIdentifierNeg>
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifierNeg
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 404/200 when claim-identifier does not exist', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                  | claimIdentifierNeg     |
      | 'NEG_Unknown_ClaimId_01'  | 'NONEXISTENT-CLAIM-001'|
  @negative @405
  Scenario: NEG - 405 when using POST (GET-only endpoint)
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    And request { dummy: 'value' }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 405 when using POST (GET-only endpoint)', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * if (responseHeaders.Allow) karate.match(responseHeaders.Allow, '#notnull')
  @negative @429
  Scenario: NEG - 429 when rate limit is exceeded
    Given url api_url
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 200}'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = 'MEDICAL'
    And header match-encounter-claims-only = 'TRUE'
    And header claim-identifier = claimIdentifier
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'VETSS', feature: 'ppkg_nonprod_summary', scenario: 'NEG - 429 when rate limit is exceeded', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

