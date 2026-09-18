Feature: Request Cosmos UPM PROD Summary

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos/claims/v3/search'
    * eval new java.io.File('target/All_Responses/ISET/UPM_Responses/Summary').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row.testcase
    * def payerClaimControlNumber = row.payerClaimControlNumber
#    * def memberId = row.memberNumber
#    * def claimNumber = row.claimNumber
#    * def groupNo = row.groupNo
#    * def site = row.site
#    * def startdate = row.startDate
#    * def enddate = row.endDate
#    * def ClaimType = row.claimType
    * def request_body = row.request
    * print('********************', testcase, payerClaimControlNumber, '[STARTED] ********************************')
#    * def json_string =
#    """
#    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
#    <ns2:searchInput xmlns:ns2="http://eaipclaims.apiengine.optum.com/clm/cosmos/claims/v3">
#        <controlModifier>
#            <cosmosSystemParameters>
#                <sourceId>17</sourceId>
#                <userId>63451</userId>
#            </cosmosSystemParameters>
#            <pagedResponse>YES</pagedResponse>
#            <uniqueClaim>NO</uniqueClaim>
#        </controlModifier>
#        <division>#(site)</division>
#        <providerType></providerType>
#        <groupNumber>#(groupNo)</groupNumber>
#        <subscriberNumber>#(memberId)</subscriberNumber>
#        <dependentCode>00</dependentCode>
#        <dateType>2</dateType>
#        <startServiceDate>#(startdate)</startServiceDate>
#        <endServiceDate>#(enddate)</endServiceDate>
#        <claimStatus>1</claimStatus>
#        <claimType>4</claimType>
#        <pagingStateBlock>
#            <moreData>false</moreData>
#        </pagingStateBlock>
#    </ns2:searchInput>
#    """

  Scenario Outline: Claim UPM summary request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/xml'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'ISET'
    And header Authorization = accessToken
    And request request_body
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)

    * print('********************', testcase, payerClaimControlNumber, '[COMPLETED] ******************************')
    * def filename = 'All_Responses/ISET/UPM_Responses/Summary/' + testcase + '_' + payerClaimControlNumber+ '_upm.json'
    * def perfData = { consumer: 'ISET', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg/ISET/summary_testdata.csv') |
