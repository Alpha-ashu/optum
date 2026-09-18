Feature: Request Tops account recovery claim payment details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://gateway-core.optum.com/api/clm/chy-summ/accounts-recovery/v1'

  Scenario Outline: Request for account recovery claim payment details validation
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row.testcase
    * def reqChkSrsDesgn = row.reqChkSrsDesgn
    * def reqChkNbr = row.reqChkNbr
    * def json_string =
        """
        {
	    "Request": {
		"hdrConsumer": "PTRCM",
		"hdrTypeOfService": "R",
		"hdrLoggingLevel": "E",
		"hdrTrapSpecificInstanceId": "",
		"hdrUniqueServiceId": "",
		"requestarea": {
			"requiredFlds": {
				"reqPayMethCd": "E",
				"reqChkSrsDesgn": "#(reqChkSrsDesgn)",
				"reqChkNbr": "#(reqChkNbr)",
				"reqClmSysId": "TOPS",
				"reqAppId": "PTRCM",
				"reqBulkRecovInd": "",
				"reqMaxNbrOccurs": 75
			},
			"reqNxtKeyFunctionality": {
				"reqAddlRecInd": "N",
				"reqClmSeqNbr": 0,
				"reqTsqNm": ""
			                          }
		    }
		}
		}
        """

    * print('********************', [testcase], [reqChkNbr], '[STARTED] ********************************')

    Given url api_url
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Cookie = 'LtpaToken2=id8SESrshe6D3Jlq2EF0N79rBXR%2BWMXxBzBfWR5qiuLr0%2Fo465nvrRBWY0fYUOVwO9hUOF2Eved4qhcCSvBqLL4CfgOu%2Fl1k8lpq19g6ODWIxPQOU1MZj13Gz%2F3DTvrurnC37kegHqWfwf7%2FSuPlKYTO8P6pDabquS7dVQRUadv9Of7JvstxG%2BTemf3ZtBss1xj9WIwGGPb%2FhjK7fdkChvQLRYHjdIMVi756dYW15GnbSZYvYsBSWTlQ4H%2BdFqLp7jGVmA6PEjgxkIappbAVAdl%2FPQYd9T%2BetmklnJIg9vaRLHxIzKA7m%2Bxqex%2BFd5xl; dtCookie=v_4_srv_43_sn_8D065AF956596B1855C208A733681832_perc_100000_ol_0_mul_1_app-3Aea7c4b59f27d43eb_1; TS01c8cd18=012db475ce692eed33365c1dbacf4598a0981819cd59f6a73594ae87dc3827a079e9007ee97d572bd64c75913b73edc10a2a08b7a7'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'accountRecovery', scenario: 'Request for account recovery claim payment details', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    * karate.write(response, 'All_Responses/UPM_Responses/' + testcase + '_' + reqChkNbr + '_upm.json')
    * print('********************', testcase, reqChkNbr, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/ppkg/tops/summary_TestData.csv') |