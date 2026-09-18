Feature: Request Cosmos TOPS PPKG PROD read claim Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def internalReferenceIdentifier = row.inventoryControlNumber
    * def searchtype = row.searchtype
    * def claimtype = row.claimType
    * def testcase = row.testcase
    * print('********************',[testcase],[internalReferenceIdentifier],'[STARTED] ********************************')
  Scenario Outline: Request for PPKG Hospital claim details validation
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + internalReferenceIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'PROD'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header claim-type = claimtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * print('********************',[testcase],[internalReferenceIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/TOPS/PPKG_Responses/Hospital/' + testcase + '_' + internalReferenceIdentifier + '_ppkg.json'
    * def perfData = { consumer: 'TOPS', feature: 'ppkg_hospital', scenario: 'Request for PPKG Hospital claim details validatio', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/ppkg/tops/cob_Hospital_Testdata.csv') |
