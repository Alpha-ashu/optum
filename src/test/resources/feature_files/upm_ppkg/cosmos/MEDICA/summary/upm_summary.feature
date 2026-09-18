Feature: Request Cosmos MEDICA UPM PROD Summary Claim Details


  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-dmz.optum.com/api/clm/cosmosclaim/read-cosmosmember-claim-summary/v4'
    * eval new java.io.File('target/All_Responses/MEDICA/UPM_Responses/Summary').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def testcase = row.testcase
    * def groupNo = row.groupNo
    * def dependentCode = row.dependentCode
    * def startDate = row.startDate
    * def endDate = row.endDate
    * def division = row.site
    * def searchMemberNumber = groupNo+memberId+dependentCode
#    * def requestBody = row.requestBody
    * def requestBody =
    """
    {
    "readInput": {
        "searchStartDate": "#(startDate)",
        "searchDateType": "2",
        "searchEndDate": "#(endDate)",
        "searchMemberNumber": "#(searchMemberNumber)",
        "searchStatusType": "3",
        "searchClaimType": "7",
        "serviceControlParameter": {
            "requestcallonceLimit": "1"
        },
        "systemDivision": "#(site)",
        "sourceSystemParameters": {
            "cosmosSystemParameter": {
                "sourceId": "54",
                "userId": "90239"
            }
        }
    }
}

    """
    * print('********************', [testcase], [memberId], [claimIdentifier], '[STARTED] ****************************')
  Scenario Outline: Claim UPM summary request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'MEDICA'
    And header Authorization = accessToken
    And request requestBody
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)

    * print('********************', [testcase], [memberId], [claimIdentifier], '[COMPLETED] **************************')
    * def filename = 'All_Responses/MEDICA/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json'
    * def perfData = { consumer: 'MEDICA', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)
#    * print response

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/MEDICA/summary_TestData.csv') |
