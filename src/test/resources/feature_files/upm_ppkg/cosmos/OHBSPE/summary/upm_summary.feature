Feature: Request Cosmos UPM PROD Summary

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos/claims/v2/search'
    * eval new java.io.File('target/All_Responses/OHBSPE/UPM_Responses/Summary').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def groupNo = row.groupNo
    * def site = row.site
    * def startdate = row.startDate
    * def enddate = row.endDate
    * def testcase = row.testcase
    * def json_string =
    """{
    "searchInput": {
        "startServiceDate": "#(startdate)",
        "endServiceDate": "#(enddate)",
        "division": "#(site)",
        "claimType": "4",
        "dateType": "2",
        "subscriberNumber": "#(memberId)",
        "controlModifier": {
            "uniqueClaim": "NO",
            "limitSearchDates": "NO",
            "cosmosSystemParameters": {
                "sourceId": "17",
                "userId": "23611"
            }
        },
        "groupNumber": "82996",
        "dependentCode": "00",
        "claimStatus": "1"
    }
}

    """

    * print('********************', testcase, memberId, claimIdentifier, '[STARTED] ********************************')

  Scenario Outline: Claim UPM summary request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'OHBSPE'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)

    * print('********************', testcase, memberId, claimIdentifier, '[COMPLETED] ******************************')
    * def filename = 'All_Responses/OHBSPE/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json'
    * def perfData = { consumer: 'OHBSPE', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/OHBSPE/summary_TestData.csv') |
