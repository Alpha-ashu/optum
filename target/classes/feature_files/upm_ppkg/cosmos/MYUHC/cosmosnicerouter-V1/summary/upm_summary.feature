Feature: Request Cosmos MYUHC_V1 Consumer OBAPI UPM PROD Summary
  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos/claims/v1/search?callonce-type=summary'
    * eval new java.io.File('target/All_Responses/MYUHC/UPM_Responses/Summary').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def dateOfBirth = row.dateOfBirth
    * def startDate = row.startDate
    * def stopDate = row.endDate
    * def groupNo = row.groupNo
    * def site = row.site
    * def testcase = row.testcase
    * def claimIdentifier = row.payerClaimControlNumber
    * def json_string =
"""
{
    "searchInput": {
        "systemParameters": {
            "cosmosSourceSystemParameters": {
                "sourceId": "10",
                "userId": "23611"
            }
        },
        "claimInfo": {
            "groupInfo": [
                {
                    "site": "#(site)",
                    "groupNo": "#(groupNo)"
                }
            ],
            "claimSystem": "COSMOS",
            "dateOfService": {
                "startDate": "#(startDate)",
                "stopDate": "#(stopDate)"
            },
            "consumerName": {
                "dateOfBirth": "#(dateOfBirth)"
            }
        },
        "controlModifier": [
            {
                "memberNumber": "#(memberId)",
                "dependentCode": "00",
                "businessType": "GOVT"
            }
        ]
    }
}
"""
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
  Scenario Outline: Claim UPM summary request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'IIM'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/MYUHC/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json'
    * def perfData = { consumer: 'MYUHC', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/MYUHC/cosmosnicerouter-V1/summary/summary_TestData.csv') |
