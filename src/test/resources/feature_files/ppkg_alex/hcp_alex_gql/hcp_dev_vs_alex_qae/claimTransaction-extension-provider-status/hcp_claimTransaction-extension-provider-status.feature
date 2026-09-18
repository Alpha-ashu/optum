Feature: HCP Service Ambulance GraphQL API Test

  Background:
    * def tokenResult = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = tokenResult.accessToken
    * def query = read('classpath:testdata/hcp_gql/claimTransaction-extension-provider-status/claimTransaction-extension-provider-status.graphql')
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def ClaimTransactionIdentifier = row.claimTransactionIdentifier
    * def claimNumber = row.claimNumber
    * def claimSubmittedIdentifier = row.claimSubmittedIdentifier
    * def testcase = row.testcase
    * def variables =
    """
    {
	"query": {
		"where": {
			"and": [
				{
					"claimSubmittedIdentifier": {
						"_eq": "FM03701874"
					}
				}
			]
		},
		"limit": {
			"pageSize": 500,
			"page": 1
		}
	}
}
    """


  Scenario Outline: Send GraphQL request for Service Ambulance
    Given url 'https://api.uhg.com/graph/1.0.0/'
    And header Content-Type = 'application/json'
    And header x-upstream-environment = 'Dev'
    And header consumername = 'claims360_prod'
    And header Authorization = accessToken
    And request { "query": "#(query)", "variables": "#(variables)" }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ALEX', feature: 'hcp_claimTransaction-extension-provider-status', scenario: 'Send GraphQL request for Service Ambulance', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimTransactionIdentifier],'[COMPLETED] ******************************')
    * def sanitizedClaimId = claimTransactionIdentifier.replace(/:/g, '_')
    * def filename = 'All_Responses/HCP_Responses/' + testcase + '_' + sanitizedClaimId +  '_HCPResponse.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/hcp_gql/hcp_alex_testdata.csv') |