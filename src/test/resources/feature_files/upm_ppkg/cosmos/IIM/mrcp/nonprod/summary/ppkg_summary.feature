Feature: Request Cosmos  PayerPackage MRCP Non-prod Summary Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def memberId = row.memberNumber
    * def searchtype = row.searchtype
    * def testcase = row.testcase
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
  Scenario Outline: Getting Single Record Based on Claim-identifiers
    Given url 'https://api.uhg.com/api/clm/hist/claims360/1.0.0/claims/' + claimIdentifier
    And header Authorization = accessToken
    And header event-type = 'SERVICE'
    And header X-Upstream-Env = 'STAGE'
    And header fields-response = 'claimIdentifiers,claimCategories,claimState,claimLevelTotals,patient,providers,healthCareInformation,claimNotes,claimAttachments,insurance,otherInsurance,claimSupportingInformation,payment,serviceLines.serviceLineState,serviceLines.healthCareInformation,serviceLines.insurance,serviceLines.otherInsurance,serviceLines.claimServiceNotes,serviceLines.claimServiceAttachments,serviceLines.subtotals,serviceLines.supportingServiceInformation'
    And header consumername = 'claims360_prod'
    And header search-type = searchtype
    And header match-encounter-claims-only = 'TRUE'
    When method get
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'IIM', feature: 'ppkg_summary', scenario: 'Getting Single Record Based on Claim-identifiers', endpoint: '#(karate.info.scenarioName)', method: 'GET', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/IIM/PPKG_Responses/Summary/' + memberId + '_' + claimNumber + '_ppkg.json'
    * karate.write(response, filename)
    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/IIM/cosmos-claims/IIM_MRCP_Summary.csv') |