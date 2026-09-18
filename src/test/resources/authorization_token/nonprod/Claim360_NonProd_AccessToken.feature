Feature: Claim360 API Access Token Generation
  Background:
    * configure ssl = true
    * def cr = claim360_cr_nonprod
    * def cs = claim360_cs_nonprod
    * def token_url = claim360_token_url_nonprod
  Scenario: Using Non-Prod Client and SecretKey For Claim360 Access Token
    Given url token_url
    And header Content-Type = "application/x-www-form-urlencoded"
    And form field client_id = cr
    And form field client_secret = cs
    And form field grant_type = "client_credentials"
    When method post
    Then status 200
    And response.access_token != null
    * def accessToken = 'Bearer ' + response.access_token
    * def ltpaToken = responseCookies.LtpaToken2 != null ? responseCookies.LtpaToken2.value : ''

