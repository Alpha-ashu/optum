Feature: DMV Index Schema Validation - PPKG vs Alex (IIM / Cosmos) claim details


  Scenario: DMV Index Schema Validation - all registered consumers
    # Generic, config-driven: NO consumer names are hardcoded here. Every
    # consumer registered in feature_config.CONSUMER_CONFIG (or auto-discovered
    # from validation_config/<Name>/config.json) runs automatically. Adding a
    # new consumer NEVER requires touching this runner file - only
    # feature_config.py (or a new validation_config/ entry) changes.
    * print('******************** [DMV INDEX SCHEMA VALIDATION] [ALL CONSUMERS] [STARTED] **************************')
    * def result = karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py --all')
    * print('[DONE] All registered DMV consumers validated. Output:', result)

