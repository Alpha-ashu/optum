# Validation Configs — one `config.json` per runner

Every stage-vs-de-canary (and legacy) validation the generic engine
(`Schema_Validation.py`) can run is described by a single `config.json` inside
its own folder here. Discovery is automatic: any
`validation_config/<Name>/config.json` is registered under `<Name>` (or the
config's `name`) and can be run with:

```powershell
python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py <Name>
# run every discovered + legacy validation:
python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py --all
```

Folders whose name starts with `_` (e.g. `_TEMPLATE`) are **ignored** by
discovery — use them for copy-paste starting points.

## How to add a config for a runner
1. Copy `_TEMPLATE/` to `<YourValidationName>/`.
2. Fill in **`test_data`** and **`mapping_sheets`** (you maintain these manually).
3. Set the response wiring to match what the karate feature writes:
   - `response_base` — the root folder the feature writes into.
   - `sources.<name>.folder` / `.suffix` — subfolder + filename suffix per side.
   - `identifier_column` — the CSV column used in the response filename
     `"<testcase>_<key>_<suffix>"` (e.g. `reqClmNbr`, `reqSbmtProvId`). Omit to
     use the claim-number column.
4. Point `source_feature_file` / `target_feature_file` at the two features (used
   to auto-detect the API URL + environment for the report header/name).
5. In the runner's `runValidation`, call the engine with your `<Name>`:
   ```javascript
   karate.exec('python src/test/utility/DMV_Index_Schema_Validation/Schema_Validation.py <Name>');
   ```

## Key fields
| Field | Meaning |
|-------|---------|
| `comparison_mode` | `"direct"` for same-shape source-vs-target (stage vs de-canary). Omit for the legacy PPKG-vs-Alex claim-array comparison. |
| `mapping_columns` | Header names of the source/target path columns in the mapping `.xlsx`. |
| `non_match_is_blocker` | Defaults `true` in direct mode: every non-`Match` row is a Blocker. |
| `report_name_template` | Tokens: `{source_env}` `{target_env}` `{timestamp}` `{consumer_token}` `{search_type}` `{validation_type}` `{request_type}`. |

## Multiple configs, one folder
A folder can hold either a single `config.json`, or several differently-named
`*.json` files that share the folder. **File names should describe the actual
comparison** (`<source>_<target>_<sourceEnv>_<targetEnv>_<claimType>`, e.g.
`IIM/ppkg_alex_dev_qae_summary.json`) — the CLI/registration name the runner
passes (e.g. `HCPvsAlex_Summary`) is set via the config's own `"name"` field,
so the file name and the runner's `Var` do NOT need to match. Both single- and
multi-file-per-folder layouts are discovered identically; group related
validations together when it makes sense, or give each its own folder.

## Current configs
| Runner | Config file | Registered name |
|--------|-------------|------------------|
| `cosmos/ppkg_ppkg/B2B/fln_search_decanary.feature` | `Claim360_B2B_FLN_Search/config.json` | `Claim360_B2B_FLN_Search` |
| `cosmos/ppkg_ppkg/B2B/member_search_decanary.feature` | `Claim360_B2B_Member_Search/config.json` | `Claim360_B2B_Member_Search` |
| `cosmos/alex/hcp_alex_api/IIM/ppkg_dev_alex_qae_cosmos_IIM_detail_summary.feature` (Scenario 1) | `IIM/ppkg_alex_dev_qae_summary.json` | `HCPvsAlex_Summary` |
| `cosmos/alex/hcp_alex_api/IIM/ppkg_dev_alex_qae_cosmos_IIM_detail_summary.feature` (Scenario 2) | `IIM/ppkg_alex_dev_qae_hospital.json` | `HCPvsAlex_Hospital` |
| `cosmos/alex/hcp_alex_api/IIM/ppkg_dev_alex_qae_cosmos_IIM_detail_summary.feature` (Scenario 3) | `IIM/ppkg_alex_dev_qae_physician.json` | `HCPvsAlex_Physician` |
| `cosmos/alex/hcp_alex_api/IIM/ppkg_prod_alex_qae_cosmos_IIM_detail.feature` | `IIM/ppkg_alex_prod_qae_physician.json` | `HCPvsAlex_Physician_Prod` |
| `cosmos/alex/hcp_alex_api/clink/clink_payer_vs_alex_cosmos.feature` (Scenario 1) | `Clink/clink_alex_nonprod_summary.json` | `HCPClink_Alex_Summary` |
| `cosmos/alex/hcp_alex_api/clink/clink_payer_vs_alex_cosmos.feature` (Scenario 2) | `Clink/clink_alex_nonprod_hospital.json` | `HCPClink_Alex_Hospital` |
| `cosmos/alex/hcp_alex_api/clink/clink_payer_vs_alex_cosmos.feature` (Scenario 3) | `Clink/clink_alex_nonprod_physician.json` | `HCPClink_Alex_Physician` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimAccumulators.feature` | `GQL/claimAccumulators.json` | `claimAccumulators` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimAggregates.feature` | `GQL/claimAggregates.json` | `claimAggregates` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimAmbulances.feature` | `GQL/claimAmbulances.json` | `claimAmbulances` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimExtensions.feature` | `GQL/claimExtensions.json` | `claimExtensions` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimOtherPayers.feature` | `GQL/claimOtherPayers.json` | `claimOtherPayers` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimPricings.feature` | `GQL/claimPricings.json` | `claimPricings` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimServiceAccumulators.feature` | `GQL/claimServiceAccumulators.json` | `claimServiceAccumulators` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimServiceAdjudicationGroups.feature` | `GQL/claimServiceAdjudicationGroups.json` | `claimServiceAdjudicationGroups` (mapping sheet not yet available) |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimServiceline.feature` | `GQL/claimServiceline.json` | `claimServiceline` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimServiceLineExtensions.feature` | `GQL/claimServiceLineExtensions.json` | `claimServiceLineExtensions` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimServiceOtherPayers.feature` | `GQL/claimServiceOtherPayers.json` | `claimServiceOtherPayers` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimServicePricings.feature` | `GQL/claimServicePricings.json` | `claimServicePricings` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimTransaction.feature` | `GQL/claimTransaction.json` | `claimTransaction` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimTransactionExtensionProviderStatus.feature` | `GQL/claimTransactionExtensionProviderStatus.json` | `claimTransactionExtensionProviderStatus` |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_claimTransactionProviders.feature` | `GQL/claimTransactionProviders.json` | `claimTransactionProviders` (mapping sheet not yet available) |
| `cosmos/alex/hcp_alex_gql/hcp_dev_vs_alex_qae/hcp_alex_serviceAmbulances.feature` | `GQL/serviceAmbulances.json` | `serviceAmbulances` |


