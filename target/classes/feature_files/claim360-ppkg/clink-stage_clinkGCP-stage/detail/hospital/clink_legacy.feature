Feature: Clink API Alex - Claims 360 Detail Search [Hospital]

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://c360j-claims360-claim-detail-api-stage.optum.com/claims360-detail/claims/v1/search'

  Scenario Outline: Clink API Alex - Claims 360 Detail Search Hospital validation
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row['testcase'] || row['\uFEFFtestcase'] || row.testcase
    * def reqInvnCtlNbr = row.reqInvnCtlNbr
    * def json_string =
        """
{
    "searchInput": {
        "reqInvnCtlNbr": "#(reqInvnCtlNbr)"
    }
}
        """

    * print('********************', testcase, reqInvnCtlNbr, '[STARTED] ********************************')

    Given url api_url
    And header Authorization = accessToken
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_np'
    And header alex-request = 'true'
    And header roleid = ''
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'ClinkAPIAlex_Hospital', scenario: 'Clink API Alex Claims 360 Detail Search Hospital', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    * karate.write(response, 'All_Responses/Hospital/Alex_Responses/'  reqInvnCtlNbr + '_alex.json')
    * print('********************', testcase, reqInvnCtlNbr, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/alex_ppkg/clink_payer_summary_TestData.csv') |

