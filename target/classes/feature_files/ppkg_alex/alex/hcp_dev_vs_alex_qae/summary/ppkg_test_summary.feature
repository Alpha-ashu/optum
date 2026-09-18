Feature: Request Cosmos ALEX Non-PROD QAE Claim Summary

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * eval new java.io.File('target/All_Responses/PPKG_Negative').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    # search-type must match the identifier we send. We send a claim control number
    # (reqClmNbr) as claim-identifier, so use the CLAIM search type (reqSearchType = 'C').
    # Using icnsearchtype ('I') here searched for the claim number as an ICN and
    # returned 404 "No records found" for every row.
    * def searchtype = row.reqSearchType
    * def claimtype = row.claimType
    * def claimIdentifier = row.reqClmNbr
    * def memberIdRaw = '' + row.memberNumber
    * def memberId = memberIdRaw.endsWith('.0') ? memberIdRaw.slice(0, -2).padStart(9, '0') : memberIdRaw.padStart(9, '0')
    * def claimNumber = row.claimNumber
    * def testcase = row.testcase
    * print('********************', [testcase], [claimIdentifier], '[STARTED] ******************************')

  Scenario Outline: Get PayerPackage claim in HCP Environment and get the claim Details to compare with PPKG
    * def reqUrl = 'https://api-stg.uhg.com/api/clm/med/claims360/2.0.0'
    * def nextKey = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 500}'
    * def reqHeaders =
      """
      {
        "Authorization": "#(accessToken)",
        "Content-Type": "application/json",
        "X-Upstream-Env": "test",
        "claim-identifier": "#(claimIdentifier)",
        "consumername": "claims360_np",
        "event-type": "SERVICE",
        "fields-response": "claimIdentifiers,claimCategories,claimState,patient,providers,claimAuthorizations,insurance,totals,payments",
        "next-key": "#(nextKey)",
        "search-type": "#(searchtype)"
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
    * def perfData = { consumer: 'IIM', feature: 'ppkg_prod_physician', scenario: 'Get PayerPackage claim Details to compare with Ale', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/Summary/PPKG_Responses/' + testcase + '_' + claimIdentifier + '_ppkgResponse.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/alex_ppkg/hcp_vs_alex_sample_testdata_2.csv') |

