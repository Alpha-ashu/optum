Feature: Request Cosmos OHBSPE UPM PROD Physician Details
  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmosclaim/readcosmosphysicianclaimdetail/v8'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimnumber = row.claimNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def memberId = row.memberNumber
    * def testcase = row.testcase
    * def systemDate = row.systemDate
    * def systemTime = row.systemTime
    * def site = row.site
    * def request_body =
    """
    {
    "readInput": {
        "recordId": "01",
        "auditControlNumber": "#(claimnumber)",
        "controlModifiers": {
            "cosmosSystemParameter": {
                "sourceId": "15",
                "userId": "90251"
            },
            "getMorePhysicianClaims": false
        },
        "systemDate": "#(systemDate)",
        "auditSub": "00",
        "systemTime": "#(systemTime)",
        "systemDivision": "#(site)"
    }
}

    """
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
  Scenario Outline: Claim UPM details Hospital request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'OHBSPE'
    And header Authorization = accessToken
    And request request_body
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'OHBSPE', feature: 'upm_physician', scenario: 'Claim UPM details Hospital request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/OHBSPE/UPM_Responses/Physician/' + memberId + '_' + claimNumber + '_upm.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/OHBSPE/physician_TestData.csv') |
