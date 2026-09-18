Feature: Alex Claim Transaction GraphQL API Test

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/ALEX_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def query = read('classpath:testdata/hcp_gql/claimPricing/claimPricing.graphql')
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
  Scenario Outline: Send GraphQL request for claim transaction
    Given url 'https://api.uhg.com/api/payer/product/payergraphql/v1/graphql'
    And header Content-Type = 'application/json'
    And header source = 'alex'
    And header Authorization = accessToken
    And request { "query": "#(query)", "variables": "#(variables)" }
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'ALEX', feature: 'alex_claimPricing', scenario: 'Send GraphQL request for claim transaction', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[claimTransactionIdentifier],'[COMPLETED] ******************************')
    * def sanitizedClaimId = claimTransactionIdentifier.replace(/:/g, '_')
    * def filename = 'All_Responses/Alex_Responses/' + testcase + '_' + sanitizedClaimId +  '_AlexResponse.json'
    * karate.write(response, filename)


    Examples:
      | read('classpath:testdata/hcp_gql/hcp_alex_TestData.csv') |
