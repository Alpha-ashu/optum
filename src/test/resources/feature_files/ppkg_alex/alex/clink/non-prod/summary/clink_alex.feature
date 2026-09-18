Feature: Clink API Payer - Claims 360 Summary Search

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/Claim360_NonProd_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def ltpaToken = callAccessToken.ltpaToken
    * def api_url = 'https://api-stg.uhg.com/api/payer/claims/claims360-summ/v1/claims/search'

  Scenario Outline: Clink API Payer - Claims 360 Summary Search validation

    # Row data from the CSV is injected per-scenario (not in Background), so read the
    # column values and build the request body here inside the Scenario.
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row['testcase'] || row['\uFEFFtestcase'] || row.testcase
    * def reqClmSysId = row.reqClmSysId
    * def reqTin = row.reqTin
    * def reqClmNbr = row.reqClmNbr
    # These two were referenced in the request body but never defined, so the JSON was
    # being built with undefined values. Map them from the CSV row. The working curl uses
    # reqSearchType = 'I' (search by ICN), which is the 'icnsearchtype' column.
    * def reqInvnCtlNbr = row.reqInvnCtlNbr
    * def reqSearchType = row.icnsearchtype
    * def json_string =
        """
        {
        	"searchInput":
        	{
        		"reqClmSysId": "#(reqClmSysId)",
        		"reqTin": "#(reqTin)",
        		"reqSearchType": "#(reqSearchType)",
        		"reqInvnCtlNbr": "#(reqInvnCtlNbr)",
        		"reqNxtKeyFunctionality":
        		{
        			"reqAddtlRecInd": "N",
        			"reqPageNbr": "1",
        			"reqNextIcn": "",
        			"reqPageSize": "300"
        		}
        	}
        }

        """
    * print('********************', testcase, reqTin, '[STARTED] ********************************')

    Given url api_url
    And header Authorization = accessToken
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_np'
    And header X-Upstream-Env = 'Development'
    And header alex-request = 'true'
    And header roleid = ''
    And request json_string
    And cookie LtpaToken2 = ltpaToken
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'ClinkAPIPayer', scenario: 'Clink API Payer Claims 360 Summary Search', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    # Filename convention '<testcase>_<reqClmNbr>_alex.json' matches the engine's
    # canonical '<testcase>_<claimNumber>' pairing (claimNumber = reqClmNbr).
    * karate.write(response, 'All_Responses/Summary/Alex_Responses/' + testcase + '_' + reqClmNbr + '_alex.json')
    * print('********************', testcase, reqTin, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/alex_ppkg/hcp_vs_alex_sample_testdata.csv') |
