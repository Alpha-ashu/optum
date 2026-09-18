@ignore
Feature: Reusable single HTTP GET (no retry, no assertions)

  # Called with two variables:
  #   reqUrl     -> the full request URL (string)
  #   reqHeaders -> a map of header name/value pairs
  # Returns the raw response, responseStatus and responseTime to the caller
  # WITHOUT asserting anything, so the caller can decide what to do next.

  Scenario:
    * url reqUrl
    * headers reqHeaders
    * method get

