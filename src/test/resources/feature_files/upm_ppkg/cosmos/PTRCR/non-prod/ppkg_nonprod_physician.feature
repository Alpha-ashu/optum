Feature: Request Cosmos PTRCR PayerPackage Non-prod Physician Details

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

  Scenario Outline: Get PayerPackage Hospital Details
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * print('********************', [testcase], [memberId], [claimIdentifier], '[COMPLETED] **************************')
    * def filename = 'All_Responses/PTRCR/PPKG_Responses/Physician/' + memberId + '_' + claimNumber + '_ppkg.json'
    * def perfData = { consumer: 'PTRCR', feature: 'ppkg_nonprod_physician', scenario: 'Get PayerPackage Hospital Details', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)


    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/PTRCR/physician_TestData.csv') |

      @negative @401
      Scenario Outline: NEG - 401 when Authorization header is missing
        * def testcase = <testcase>
        * def claimIdentifier = <claimIdentifier>
        Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
        And header event-type = 'SERVICE'
        And header X-Upstream-Env = 'STAGE'
        And header fields-response = 'claimIdentifiers'
        And header consumername = 'claims360_prod'
        And header search-type = 'CLAIM_ID'
        And header claim-type = 'PROF'
        And header match-encounter-claims-only = 'TRUE'
        When method get
        * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'PTRCR', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 401 when Authorization header is missing', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
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
        And header X-Upstream-Env = 'STAGE'
        And header fields-response = 'claimIdentifiers'
        And header consumername = 'claims360_prod'
        And header search-type = 'CLAIM_ID'
        And header claim-type = 'PROF'
        And header match-encounter-claims-only = 'TRUE'
        When method get
        * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'PTRCR', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 401 when Authorization token is invalid/malf', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
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
    * def perfData = { consumer: 'PTRCR', feature: 'ppkg_nonprod_physician', scenario: 'NEG - 403 when consumer/environment headers are un', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
        Examples:
          | testcase                      | claimIdentifier         |
          | 'NEG_Unauthorized_Header_01'  | 'NON_EXISTENT_CLAIM_03' |

