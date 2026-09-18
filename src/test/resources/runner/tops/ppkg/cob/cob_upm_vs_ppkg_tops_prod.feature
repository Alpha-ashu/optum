Feature: COB API - UPM vs PPKG Physician & Hospital Claim Details [TOPS] [PROD]

  Background:
    # Base response folders
    * def ppkgPhysicianBase = 'target/All_Responses/TOPS/PPKG_Responses/Physician'
    * def upmPhysicianBase = 'target/All_Responses/TOPS/UPM_Responses/Physician'
    * def ppkgHospitalBase = 'target/All_Responses/TOPS/PPKG_Responses/Hospital'
    * def upmHospitalBase = 'target/All_Responses/TOPS/UPM_Responses/Hospital'

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

    # Helper: run validation and generate reports (Physician + Hospital combined)
    * def runValidation =
    """
    function(varName) {
      karate.log('[VALIDATION] === Generating reports for:', varName, '===');
      try {
        var result = karate.exec('python src/test/utility/ppkg/cob_compare.py');
        karate.log('[VALIDATION] cob_compare.py completed:', result);
      } catch(e) { karate.log('[VALIDATION] cob_compare.py error:', e.message); }
      try {
        karate.exec('python src/test/utility/performance/generate_performance_report.py');
        karate.log('[VALIDATION] Performance report generated for', varName);
      } catch(e) { karate.log('[VALIDATION] performance report error:', e.message); }
      karate.log('[VALIDATION] === Done for:', varName, '===');
    }
    """
  Scenario: 1. COB - Collect Hospital Responses [TOPS] [PROD]
    * print('******************** [COB HOSPITAL] [UPM vs PPKG] [TOPS] [PROD] [STARTED] ********************')

    # --- Clean stale responses ---
    * eval cleanResponseFolder(ppkgHospitalBase)
    * eval cleanResponseFolder(upmHospitalBase)
    * print('******************** [CLEANUP] Hospital response folders cleared ********************')

    # --- Collect PPKG Hospital Responses ---
    * print('******************** [COB PPKG HOSPITAL] [STARTED] ********************')
    * def calloncePpkgHospital = callonce read('classpath:feature_files/upm_ppkg/tops/cob/hospital/ppkg_hospital.feature')
    * print('******************** [COB PPKG HOSPITAL] [COMPLETED] ********************')

    # --- Collect UPM Hospital Responses ---
    * print('******************** [COB UPM HOSPITAL] [STARTED] ********************')
    * def callonceUpmHospital = callonce read('classpath:feature_files/upm_ppkg/tops/cob/hospital/upm_hospital.feature')
    * print('******************** [COB UPM HOSPITAL] [COMPLETED] ********************')

    * print('******************** [COB HOSPITAL] [UPM vs PPKG] [TOPS] [PROD] [COMPLETED] ********************')
  Scenario: 2. COB - Collect Physician Responses [TOPS] [PROD]
    * print('******************** [COB PHYSICIAN] [UPM vs PPKG] [TOPS] [PROD] [STARTED] ********************')

    # --- Clean stale responses ---
    * eval cleanResponseFolder(ppkgPhysicianBase)
    * eval cleanResponseFolder(upmPhysicianBase)
    * print('******************** [CLEANUP] Physician response folders cleared ********************')

    # --- Collect PPKG Physician Responses ---
    * print('******************** [COB PPKG PHYSICIAN] [STARTED] ********************')
    * def calloncePpkgPhysician = callonce read('classpath:feature_files/upm_ppkg/tops/cob/physician/ppkg_physician.feature')
    * print('******************** [COB PPKG PHYSICIAN] [COMPLETED] ********************')

    # --- Collect UPM Physician Responses ---
    * print('******************** [COB UPM PHYSICIAN] [STARTED] ********************')
    * def callonceUpmPhysician = callonce read('classpath:feature_files/upm_ppkg/tops/cob/physician/upm_physician.feature')
    * print('******************** [COB UPM PHYSICIAN] [COMPLETED] ********************')

    * print('******************** [COB PHYSICIAN] [UPM vs PPKG] [TOPS] [PROD] [COMPLETED] ********************')
  Scenario: 3. COB - Validate & Generate Comparison Reports (Physician + Hospital)
    * print('******************** [PYTHON VALIDATION - PHYSICIAN & HOSPITAL] [STARTED] ********************')
    * def Var = 'Physician_Hospital'
    # --- Validation and Report Generation ---
    * eval runValidation(Var)
    * print('******************** [PYTHON VALIDATION - PHYSICIAN & HOSPITAL] [COMPLETED] ********************')
    * print('[DONE] Scenario completed, validated, and cleaned:', Var)
