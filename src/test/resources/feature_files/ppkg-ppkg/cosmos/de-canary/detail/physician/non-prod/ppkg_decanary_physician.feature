Feature: Request Cosmos PayerPackage Non-PROD Physician Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def ICN = row.internalReferenceIdentifier
    * def testcase = row.testcase
    * print('********************', [testcase], [ICN], '[STARTED] ****************************')

  Scenario Outline: Get PayerPackage Physician Details
    Given url 'https://api-stg.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + ICN
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'Development'
    And header environment = 'de-canary'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_np'
    And header search-type = searchtype
    And header claim-type = claimtype

    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'TOPS', feature: 'ppkg_nonprod_Physician', scenario: 'Get PayerPackage Hospital Details', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************', [testcase], [ICN], '[COMPLETED] **************************')
    * def filename = 'All_Responses/TOPS/Decanary_Responses/Physician/'+ testcase +'_'+ ICN + '_ppkg.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/decanary/decanarydetailphysician.csv') |
