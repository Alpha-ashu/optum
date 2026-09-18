Feature: Request Cosmos ISET UPM PROD Physician Details
  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos-facets/claims/v2/read'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimnumber = row.claimNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def memberId = row.memberNumber
    * def site = row.site
    * def claimTypeFull = row.claimTypeFull
    * def testcase = row.testcase
    * def request_body =
    """
    {
  "readInput": {
    "readClaimControlModifiers": {
      "cosmosSystemParameter": {
        "sourceId": "17",
        "userId": "23611"
      },
      "sourceSystem": "COSMOS"
    },
    "systemDivision": "#(site)",
    "claimType": "#(claimTypeFull)",
    "auditControlNumber": "#(claimnumber)",
    "auditSubNumber": "00",
    "recordId": "01",
    "adjustmentSequenceNumber": "",
    "additionalDescriptions": "Y"
  }
}
    """
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
  Scenario Outline: Claim UPM details Hospital request validation
#    * print request_body
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'ISET'
    And header Authorization = accessToken
    And request request_body
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ISET', feature: 'upm_physician', scenario: 'Claim UPM details Hospital request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/ISET/UPM_Responses/Physician/' + testcase + '_' + claimIdentifier + '_upm.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg/ISET/summary_testdata.csv') |
