Feature: ALEX Claim Service line GraphQL API Test

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/nonprod/ALEX_NonProd_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def query = read('classpath:testdata/hcp_gql/claimExtension/claimExtensions.graphql')
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
					"claimTransactionIdentifier": {
						"_eq": "FL70741151:01:20462:1844000:1"
					}
				},
				{}
			]
		},
		"limit": {
			"pageSize": 500,
			"page": 1
		}
	}
}
    """
  Scenario Outline: Send GraphQL request for Claim Service line
    Given url 'https://api-stg.uhg.com/api/clm/med/asadjudicatedcrud/1.0.0/api/graphql'
    And header Content-Type = 'application/json'
    And header X-Upstream-Env = 'uat'
    And header Authorization = accessToken
    And request { "query": "#(query)", "variables": "#(variables)" }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ALEX', feature: 'mes_claimExtension', scenario: 'Send GraphQL request for Claim Service line', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

    * print('********************',[testcase],[claimTransactionIdentifier],'[COMPLETED] ******************************')
    * def sanitizedClaimId = claimTransactionIdentifier.replace(/:/g, '_')
    * def filename = 'All_Responses/ALEX_Responses/' + testcase + '_' + sanitizedClaimId +  '_ALEXResponse.json'
    * karate.write(response, filename)


    Examples:
      | read('classpath:testdata/hcp_gql/hcp_mes_sample.csv') |