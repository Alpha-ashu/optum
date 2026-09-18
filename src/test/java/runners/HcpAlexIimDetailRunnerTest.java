package runners;

import com.intuit.karate.junit5.Karate;

/**
 * JUnit 5 entry point for the HCP vs Alex (IIM / Cosmos) validation runner.
 *
 * Running this class executes the Karate runner feature
 *   src/test/resources/runner/cosmos/alex/hcp_alex_api/IIM/ppkg_dev_alex_qae_cosmos_IIM_detail_summary.feature
 * which, for each scenario (Physician / Hospital / Summary, DEV vs QAE, plus
 * Physician PROD vs QAE), collects the API responses and then calls
 *   python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py <Var>
 * (via karate.exec inside runValidation()) so the Excel validation report is
 * generated automatically the moment each scenario finishes. Consumer name,
 * source/target feature files, endpoints and environments are all read from
 * feature_config.CONSUMER_CONFIG - nothing is hardcoded in the validation or
 * reporting layer; onboarding a new scenario only means adding a
 * CONSUMER_CONFIG entry + a Karate scenario that sets `Var` and calls
 * runValidation(Var).
 *
 * HOW TO RUN
 * ──────────
 * IntelliJ : click the green ▶ next to the method (JUnit) — no Karate plugin
 *            required. Put env in Run Config → "VM options": -Dkarate.env=qae
 * Terminal : mvn test -Dtest=HcpAlexIimDetailRunnerTest -Dkarate.env=qae
 *
 * Prerequisite for the auto-report step: `python` must be on PATH and the
 * packages in requirements.txt (pandas, openpyxl) installed —
 *   pip install -r requirements.txt
 */
class HcpAlexIimDetailRunnerTest {

    @Karate.Test
    Karate iimDetail() {
        return Karate.run(
                "classpath:runner/cosmos/alex/hcp_alex_api/IIM/ppkg_dev_alex_qae_cosmos_IIM_detail_summary.feature"
        );
    }
}

