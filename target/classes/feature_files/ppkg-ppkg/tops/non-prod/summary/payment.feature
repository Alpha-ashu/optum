Feature: Request Tops account recovery claim payment details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://api-stg.uhg.com/api/payer/claims/claims360/1.0.0/payments/'

  Scenario Outline: Request for account recovery claim payment details validation
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row.testcase
    * def reqChkSrsDesgn = row.reqChkSrsDesgn
    * def reqChkNbr = row.reqChkNbr

    * print('********************', testcase, reqChkNbr, '[STARTED] ********************************')

    Given url api_url + reqChkNbr
    And header consumername = 'claims360_prod'
    And header X-Upstream-Env = 'stagecloud'
    And header next-key = '{"nextPageToken": "","pageNum": 1,"numPages": 0,"pageSize": 150}'
    And header checkSeriesDesignator = reqChkSrsDesgn
    And header SourceSystemCode = 'TOPS'
    And header bulkRecoveryIndicator = ''
    And header Authorization = accessToken
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'payment', scenario: 'Request for account recovery claim payment details', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, 'All_Responses/PPKG_Responses/' + testcase + '_' + reqChkNbr + '_ppkg.json')
    * print('********************', testcase, reqChkNbr, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/ppkg/tops/summary_TestData.csv') |