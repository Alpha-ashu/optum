Feature: Alex API Access Token Generation
  Background:
    * configure ssl = true
    * def cr = alex_cr_nonprod
    * def cs = alex_cs_nonprod
    * def token_url = alex_token_url_nonprod
  Scenario: Using Non-Prod Client and SecretKey For upm Access Token
    Given url token_url
    And header Content-Type = "application/x-www-form-urlencoded"
    And form field client_id = cr
    And form field client_secret = cs
    And form field grant_type = "client_credentials"
    And form field scope = "https://api.uhg.com/.default"
    When method post
    Then status 200
    And response.access_token != null
    * def accessToken = 'Bearer ' +response.access_token
