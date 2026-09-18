Feature: Request Cosmos PayerPackage Non-prod Summary

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/Claim360_NonProd_AccessToken.feature')
    * def accessToken =  callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def ICN = row.internalReferenceIdentifier
    * def TIN = row.tin
    * def searchtype = row.searchtype
    * def testcase = row.testcase
    * def api_url = 'https://gateway-stage-dmz.optum.com/api/dev/clm/claims360-summ/claims/v1/search'
    * def json_string =
    """
    {
    "searchInput": {
        "reqClmSysId": "",
        "reqTin": "#(TIN)",
        "reqSearchType": "#(searchtype)",
        "reqInvnCtlNbr": "#(ICN)",
        "reqNxtKeyFunctionality": {
            "reqAddtlRecInd": "",
            "reqPageNbr": "1",
            "reqNextIcn": "",
            "reqPageSize": "300"
        }
    }
}
    """
    * print('********************', [testcase], [ICN], '[STARTED] **************************')

  Scenario Outline:
    Given url api_url
    And header Accept = '*/*'
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_np'
    And header Connection = 'keep-alive'
    And header Authorization = accessToken
    And header roleid = ''
    And header environment = 'de-canary'
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * print('********************', [testcase], [ICN], '[COMPLETED] ******************************')
    * def filename = 'All_Responses/Claim360/PPKG_Responses/Summary/' + testcase + '_' + ICN + '_decan.json'
    * def perfData = { consumer: 'COSMOS', feature: 'claim360_summary_decanary', scenario: 'Claim360 de-canary summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/claim360/summary_TestData.csv') |