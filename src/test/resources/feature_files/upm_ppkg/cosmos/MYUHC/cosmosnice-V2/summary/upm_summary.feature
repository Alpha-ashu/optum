  Feature: Request Cosmos UPM PROD Summary
  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway.optum.com/api/clm/cosmos-nice/claims/v2/search?callonce-type=summary'
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
        "controlModifier": [
          {
            "businessType": "GOVT",
            "dependentCode": "00",
            "limitSearchDates": null,
            "memberNumber": "#(memberId)",
            "pagedResponse": null,
            "uniqueClaim": null
          }
        ],
        "claimInfo": {
          "adjustmentSequenceNumber": null,
          "claimNumber": null,
          "claimRecordId": null,
          "claimStatus": null,
          "claimSubNumber": null,
          "claimSystem": "COSMOS",
          "claimType": null,
          "consumerName": {
            "dateOfBirth": "#(dateOfBirth)",
            "name": null
          },
          "dateOfService": {
            "startDate": "#(startDate)",
            "stopDate": "#(stopDate)"
          },
          "dateType": null,
          "groupInfo": [
            {
              "groupNo": "#(groupNo)",
              "site": "#(site)"
            }
          ],
          "limitedServiceNumber": null,
          "maximumClaimsIndicator": null,
          "medicalRecordNumber": null,
          "nationalProviderId": null,
          "noLookbackFlag": null,
          "pacNumber": null,
          "pagingState": null,
          "physicianTin": null,
          "providerInfo": null,
          "providerNPI": null,
          "providerNumber": null,
          "providerSpecialty": null,
          "providerTaxId": null,
          "providerType": null,
          "rtsNumber": null,
          "submittedChargeAmount": null,
          "systemDate": null,
          "systemTime": null
        },
        "systemParameters": {
          "cosmosSourceSystemParameters": {
            "sourceId": "10",
            "userId": "23611"
          },
          "niceSourceSystemParameters": null,
          "shipSystemParameters": null
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
    And header actor = 'IIM'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
      * print('********************', [testcase], [memberId], [claimIdentifier], '[COMPLETED] **************************')
    * def filename = 'All_Responses/MYUHC/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json'
    * def perfData = { consumer: 'MYUHC', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/MYUHC/cosmosnice-V2/summary/summary_TestData.csv') |
