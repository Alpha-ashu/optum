***

# **ppkg-claims-dark-mode-validator**

This repository contains **UHG UPM and PayerPackage API (upm\_ppkg)** automation framework based on the **Karate Framework**, designed for **Dark Mode Validation (DMV)** in claims flows.

!karate logo

***

## **Purpose**

The goal of this project is to create robust API testing features using **Karate** for execution and **Python** for advanced validations and reporting. It validates cross-system data (UPM vs. PPKG) and generates business-friendly reports.

***

## **Architecture Overview**

*   **Execution Layer (Karate):**  
    BDD feature files for API calls, schema validation, and response persistence. Managed via **Maven/JUnit**.
*   **Validation Layer (Python):**  
    Post-run scripts for transforming, mapping, and comparing multi-source responses; generates Excel reports.
*   **Configuration/Data Layer:**  
    Environment configs in `karate-config.js`; test data under `src/test/resources/testdata`.
*   **Reporting Layer:**  
    Karate HTML reports + custom Excel validation reports.

**High-level flow:**  
IntelliJ VM Options → Karate executes `.feature` tests → Responses saved → Python scripts validate → Excel report generated.

***

## **Technology Stack**

*   **API Testing:** Karate (JVM/BDD)
*   **Languages:** Java, JavaScript (Karate config), Python (validation/reporting)
*   **Build:** Apache Maven
*   **CI/CD:** Jenkins
*   **Reports:** Karate HTML + Custom Excel Report via Python

***

## **Project Structure**

    ppkg-claims-dark-mode-validator/
    ├─ pom.xml
    ├─ Jenkinsfile
    ├─ Dockerfile
    ├─ requirements.txt          # Python dependencies
    ├─ docs/
    │  ├─ NAMING_CONVENTIONS.md   # Framework naming & organization standard
    │  └─ REFACTOR_LOG.md         # Staged standardization progress
    ├─ src/
    │  └─ test/
    │     ├─ java/               # JUnit runners (runners/), karate-config.js
    │     ├─ resources/
    │     │  ├─ authorization_token/   # OAuth token features (prod / nonprod)
    │     │  ├─ feature_files/         # API/GraphQL call features (by system)
    │     │  ├─ performance/           # log_performance.feature
    │     │  ├─ runner/                # Orchestrator features (entry points)
    │     │  └─ testdata/              # CSV / GraphQL / JSON inputs
    │     └─ utility/            # Python validation & reporting
    │        ├─ alex_validation/
    │        ├─ DMV_Index_Schema_Validation/
    │        ├─ ppkg/
    │        ├─ upm_ppkg_validation/
    │        ├─ performance/
    │        └─ validation_mapping/    # Excel field-mapping workbooks
    └─ target/
       ├─ karate-reports/
       ├─ Performance/                 # performance_log.csv + Excel report
       └─ All_Responses/
          └─ <CONSUMER>/               # e.g. IIM, ISET, ACET …
             ├─ UPM_Responses/
             ├─ PPKG_Responses/
             ├─ ALEX_Responses/
             └─ HCP_Responses/

> **Naming & organization standards:** see
> [`docs/NAMING_CONVENTIONS.md`](docs/NAMING_CONVENTIONS.md). Migration progress
> is tracked in [`docs/REFACTOR_LOG.md`](docs/REFACTOR_LOG.md).

***

## **Prerequisites**

*   **Java:** 8 or higher (tested with Java 8)
*   **Maven:** 3.8+
*   **Python:** 3.8+
*   **Git**
*   Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

***

## **Setup & Installation**

```bash
# Clone Main Branch 
git clone https://github.com/uhc-tech-benefit-ops/ppkg-claims-dark-mode-validator.git

# Or Forked Branch
git clone https://github.com/sashra19_uhg/ppkg-claims-dark-mode-validator.git

cd ppkg-claims-dark-mode-validator
mvn clean install
```

Configure environment tokens/URLs in `karate-config.js` and `authorization_token/<env>/`.

***

## **How to Run**

### **Maven**

Run all tests:

```bash
  mvn test
```
Run by runner:

```bash
mvn test -Dtest=MyTestRunner -Dkarate.env=nonprod
```

***

### **IntelliJ VM Options**

#### **Prod**

```bash
-Dkarate.env=prod \
-Dupm_gateway_oauth_client_id_prod="$gateway_oauth_client_id" \
-Dupm_gateway_oauth_client_secret_prod="$gateway_oauth_client_secret" \
-Dppkg_gateway_oauth_client_id_prod="$gateway_oauth_client_id" \
-Dppkg_gateway_oauth_client_secret_prod="$gateway_oauth_client_secret"
```

#### **Non-Prod**

```bash
-Dkarate.env=nonprod \
-Dupm_gateway_oauth_client_id_nonprod="$gateway_oauth_client_id" \
-Dupm_gateway_oauth_client_secret_nonprod="$gateway_oauth_client_secret" \
-Dppkg_gateway_oauth_client_id_nonprod="$gateway_oauth_client_id" \
-Dppkg_gateway_oauth_client_secret_nonprod="$gateway_oauth_client_secret"
```

#### **Mixed (Prod & Non-Prod)**

```bash
-Dkarate.env=nonprod
-Dupm_env=prod
-Dppkg_env=nonprod
-Dupm_gateway_oauth_client_id_prod="$gateway_oauth_client_id"
-Dupm_gateway_oauth_client_secret_prod="$gateway_oauth_client_secret"
-Dppkg_gateway_oauth_client_id_nonprod="$gateway_oauth_client_id"
-Dppkg_gateway_oauth_client_secret_nonprod="$gateway_oauth_client_secret"
```

***

## **Reporting**

*   **Karate HTML:** `target/karate-reports/karate-summary.html`
*   **Custom Excel validation report (Python):**
    `target/All_Responses/<CONSUMER>/…_validated_report.xlsx`
*   **Performance Excel report (Python):**
    `target/All_Responses/<CONSUMER>/<Type>_Performance_Report.xlsx`

***

## **Notes**

*   Docker configuration is **not fully tested yet**.
*   Do **not** commit tokens; use IntelliJ VM options or secure stores.

***
