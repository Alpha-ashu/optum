Feature: Request Cosmos UPM PROD Access Token
  Background:
    * configure ssl = true
    * def cr = ('' + upm_cob_cr_prod).replaceAll('"', '')
    * def cs = ('' + upm_cob_cs_prod).replaceAll('"', '')
    * def token_url = upm_cob_token_url_prod
  Scenario: Using Cosmos UPM Prod Client and SecretKey to Generate Access Token
    Given url token_url
    And header Content-Type = "application/x-www-form-urlencoded"
    And form field client_id = cr
    And form field client_secret = cs
    And form field grant_type = "client_credentials"
    When method post
    Then status 200
#    * print response
    And response.access_token != null
    * def accessToken = 'Bearer ' + response.access_token
    * def ltpaToken = responseCookies.LtpaToken2 != null ? responseCookies.LtpaToken2.value : ''



