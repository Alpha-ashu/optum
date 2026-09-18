Feature:

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/Claim360_NonProd_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://gateway-stage-dmz.optum.com/api/dev/clm/claims360-edi/claims/v1/search'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row['testcase'] || row['\uFEFFtestcase'] || row.testcase
    * def reqClmNbr = row.reqClmNbr
    * def reqClmSysId = row.reqClmSysId
    * def reqSbmtProvId = row.reqSbmtProvId
    * def json_string =
        """
        {
  "searchInput": {
    "reqExpandInd": "Y",
    "reqSbmtProvId": "#(reqSbmtProvId)",
    "reqSbmtProvTyp": "T",
    "reqSbmtMemId": "111111119",
    "reqCDBMemIdInfo": [
      {
        "reqSbscrId": "111111119",
        "reqAlternId": "",
				"reqClmSysId": "#(reqClmSysId)",
        "reqTopsSeqNbr": "",
        "reqCDBRelCd": "",
        "reqCDBDepSeqNbr": "",
				"reqPolNbr": "AAAAAA",
        "reqCDBDepCd": "",
        "reqCOSMDivCd": "ABC",
        "reqPNICCompCd": "00"
      }
    ],
    "reqPtntFstNm": "ABCDEF",
    "reqPtntBthDt": "9999-01-01",
    "reqFstSrvcDt": "9999-01-01",
    "reqLstSrvcDt": "9999-01-01",
    "reqTotChrgAmt": "",
    "reqClmNbr": "#(reqClmNbr)",
    "reqPtntAcctNbr": "",
    "reqTransId": "",
    "reqSubmtrId": "",
    "reqNxtKeyFunctionality": {
      "reqAddtlRecInd": "N",
      "reqPageNbr": "0",
      "reqPageSize": "25",
      "reqNextIcn": ""
    },
    "reqMpinTin": [
      {
        "reqMpin": "",
        "reqTin": ""
      }
    ],
    "reqVariableArea": [
      {
        "reqNpi": [
          ""
        ]
      }
    ]
  }
}
"""
  Scenario Outline: Claims 360 B2B FLN Search
    * print('********************', testcase, reqClmNbr, '[STARTED] ********************************')
    Given url api_url
    And header Authorization = accessToken
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_np'
    And header environment = 'de-canary'
    And header roleid = ''
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def filename = 'All_Responses/Claim360/B2B/FLN_Search/Decanary_Responses/' + testcase + '_' + reqClmNbr + '_decan.json'
    * def perfData = { consumer: 'CLAIMS360', feature: 'b2b_fln_search_decanary', scenario: 'Claim360 B2B de-canary FLN search request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)
    * print('********************', testcase, reqClmNbr, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/claim360/b2b_fln_search_testdata.csv') |
