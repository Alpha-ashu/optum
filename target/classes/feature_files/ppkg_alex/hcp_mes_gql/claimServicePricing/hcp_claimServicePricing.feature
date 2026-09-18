Feature: HCP Claim Service Pricing GraphQL API Test

  Background:
    * def tokenResult = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = tokenResult.accessToken
    * def query = read('classpath:testdata/hcp_gql/claimServicePricing/claimServicePricing.graphql')
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def ClaimTransactionIdentifier = row.claimTransactionIdentifier
    * def claimNumber = row.claimNumber
    * def claimSubmittedIdentifier = row.claimSubmittedIdentifier
    * def testcase = row.testcase
    * def variables =
    """
    {
	"claimServiceLine": true,
	"query": {
		"limit": {
			"pageSize": 500
		},
		"where": {
			"and": [
				{
					"claimTransactionIdentifier": {
						"_eq": "#(claimTransactionIdentifier)"
					}
				}
			]
		}
	}
}
    """


  Scenario Outline: Send GraphQL request for Claim Service Pricing
    Given url 'https://api.uhg.com/graph/1.0.0/'
    And header Content-Type = 'application/json'
    And header x-upstream-environment = 'PROD'
    And header consumername = 'claims360_prod'
    And header Authorization = accessToken
    And request { "query": "#(query)", "variables": "#(variables)" }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ALEX', feature: 'hcp_claimServicePricing', scenario: 'Send GraphQL request for Claim Service Pricing', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimTransactionIdentifier],'[COMPLETED] ******************************')
    * def sanitizedClaimId = claimTransactionIdentifier.replace(/:/g, '_')
    * def filename = 'All_Responses/HCP_Responses/' + testcase + '_' + sanitizedClaimId +  '_HCPResponse.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/hcp_gql/hcp_mes_sample.csv') |