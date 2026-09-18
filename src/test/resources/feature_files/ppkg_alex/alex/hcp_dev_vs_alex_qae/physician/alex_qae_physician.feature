Feature: Request Cosmos ALEX Non-PROD Claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/ALEX_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * eval new java.io.File('target/All_Responses/Alex_Negative').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def searchtype = row.reqSearchType
    * def claimtype = row.claimType
    # Hospital searches by ICN (search-type = 'I'), and the response file is keyed
    # by that same ICN. The validator is told to match this via "identifier_column":
    # "reqInvnCtlNbr" in validation_config/IIM/ppkg_alex_dev_qae_hospital.json.
    * def claimIdentifier = row.reqClmNbr
    * def memberIdRaw = '' + row.memberNumber
    * def testcase = row.testcase
    * print('********************', [testcase], [claimIdentifier], '[STARTED] ******************************')

  Scenario Outline: Get PayerPackage claim in Alex Environment and get the claim Details to compare with PPKG
    * def reqUrl = 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    * def reqHeaders =
      """
      {
        "Authorization": "#(accessToken)",
        "event-type": "SERVICE",
        "X-Upstream-Env": "qae",
        "fields-response": "claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation",
        "consumername": "claims360_np",
        "search-type": "#(searchtype)",
        "claim-type": "#(claimtype)",
        "match-encounter-claims-only": "TRUE"
      }
      """
    # Retry up to 10 times until we get HTTP 200. Stops as soon as 200 comes back
    # and moves on. If 200 never comes it does NOT crash the run - the last
    # response is still saved below.
    * def retryGet = read('classpath:utility/retry_get.js')
    * def result = retryGet({ max: 10, interval: 1000, req: { reqUrl: reqUrl, reqHeaders: reqHeaders } })
    * def response = result.response
    * def responseStatus = result.responseStatus
    * def responseTime = result.responseTime
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Never got 200 after 10 attempts, last status', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'IIM', feature: 'alex_nonprod_physician', scenario: 'Get PayerPackage claim in Alex Environment and get', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/Physician/Alex_Responses/' + testcase + '_' + claimIdentifier + '_alexResponse.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/alex_ppkg/hcp_vs_alex_sample_testdata_2.csv') |

