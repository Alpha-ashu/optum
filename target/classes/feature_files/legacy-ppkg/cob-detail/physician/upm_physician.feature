Feature: Request Tops COB UPM PROD read claim Details
  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Cob_Prod_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def ltpaToken = callAccessToken.ltpaToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cob-detail/claims/v1'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def reqInvnCtlNbr = row.internalReferenceIdentifier
    * def testcase = row.testcase
    * def request_body =
    """
   {
   "reqFields":
   {
    "reqClmSysId": null,
    "reqInvnCtlNbr": "#(reqInvnCtlNbr)",
    "reqMaxNbrOccurs": null,
    "reqMaxWaitTm": null,
    "reqAddtlRecInd": null,
    "reqClmSeqNbr": null,
    "reqTsqNm": null
    }
    }
    """

    * print('********************',[testcase],[reqInvnCtlNbr],'[STARTED] ********************************')
  Scenario Outline: Request for COB claim details validation
    Given url api_url
    And header Accept = '*/*'
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_prod'
    And header Authorization = accessToken
    And cookie LtpaToken2 = ltpaToken
    And request request_body
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'CobDetailApi', scenario: 'Request for claim details validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[reqInvnCtlNbr],'[COMPLETED] ********************************')
    * def filename = 'All_Responses/TOPS/UPM_Responses/Physician/' + testcase + '_' + reqInvnCtlNbr + '_upm.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/ppkg/tops/cob_Physician_Testdata.csv') |
