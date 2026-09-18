Feature: Request Cosmos ALEX Non-PROD QAE Claim Summary

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/ALEX_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * eval new java.io.File('target/All_Responses/Alex_Negative').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def searchtype = row.reqSearchType
    * def claimtype = row.claimType
    * def claimIdentifier = row.reqClmNbr
    * def memberIdRaw = '' + row.memberNumber
    * def memberId = memberIdRaw.endsWith('.0') ? memberIdRaw.slice(0, -2).padStart(9, '0') : memberIdRaw.padStart(9, '0')
    * def claimNumber = row.claimNumber
    * def testcase = row.testcase
    * print('********************', [testcase], [claimIdentifier], '[STARTED] ******************************')

  Scenario Outline: Get PayerPackage claim in Alex Environment and get the claim Details to compare with PPKG
    * def reqUrl = 'https://api-stg.uhg.com/api/payer/claims/summary/1.0.0'
    * def nextKey = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 100}'
    * def reqHeaders =
      """
      {
        "Authorization": "#(accessToken)",
        "event-type": "SERVICE",
        "X-Upstream-Env": "qae",
        "fields-response": "claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payment",
        "consumername": "claims360_np",
        "search-type": "#(searchtype)",
        "claim-type": "#(claimtype)",
        "claim-identifier": "#(claimIdentifier)",
        "match-encounter-claims-only": "TRUE",
        "next-key": "#(nextKey)"
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
    * def filename = 'All_Responses/Summary/Alex_Responses/' + testcase + '_' + claimIdentifier + '_alexResponse.json'
    * karate.write(response, filename)


    Examples:
      | read('classpath:testdata/alex_ppkg/hcp_vs_alex_sample_testdata_2.csv') |
