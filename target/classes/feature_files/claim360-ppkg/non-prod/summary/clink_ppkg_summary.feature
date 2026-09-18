Feature: Clink API Payer - Claims 360 Summary Search

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://gateway-stage-dmz.optum.com/api/dev/clm/claims360-summ/claims/v1/search'

  Scenario Outline: Clink API Payer - Claims 360 Summary Search validation
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row['testcase'] || row['\uFEFFtestcase'] || row.testcase
    * def reqClmSysId = row.reqClmSysId
    * def reqTin = row.reqTin
    * def reqClmNbr = row.reqClmNbr
    * def json_string =
        """
{
    "searchInput": {
        "reqClmSysId": "#(reqClmSysId)",
        "reqTin": "#(reqTin)",
        "reqSearchType": "C",
        "reqClmNbr": "#(reqClmNbr)",
        "reqNxtKeyFunctionality": {
            "reqAddtlRecInd": "N",
            "reqPageNbr": "1",
            "reqNextIcn": "",
            "reqPageSize": "300"
        }
    }
}
        """

    * print('********************', testcase, reqTin, '[STARTED] ********************************')

    Given url api_url
    And header Authorization = accessToken
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_np'
    And header roleid = ''
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'ClinkAPIPayer', scenario: 'Clink API Payer Claims 360 Summary Search', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    * karate.write(response, 'All_Responses/Summary/PPKG_Responses/' + reqTin + '_' + reqClmNbr + '_ppkg.json')
    * print('********************', testcase, reqTin, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/alex_ppkg/clink_payer_summary_TestData.csv') |
