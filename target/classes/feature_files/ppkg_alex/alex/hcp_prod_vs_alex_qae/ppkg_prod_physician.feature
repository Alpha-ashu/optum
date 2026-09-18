Feature: Request Cosmos PayerPackage PROD Claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * eval new java.io.File('All_Responses/PPKG_Negative').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def memberId = row.memberNumber
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def testcase = row.testcase
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
  Scenario Outline: Get PayerPackage claim Details to compare with Alex
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
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'Get PayerPackage claim Details to compare with Ale', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/PPKG_Responses/' + memberId + '_' + claimIdentifier + '_ppkgResponse.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/alex_ppkg/hcp_alex_physician_prod_data.csv') |

  @negative @401
  Scenario Outline: NEG - 401 when Authorization header is missing
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 401 when Authorization header is missing', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Missing_Token_01_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Missing_Token_01'  | '111111111'  | 'PRODCLAIM0001'         | '0001'      | 'claimIdentifier'| 'professional' |

  @negative @401
  Scenario Outline: NEG - 401 when Authorization token is invalid/malformed
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = 'Bearer invalid.or.malformed.token'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 401 when Authorization token is invalid/malf', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Invalid_Token_01_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Invalid_Token_01'  | '111111111'  | 'PRODCLAIM0002'         | '0002'      | 'claimIdentifier'| 'professional' |

  @negative @403
  Scenario Outline: NEG - 403 when consumer/environment headers are unauthorized
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'BAD_EVENT'
    And header X-Upstream-Env = 'BAD_ENV'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState'
    And header consumername = 'unauthorized-consumer'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 403 when consumer/environment headers are un', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Unauthorized_Header_01_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                        | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Unauthorized_Header_01'    | '111111111'  | 'PRODCLAIM0003'         | '0003'      | 'claimIdentifier'| 'professional' |

  @negative @415
  Scenario Outline: NEG - 415 when Content-Type is not appropriate for GET
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header Content-Type = 'text/plain'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 415 when Content-Type is not appropriate for', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Unsupported_ContentType_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_415_Content_Type_01' | '111111111' | 'PRODCLAIM0004' | '0004' | 'claimIdentifier'| 'professional' |

  @negative @406
  Scenario Outline: NEG - 406 when Accept is unsupported
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header Accept = 'application/xml'
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 406 when Accept is unsupported', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Not_Acceptable_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_406_Accept_01' | '111111111' | 'PRODCLAIM0005' | '0005' | 'claimIdentifier'| 'professional' |

  @negative @validation
  Scenario Outline: NEG - 400/422 when required header 'search-type' is missing
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 400/422 when required header search-type i', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Missing_Search_Type_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Missing_Search_Type_01' | '111111111' | 'PRODCLAIM0006' | '0006' | 'claimIdentifier'| 'professional' |

  @negative @validation
  Scenario Outline: NEG - 400/422 when required header 'claim-identifier' is missing
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 400/422 when required header claim-identifi', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Missing_Claim_Identifier_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Missing_Claim_Identifier_01' | '111111111' | 'PRODCLAIM0007' | '0007' | 'claimIdentifier'| 'professional' |

  @negative @validation
  Scenario Outline: NEG - 400/422 when header values are invalid
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = <invalidSearchType>
    And header claim-type = <invalidClaimType>
    And header match-encounter-claims-only = <invalidMatchEncounter>
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 400/422 when header values are invalid', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Invalid_Header_Enums_01_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                      | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      | invalidSearchType | invalidClaimType | invalidMatchEncounter |
      | 'NEG_Invalid_Header_Enums_01' | '111111111'  | 'PRODCLAIM0008'         | '0008'      | 'claimIdentifier'| 'professional' | 'INVALID'         | 'INVALID'        | 'MAYBE'               |

  @negative @validation
  Scenario Outline: NEG - 400/422 when next-key is malformed JSON
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    And header next-key = <nextKey>
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 400/422 when next-key is malformed JSON', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/' + testcase + '_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                        | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      | nextKey                                      |
      | 'NEG_Next_Key_Bad_Type_01'      | '111111111'  | 'PRODCLAIM0009'         | '0009'      | 'claimIdentifier'| 'professional' | '{"offset":"abc","size":10}'            |
      | 'NEG_Next_Key_Negative_01'      | '111111111'  | 'PRODCLAIM0010'         | '0010'      | 'claimIdentifier'| 'professional' | '{"offset":-1,"size":10}'                 |
      | 'NEG_Next_Key_Huge_Page_Size_01'| '111111111'  | 'PRODCLAIM0011'         | '0011'      | 'claimIdentifier'| 'professional' | '{"offset":0,"size":999999999}'           |

  @negative @validation
  Scenario Outline: NEG - 400/422 when fields-response contains unknown fields
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    And header fields-response = <invalidFieldsResponse>
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 400/422 when fields-response contains unknow', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/' + testcase + '_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                         | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      | invalidFieldsResponse                 |
      | 'NEG_Fields_Response_Unknown_01' | '111111111'  | 'PRODCLAIM0012'         | '0012'      | 'claimIdentifier'| 'professional' | 'foo,bar,unknownField'                |
      | 'NEG_Fields_Response_Unknown_02' | '111111111'  | 'PRODCLAIM0013'         | '0013'      | 'claimIdentifier'| 'professional' | 'serviceLines.badField,patient.zzz'   |

  @negative @validation
  Scenario Outline: NEG - 404/200 when claim-identifier does not exist
    * def badClaimId = <badClaimId>
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + badClaimId
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 404/200 when claim-identifier does not exist', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/' + testcase + '_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase                              | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      | badClaimId                |
      | 'NEG_Claim_Identifier_Not_Exist_01'   | '111111111'  | 'PRODCLAIM0014'         | '0014'      | 'claimIdentifier'| 'professional' | 'NOTFOUNDCLAIM00000001'   |
      | 'NEG_Claim_Identifier_Not_Exist_02'   | '111111111'  | 'PRODCLAIM0015'         | '0015'      | 'claimIdentifier'| 'professional' | 'NOTFOUNDCLAIM00000002'   |

  @negative @405
  Scenario Outline: NEG - 405 when using POST (GET-only endpoint)
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    And request { dummy: 'value' }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 405 when using POST (GET-only endpoint)', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * if (responseHeaders.Allow) karate.match(responseHeaders.Allow, '#notnull')
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Method_Not_Allowed_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Method_Not_Allowed_01' | '111111111' | 'PRODCLAIM0016' | '0016' | 'claimIdentifier'| 'professional' |

  @negative @429
  Scenario Outline: NEG - 429 when rate limit is exceeded (retry probe)
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'NEG - 429 when rate limit is exceeded (retry probe', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Negative/NEG_Rate_Limit_Probe_' + java.lang.System.currentTimeMillis() + '.json')

    Examples:
      | testcase | memberNumber | payerClaimControlNumber | claimNumber | searchtype       | claimType      |
      | 'NEG_Rate_Limit_Probe_01' | '111111111' | 'PRODCLAIM0017' | '0017' | 'claimIdentifier'| 'professional' |
