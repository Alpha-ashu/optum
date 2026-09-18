@ignore
Feature: Reusable helper - logs one performance row to CSV

  Scenario:
    * def feature    = __arg.feature    || 'unknown'
    * def scenario   = __arg.scenario   || 'unknown'
    * def endpoint   = __arg.endpoint   || 'unknown'
    * def method     = __arg.method     || 'unknown'
    * def status     = __arg.status     || 0
    * def responseMs = __arg.responseTimeMs || 0
    * def consumer   = __arg.consumer   || 'unknown'
    * def timestamp  = java.time.LocalDateTime.now().toString()

    # Write to target/Performance/ folder (single CSV, all features)
    * def dir = new java.io.File('target/Performance')
    * eval dir.mkdirs()

    * def csvFile = new java.io.File(dir, 'performance_log.csv')
    * def needsHeader = !csvFile.exists() || csvFile.length() == 0

    # Escape commas and special characters in values
    * def clean =
    """
    function(val) {
      return (val + '').replace(/,/g, ' ').replace(/'/g, '').replace(/>/g, '').replace(/"/g, '');
    }
    """
    * def cleanFeature  = clean(feature)
    * def cleanScenario = clean(scenario)
    * def cleanEndpoint = clean(endpoint)
    * def cleanMethod   = clean(method)
    * def cleanConsumer = clean(consumer)

    # Build CSV lines
    * def absPath = csvFile.getAbsolutePath()
    * def header = 'consumer,feature,scenario,endpoint,method,status,response_time_ms,timestamp'
    * def row = cleanConsumer + ',' + cleanFeature + ',' + cleanScenario + ',' + cleanEndpoint + ',' + cleanMethod + ',' + status + ',' + responseMs + ',' + timestamp

    # Use cmd /c echo >>file via karate.exec - external process, no file handle retained in JVM
    * if (needsHeader) karate.exec('cmd /c echo ' + header + '>>"' + absPath + '"')
    * karate.exec('cmd /c echo ' + row + '>>"' + absPath + '"')
