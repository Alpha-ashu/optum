Feature:

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/Claim360_NonProd_AccessToken.feature')
    * def accessToken = 'Bearer ' + callAccessToken.response.access_token
    * def api_url = 'https://gateway-stage-dmz.optum.com/api/dev/clm/claims360-edi/claims/v1/search'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row['testcase'] || row['\uFEFFtestcase'] || row.testcase
    * def reqSbmtProvId = row.reqSbmtProvId
    * def reqSbmtProvTyp = row.reqSbmtProvTyp
    * def reqSbmtMemId = row.reqSbmtMemId
    * def reqSbscrId = row.reqSbscrId
    * def reqClmSysId = row.reqClmSysId
    * def reqPolNbr = row.reqPolNbr
    * def reqCOSMDivCd = row.reqCOSMDivCd
    * def reqPNICCompCd = row.reqPNICCompCd
    * def reqPtntFstNm = row.reqPtntFstNm
    * def reqPtntBthDt = row.reqPtntBthDt
    * def reqFstSrvcDt = row.reqFstSrvcDt
    * def reqLstSrvcDt = row.reqLstSrvcDt
    * def json_string =
        """
        {
  "searchInput": {
    "reqExpandInd": "Y",
    "reqSbmtProvId": "#(reqSbmtProvId)",
    "reqSbmtProvTyp": "#(reqSbmtProvTyp)",
    "reqSbmtMemId": "#(reqSbmtMemId)",
    "reqCDBMemIdInfo": [
      {
        "reqSbscrId": "#(reqSbscrId)",
        "reqAlternId": "",
        "reqClmSysId": "#(reqClmSysId)",
        "reqTopsSeqNbr": "",
        "reqCDBRelCd": "",
        "reqCDBDepSeqNbr": "",
        "reqPolNbr": "#(reqPolNbr)",
        "reqCDBDepCd": "",
        "reqCOSMDivCd": "#(reqCOSMDivCd)",
        "reqPNICCompCd": "#(reqPNICCompCd)"
      }
    ],
    "reqPtntFstNm": "#(reqPtntFstNm)",
    "reqPtntBthDt": "#(reqPtntBthDt)",
    "reqFstSrvcDt": "#(reqFstSrvcDt)",
    "reqLstSrvcDt": "#(reqLstSrvcDt)",
    "reqTotChrgAmt": "",
    "reqClmNbr": "",
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


  Scenario Outline: Claims 360 B2B Member Search
    * print('********************', testcase, reqSbmtProvId, '[STARTED] ********************************')
    Given url api_url
    And header Authorization = accessToken
    And header Content-Type = 'application/json'
    And header consumername = 'claims360_np'
    And header roleid = ''
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def filename = 'All_Responses/Claim360/B2B/Member_Search/B2B_Responses/' + testcase + '_' + reqSbmtProvId + '_ppkg.json'
    * def perfData = { consumer: 'CLAIMS360', feature: 'b2b_member_search', scenario: 'Claim360 B2B member search request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)
    * print('********************', testcase, reqSbmtProvId, '[COMPLETED] ******************************')

    Examples:
      | read('classpath:testdata/claim360/b2b_member_search_testdata.csv') |
