Feature: Request Cosmos ALEX Non-PROD Claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/ALEX_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * eval new java.io.File('target/All_Responses/Alex_Negative').mkdirs()
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def claimIdentifier = row.payerClaimControlNumber
    * def memberIdRaw = '' + row.memberNumber
    * def memberId = memberIdRaw.endsWith('.0') ? memberIdRaw.slice(0, -2).padStart(9, '0') : memberIdRaw.padStart(9, '0')
    * def claimNumber = row.claimNumber
    * def testcase = row.testcase
    * print('********************', [testcase],[claimIdentifier], '[STARTED] ******************************')

  Scenario Outline: Get PayerPackage claim in Alex Environment and get the claim Details to compare with PPKG
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'qae'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_np'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    And retry until responseStatus != 429
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'IIM', feature: 'alex_nonprod_physician', scenario: 'Get PayerPackage claim in Alex Environment and get', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/Hospital/Alex_Responses/' + testcase + '_' + claimIdentifier + '_alexResponse.json'
    * karate.write(response, filename)


    Examples:
      | read('classpath:testdata/alex_ppkg/hcp_vs_alex_sample_testdata.csv') |

