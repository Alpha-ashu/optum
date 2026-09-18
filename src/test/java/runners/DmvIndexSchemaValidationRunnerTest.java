package runners;

import com.intuit.karate.junit5.Karate;

/**
 * JUnit 5 entry point for the DMV Index Schema Validation runner.
 *
 * Running this class executes the Karate runner feature
 *   src/test/resources/runner/dmv/dmv_index_schema_validation.feature
 * which runs a single generic scenario that invokes
 *   python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py --all
 * (via karate.exec) so EVERY consumer registered in
 * feature_config.CONSUMER_CONFIG (or auto-discovered from
 * validation_config/&lt;Name&gt;/config.json) is validated automatically and its
 * Excel report - including the additive "Run Information" / "Validation
 * Summary" sheets - is generated, without the runner ever hardcoding a
 * consumer name. To onboard a new consumer, only feature_config.py (or a new
 * validation_config/ entry) changes - the runner, validation engine,
 * hardcoded-override layer and reporting layer are never edited.
 *
 * HOW TO RUN
 * ──────────
 * IntelliJ : click the green ▶ next to the method (JUnit) — no Karate plugin
 *            required. Put env in Run Config → "VM options": -Dkarate.env=qae
 * Terminal : mvn test -Dtest=DmvIndexSchemaValidationRunnerTest -Dkarate.env=qae
 *
 * Prerequisite for the auto-report step: `python` must be on PATH and the
 * packages in requirements.txt (pandas, openpyxl) installed —
 *   pip install -r requirements.txt
 */
class DmvIndexSchemaValidationRunnerTest {

    @Karate.Test
    Karate dmvIndexSchemaValidation() {
        return Karate.run(
                "classpath:runner/dmv/dmv_index_schema_validation.feature"
        );
    }
}

