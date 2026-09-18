Feature: COB API Access Token Generation
  Background:
    * configure ssl = true
    * def cr = COB_cr_prod
    * def cs = COB_cs_prod
    * def token_url = COB_token_url_prod
  Scenario: Using Prod Client and SecretKey For COB Access Token
    Given url token_url
    And header Content-Type = "application/x-www-form-urlencoded"
    And form field client_id = cr
    And form field client_secret = cs
    And form field grant_type = "client_credentials"
    And form field scope = "https://api.uhg.com/.default"
    When method post
    Then status 200
    And response.access_token != null
    * def accessToken = 'Bearer ' + response.access_token

