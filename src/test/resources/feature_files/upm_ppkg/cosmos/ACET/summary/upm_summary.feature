Feature: Request Cosmos ACET UPM PROD Summary Claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos/claims/v2/search'

    * eval new java.io.File('target/All_Responses/ACET/UPM_Responses/Summary').mkdirs()

    * def UUID = Java.type('java.util.UUID')

  Scenario Outline: Request for UPM Summary claim details validation
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def groupNo = row.groupNo
    * def site = row.site
    * def startdate = row.startDate
    * def enddate = row.endDate
    * def testcase = row.testcase
    * def ClaimType = row.claimType
    * def json_string =
        """
        {
          "searchInput": {
            "startServiceDate": "#(startdate)",
            "endServiceDate": "#(enddate)",
            "division": "#(site)",
            "subscriberNumber": "#(memberId)",
            "controlModifier": {
              "uniqueClaim": "NO",
              "limitSearchDates": "NO",
              "cosmosSystemParameters": {
                "sourceId": "17",
                "userId": "23611"
              }
            },
            "groupNumber": "#(groupNo)"
          }
        }
        """

    * print('********************', testcase, memberId, claimIdentifier, '[STARTED] ********************************')

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ACET', feature: 'upm_summary', scenario: 'Request for UPM Summary claim details validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    * karate.write(response, 'All_Responses/ACET/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json')
    * print('********************', testcase, memberId, claimIdentifier, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/ACET/summary_TestData.csv') |
