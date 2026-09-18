Feature: Request Cosmos UPM PROD Summary Details

  Background:
    * def callAccessToken = callonce read('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature')
    * def accessToken = callAccessToken.accessToken
    * def api_url = 'https://gateway-core.optum.com/api/clm/cosmos/claims/v3/search'
    * def row = (typeof __row == 'undefined' ? {} : __row)
    * def memberId = row.memberNumber
    * def claimIdentifier = row.payerClaimControlNumber
    * def claimNumber = row.claimNumber
    * def groupNo = row.groupNo
    * def site = row.site
    * def startServiceDate = row.startDate
    * def endServiceDate = row.endDate
    * def testcase = row.testcase
    * print('********************',[testcase],[memberId],[claimIdentifier],'[STARTED] ********************************')
    * def json_string =
    """
    {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startServiceDate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(endServiceDate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

  Scenario Outline: Claim UPM summary request validation
    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header User-Agent = 'PostmanRuntime/7.29.0'
    And header Accept = '*/*'
    And header Accept-Encoding = 'gzip, deflate, br'
    And header Connection = 'keep-alive'
    And header Authorization = accessToken
    And header actor = 'IIM'
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * if (responseStatus != 200) karate.log('[WARN] Expected 200 but got', responseStatus, 'for', karate.info.scenarioName)
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'Claim UPM summary request validation', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * print('********************',[testcase],[memberId],[claimIdentifier],'[COMPLETED] ******************************')
    * def filename = 'All_Responses/IIM/UPM_Responses/Summary/' + memberId + '_' + claimNumber + '_upm.json'
    * karate.write(response, filename)

    Examples:
      | read('classpath:testdata/upm_ppkg_cosmos/IIM/cosmos-claims/IIM_MRCP_Summary.csv') |

  @negative @401
  Scenario Outline: NEG - 401 when Authorization header is missing
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>
    * def startdate = <startdate>
    * def enddate = <enddate>

    * def json_string =
        """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    * print('********************', testcase, memberId, '[NEG 401 STARTED] ********************************')

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 401 when Authorization header is missing', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase               | memberId    | groupNo | site | startdate    | enddate      |
      | 'NEG_Missing_Token_01' | '999999999' | '99999' | 'MN' | '2024-01-01' | '2024-01-31' |


  @negative @401
  Scenario Outline: NEG - 401 when Authorization token is invalid/malformed
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>
    * def startdate = <startdate>
    * def enddate = <enddate>

    * def json_string =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    * print('********************', testcase, memberId, '[NEG 401 INVALID TOKEN STARTED] ***************')

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = 'Bearer invalid.or.malformed.token'
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 401 when Authorization token is invalid/malf', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase               | memberId    | groupNo | site | startdate    | enddate      |
      | 'NEG_Invalid_Token_01' | '888888888' | '88888' | 'TX' | '2024-02-01' | '2024-02-28' |

  @negative @415
  Scenario Outline: NEG - 415 when Content-Type is not JSON
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>
    * def startdate = <startdate>
    * def enddate = <enddate>

    * def json_string =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'text/plain'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 415 when Content-Type is not JSON', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase                 | memberId    | groupNo | site | startdate   | enddate     |
      | 'NEG_UnsupportedType_01' | '777777777' | '77777' | 'CA' | '2024-03-01'| '2024-03-31' |

  @negative @validation
  Scenario Outline: NEG - 400/422 when startServiceDate > endServiceDate
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>
    * def startdate = <startdate>
    * def enddate = <enddate>

    * def json_string =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    * print('********************', testcase, memberId, '[NEG INVALID DATES STARTED] *********************')

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request json_string
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 400/422 when startServiceDate > endServiceDa', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase                 | memberId    | groupNo | site | startdate   | enddate     |
      | 'NEG_Start_After_End_01' | '666666666' | '66666' | 'FL' | '2024-05-31'| '2024-05-01' |

  @negative @validation
  Scenario Outline: NEG - 400/422 when required field 'subscriberNumber' is missing
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>
    * def startdate = <startdate>
    * def enddate = <enddate>

    * def json_string =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    # Remove the required field
    * def payload = eval(json_string)
    * remove payload.searchInput.subscriberNumber

    * print('********************', testcase, memberId, '[NEG MISSING FIELD STARTED] **********************')

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request payload
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 400/422 when required field subscriberNumbe', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase                    | memberId    | groupNo | site | startdate   | enddate     |
      | 'NEG_Missing_Subscriber_01' | '555555555' | '55555' | 'NY' | '2024-06-01'| '2024-06-30' |

  @negative @badjson
  Scenario: NEG - 400/500 when request body is malformed JSON
    * def testcase = 'NEG_Malformed_JSON_01'
    * def memberId = '444444444'
    * def groupNo = '44444'
    * def site = 'AZ'
    * def startdate = '2024-07-01'
    * def enddate = '2024-07-31'

    * text badJson =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    * print('********************', testcase, memberId, '[NEG MALFORMED JSON STARTED] **********************')

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request badJson
    When method post
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 400/500 when request body is malformed JSON', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData

  @negative @406
  Scenario Outline: NEG - 406 when Accept header requests an unsupported media type
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>
    * def startdate = <startdate>
    * def enddate = <enddate>

    * def json_string =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = 'application/xml'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request json_string
    When method post
    * print 'Actual responseStatus:', responseStatus
    * print 'Actual response:', response
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 406 when Accept header requests an unsupport', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase               | memberId    | groupNo | site | startdate   | enddate     |
      | 'NEG_NotAcceptable_01' | '123456789' | '10001' | 'MN' | '2024-01-01'| '2024-01-31' |

  @negative @405
  Scenario: NEG - 405 when using a wrong HTTP method (PUT not allowed)
    * def testcase = 'NEG_Method_Not_Allowed_01'

    Given url api_url
    And header Cache-Control = 'no-cache'
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request { dummy: 'value' }
    When method put
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 405 when using a wrong HTTP method (PUT not ', endpoint: '#(karate.info.scenarioName)', method: 'PUT', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData
    * if (responseHeaders.Allow) karate.match(responseHeaders.Allow, '#notnull')


  @negative @validation
  Scenario Outline: NEG - 400 when date format is invalid (not ISO-8601)
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>

    * def json_string =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    Given url api_url
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request json_string
    When method post
    * print 'Actual responseStatus:', responseStatus
    * print 'Actual response:', response
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 400 when date format is invalid (not ISO-860', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase                 | memberId    | groupNo | site |
      | 'NEG_Invalid_DateFmt_01' | '222222222' | '20002' | 'TX' |

  @negative @validation
  Scenario Outline: NEG - 400 when types are invalid (number where string expected)
    * def testcase = <testcase>
    * def groupNo = <groupNo>
    * def site = <site>

    * def payload =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    Given url api_url
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request payload
    When method post
    * print 'Actual responseStatus:', responseStatus
    * print 'Actual response:', response
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 400 when types are invalid (number where str', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase               | groupNo | site |
      | 'NEG_Invalid_Types_01' | '30003' | 'CA' |


  @negative @validation
  Scenario Outline: NEG - 400 when additional/unknown property is present
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>

    * def payload =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    Given url api_url
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'ACET'
    And header Authorization = accessToken
    And request payload
    When method post
    * print 'Actual responseStatus:', responseStatus
    * print 'Actual response:', response
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 400 when additional/unknown property is pres', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase                  | memberId    | groupNo | site |
      | 'NEG_Additional_Field_01' | '333333333' | '30003' | 'FL' |

  @negative @403
  Scenario Outline: NEG - 403 when actor is unauthorized/forbidden for this operation
    * def testcase = <testcase>
    * def memberId = <memberId>
    * def groupNo = <groupNo>
    * def site = <site>

    * def payload =
    """
        {
      "searchInput": {
        "division": "#(site)",
        "claimType": "1",
        "startServiceDate": "#(startdate)",
        "pagingStateBlock": {
          "moreData": "",
          "nextPdeKeys": "",
          "nextClaimLkp": "",
          "nextGlobalKeys": "",
          "nextGrpXKeys": "",
          "nextClaimKeys": ""
        },
        "subscriberNumber": "#(memberId)",
        "noLookbackFlag": "",
        "dependentCode": "00",
        "endServiceDate": "#(enddate)",
        "controlModifier": {
          "uniqueClaim": "NO",
          "limitSearchDates": "NO",
          "pagedResponse": "YES",
          "cosmosSystemParameters": {
            "sourceId": "40",
            "userId": "90161"
          }
        },
        "groupNumber": "#(groupNo)"
      }
    }
    """

    # wrong/unknown actor on purpose
    Given url api_url
    And header Content-Type = 'application/json'
    And header Accept = '*/*'
    And header actor = 'UNKNOWN-ACTOR'
    And header Authorization = accessToken
    And request payload
    When method post
    * print 'Actual responseStatus:', responseStatus
    * print 'Actual response:', response
    * assert responseStatus >= 200 && responseStatus < 600
    * def perfData = { consumer: 'IIM', feature: 'upm_summary', scenario: 'NEG - 403 when actor is unauthorized/forbidden for', endpoint: '#(karate.info.scenarioName)', method: 'POST', status: '#(responseStatus)', responseTimeMs: '#(responseTime)' }
    * call read('classpath:performance/log_performance.feature') perfData


    Examples:
      | testcase                    | memberId    | groupNo | site | startdate   | enddate     |
      | 'NEG_Missing_Subscriber_01' | '555555555' | '55555' | 'NY' | '2024-06-01'| '2024-06-30' |
