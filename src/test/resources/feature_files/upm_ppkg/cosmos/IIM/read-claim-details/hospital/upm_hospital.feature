Feature: Request Cosmos IIM UPM PROD Hospital Details
  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/claim/readclaimdetail/v13'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimnumber = row.claimNumber
    * def memberId = row.memberNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimType = row.claimtype
    * def site = row.site
    * def testcase = row.testcase
    * def request_body =
    """
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <soapenv:Header></soapenv:Header>
    <soapenv:Body>
        <ns1:invokeService xmlns:ns1="http://upm3.uhc.com/claim/readclaimdetail/v13">
            <arg0>
                <requestHeader>
                    <applicationName>IIM</applicationName>
                    <applicationInstanceName>IIM</applicationInstanceName>
                    <logLevel>DEBUG</logLevel>
                    <serviceOption>
                        <key>SECURITY_GROUPS</key>
                        <value>UPM3_MIIM_TST,UPM3_MIIM_STG,UPM3_MIIM_PROD,LeadsService_SRVCGRP,LeadsService_NONPRODSRVCGRP,</value>
                    </serviceOption>
                </requestHeader>
                <readClaimControlModifiers>
                    <cosmosSystemParameter>
                        <sourceId>17</sourceId>
                        <userId>23611</userId>
                    </cosmosSystemParameter>
                    <sourceSystem>COSMOS</sourceSystem>
                </readClaimControlModifiers>
                <systemDivision>#(site)</systemDivision>
                <claimType>HOSPITAL</claimType>
                <auditControlNumber>#(claimnumber)</auditControlNumber>
                <auditSubNumber>00</auditSubNumber>
                <recordId>01</recordId>
            </arg0>
        </ns1:invokeService>
    </soapenv:Body>
</soapenv:Envelope>
"""

    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')

  Scenario Outline: Claim UPM details Hospital request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/xml'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header actor = 'IIM'
    And header Authorization = accessToken
    And request request_body
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'IIM', feature: 'upm_hospital', scenario: 'Claim UPM details Hospital request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/IIM/UPM_Responses/Hospital/' + memberId + '_' + claimNumber + '_upm.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/IIM/read-claim-details/hospital_TestData.csv') |
