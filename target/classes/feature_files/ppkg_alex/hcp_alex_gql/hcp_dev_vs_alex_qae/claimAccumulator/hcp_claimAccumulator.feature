Feature: HCP Claim Accumulator GraphQL API Test

  Background:
    * def tokenResult = callonce read('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature')
    * def accessToken = tokenResult.accessToken
    * def query = read('classpath:testdata/hcp_gql/claimAccumulator/claimAccumulator.graphql')
    * def header = 'GQL ClaimTransaction'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def testcase = row.testcase
    * def ClaimTransactionIdentifier = row.claimTransactionIdentifier
    * def variables =
    """
    {
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


  Scenario Outline: Send GraphQL request for Claim Accumulator
    Given url 'https://api.uhg.com/graph/1.0.0/'
    And header Content-Type = 'application/json'
    And header x-upstream-environment = 'Dev'
    And header consumername = 'claims360_prod'
    And header Authorization = accessToken
    And request { "query": "#(query)", "variables": "#(variables)" }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ALEX', feature: 'hcp_claimAccumulator', scenario: 'Send GraphQL request for Claim Accumulator', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimTransactionIdentifier],'[COMPLETED] ******************************')
    * def sanitizedClaimId = claimTransactionIdentifier.replace(/:/g, '_')
    * def filename = 'All_Responses/HCP_Responses/' + testcase + '_' + sanitizedClaimId +  '_HCPResponse.json'
    * karate.write(response, filename)


    Examples:
      | read('classpath:testdata/hcp_gql/hcp_alex_testdata.csv') |