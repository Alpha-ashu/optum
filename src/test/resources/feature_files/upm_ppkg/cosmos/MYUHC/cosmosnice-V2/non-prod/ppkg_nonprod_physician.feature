Feature: Request Cosmos PayerPackage Non-PROD Physician Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def claimIdentifier = row.payerClaimControlNumber
    * def memberId = row.memberNumber
    * def claimNumber = row.claimNumber
    * def testcase = row.testcase
    * print('********************', [testcase], [memberId], [claimIdentifier], '[STARTED] ****************************')

  Scenario Outline: Get PayerPackage Summary Details
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
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
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'Get PayerPackage Summary Details', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************', [testcase], [memberId], [claimIdentifier], '[COMPLETED] **************************')
    * def filename = 'All_Responses/MYUHC/PPKG_Responses/Physician/' + memberId + '_' + claimNumber + '_ppkg.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/MYUHC/cosmosnice-V2/details/physician_TestData.csv') |

  @negative @401
  Scenario Outline: NEG - 401 when Authorization header is missing
    * def testcase = <testcase>
    * def claimIdentifier = <claimIdentifier>
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 401 when Authorization header is missing', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase               | claimIdentifier         |
      | 'NEG_Missing_Token_01' | 'NON_EXISTENT_CLAIM_01' |

  @negative @401
  Scenario Outline: NEG - 401 when Authorization token is invalid/malformed
    * def testcase = <testcase>
    * def claimIdentifier = <claimIdentifier>
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = 'Bearer invalid.or.malformed.token'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 401 when Authorization token is invalid/malf', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase              | claimIdentifier         |
      | 'NEG_Invalid_Token_01'| 'NON_EXISTENT_CLAIM_02' |

  @negative @403
  Scenario Outline: NEG - 403 when consumer/environment headers are unauthorized
    * def testcase = <testcase>
    * def claimIdentifier = <claimIdentifier>
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'BAD_EVENT'
    And header X-Upstream-Env = 'BAD_ENV'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'unauthorized-consumer'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 403 when consumer/environment headers are un', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                      | claimIdentifier         |
      | 'NEG_Unauthorized_Header_01'  | 'NON_EXISTENT_CLAIM_03' |

  @negative @415
  Scenario: NEG - 415 when Content-Type is not appropriate for GET
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_04'
    And header Authorization = accessToken
    And header Content-Type = 'text/plain'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 415 when Content-Type is not appropriate for', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @406
  Scenario: NEG - 406 when Accept is unsupported
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_05'
    And header Authorization = accessToken
    And header Accept = 'application/xml'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 406 when Accept is unsupported', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @validation
  Scenario: NEG - 400/422 when required header 'search-type' is missing
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_06'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 400/422 when required header search-type i', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @validation
  Scenario: NEG - 400/422 when required header 'claim-identifier' is missing
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_07'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 400/422 when required header claim-identifi', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @validation
  Scenario: NEG - 400/422 when header values are invalid
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_08'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'INVALID'
    And header claim-type = 'INVALID'
    And header match-encounter-claims-only = 'MAYBE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 400/422 when header values are invalid', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @validation
  Scenario Outline: NEG - 400/422 when next-key is malformed JSON
    * def testcase = <testcase>
    * def nextKey = <nextKey>
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_09'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header next-key = nextKey
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 400/422 when next-key is malformed JSON', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                    | nextKey                             |
      | 'NEG_Next_Key_Bad_Type_01'  | '{"offset":"abc","size":10}'   |
      | 'NEG_Next_Key_Negative_01'  | '{"offset":-1,"size":10}'        |
      | 'NEG_Next_Key_Huge_Page_01' | '{"offset":0,"size":999999999}'  |

  @negative @validation
  Scenario Outline: NEG - 400/422 when fields-response contains unknown fields
    * def testcase = <testcase>
    * def fields = <fields>
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_10'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = fields
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 400/422 when fields-response contains unknow', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                         | fields          |
      | 'NEG_Unknown_Fields_Response_01' | 'fooBar,bazQux' |

  @negative @404
  Scenario Outline: NEG - 404/200 when claim-identifier does not exist
    * def testcase = <testcase>
    * def claimIdentifier = <claimIdentifier>
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 404/200 when claim-identifier does not exist', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    Examples:
      | testcase                            | claimIdentifier         |
      | 'NEG_Claim_Identifier_NotFound_01'  | 'NON_EXISTENT_CLAIM_11' |

  @negative @405
  Scenario: NEG - 405 when using POST (GET-only endpoint)
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_12'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    And request { dummy: 'value' }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 405 when using POST (GET-only endpoint)', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @429
  Scenario: NEG - 429 when rate limit is exceeded (retry probe)
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/NON_EXISTENT_CLAIM_13'
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers'
    And header consumername = 'claims360_prod'
    And header search-type = 'CLAIM_ID'
    And header claim-type = 'PROF'
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'MYUHC', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 429 when rate limit is exceeded (retry probe', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
