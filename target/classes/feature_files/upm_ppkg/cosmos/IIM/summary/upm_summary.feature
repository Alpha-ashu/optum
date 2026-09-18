Feature: Request Cosmos UPM PROD Summary

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos/claims/v3/search'
    * eval new java.io.File('target/All_Responses/IIM/UPM_Responses/Summary').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def groupNo = row.groupNo
    * def site = row.site
    * def testcase = row.testcase
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
    * def json_string =
    """
    {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "2025-02-01",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "2025-04-01",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

  Scenario Outline: Claim UPM summary request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header Authorization = accessToken
    And header actor = 'IIM'
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/IIM/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json'
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/IIM/cosmos-claims/summary_TestData.csv') |
