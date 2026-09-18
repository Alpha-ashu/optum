Feature:  Claims360 B2B-EDI - Stage vs De-Canary Member Search for NON-PROD ENVIRONMENT

  Background:
    # Base response folders (both features write into the same Member_Search folder,
    # PPKG/stage responses use the _ppkg.json suffix and de-canary use _decan.json)
    * def ppkgBase = 'target/All_Responses/Claim360/B2B/Member_Search'
    * def decanBase = 'target/All_Responses/Claim360/B2B/Member_Search'

    # Helper: delete all files inside a directory (non-recursive, files only)
    * def cleanResponseFolder =
    """
    function(path) {
      var File = Java.type('java.io.File');
      var dir = new File(path);
      if (dir.exists()) {
        var files = dir.listFiles();
        if (files) {
          for (var i = 0; i < files.length; i++) {
            if (!files[i].isDirectory()) {
              files[i].delete();
            }
          }
        }
      }
    }
    """

    # Helper: run validation and generate reports for the given Var
    * def runValidation =
    """
    function(varName) {
      var consumer     = 'CLAIMS360_B2B';
      var validation   = 'Claim360_B2B_Member_Search';
      karate.log('[VALIDATION] === Generating De-Canary reports for:', validation, '(Consumer:', consumer, ') ===');
      try {
        karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py ' + validation);
        karate.log('[VALIDATION] Schema_Validation.py completed for', validation);
      } catch(e) { karate.log('[VALIDATION] Schema_Validation.py error:', e.message); }
      try {
        var features = 'b2b_member_search,b2b_member_search_decanary';
        karate.exec('python src/test/utility/performance/generate_performance_report.py --consumer-filter ' + consumer + ' --feature-filter ' + features + ' --output target/All_Responses/' + consumer + '/' + varName + '_Performance_Report.xlsx');
        karate.log('[VALIDATION] Performance report generated for', consumer);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', validation, '===');
    }
    """

  Scenario: 1. Claims360 B2B-EDI Member Search - Stage vs De-Canary
    * print('******************** [Claims360 B2B Member Search] [COSMOS] [NON-PROD] [STARTED] *********************')
    * def Var = 'Member_Search'
    * print('[CLEANUP] Response folders cleaned - fresh start for:', Var)
    * eval cleanResponseFolder(ppkgBase)
    * eval cleanResponseFolder(decanBase)
    * print('******************** [PPKG STAGE MEMBER SEARCH][STARTED] *******************************************')
    * def calloncePpkg = callonce read('classpath:feature_files/claim360-ppkg/B2B-EDI/de-canary/member_search/b2b.feature')
    * print('******************** [PPKG STAGE MEMBER SEARCH][COMPLETED] *****************************************')
    * print('******************** [DE-CANARY MEMBER SEARCH][STARTED] ******************************************')
    * def callonceDecanary = callonce read('classpath:feature_files/claim360-ppkg/B2B-EDI/de-canary/member_search/b2b_decanary.feature')
    * print('******************** [DE-CANARY MEMBER SEARCH][COMPLETED] ****************************************')
    * print('******************** [Claims360 B2B Member Search] [COSMOS] [NON-PROD] [COMPLETED] *******************')
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)
