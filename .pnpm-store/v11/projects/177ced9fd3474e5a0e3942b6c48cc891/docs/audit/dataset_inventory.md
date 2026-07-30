# Scientific Dataset Inventory

> Historical alpha inventory. Commit `39dcf17` replaced the flat 17-file protein suite
> with a 301-dataset harmonized package. Current activation decisions are documented in
> `docs/advanced_model/dataset_activation_matrix.md` and
> `Greenhub/data/global_audit_package/dataset_activation_matrix.csv`.

Audit date: 2026-07-29

Readiness levels: D0 discovered, D1 documented but structurally unusable, D2 schema
ready, D3 loadable and validated, D4 connected, D5 verified by tests and reports.

## Master Workbook

`Greenhub/data/greenhub_feed_inputs.xlsx` has 14 sheets: ReadMe, ModelControl,
MonthlyMass, FeedMeasurements, Parameters, GrassAvailability, GrassMeasurements,
Phase3Parameters, Phase4Parameters, AcidTitration, ProteinRecoveryData,
Phase5Parameters, Phase6Parameters, and Phase7Parameters.

Readiness: **D5**. It has loaders, type/range/quality gates, scenario/month resolution,
tests, active calculation connections, and reports. Blank cells are intentional in many
optional/provenance fields; required active blanks fail before unit construction.

Workbook backup files are archival evidence, not active datasets. Readiness: **D0** as
calculation inputs; do not load automatically.

## Protein-Recovery Dataset Suite

No existing Python code or test references any of these CSV filenames. The suite is
therefore disconnected. Documentation describes conceptual `ProductionModel` classes
and subfolders that do not exist in the active package; files are currently flat.

| Dataset | Rows | Main purpose | Required blank values | Readiness | Decision |
|---|---:|---|---:|---|---|
| `dynamic_isoelectric_protein_model_dataset.csv` | 154 | pI/solubility/kinetic/equation registry | 0 explicitly required; 50 blank values | D2 | Schema-rich, but many outputs/calibration fields and 85 missing sources require row-role validation |
| `lactic_fermentation_bacterial_strain_database.csv` | 74 | strain kinetic/physiology parameters | 0 | D2 | Literature/proxy table; 16 values absent and several `missing_prior` rows |
| `lactic_fermentation_feed_composition.csv` | 44 | fermentation feed state | 7 | D1 | Cannot build a complete feed without explicit upstream coupling values |
| `lactic_fermentation_metabolic_reaction_registry.csv` | 12 | reactions and rate forms | 0 | D2 | Equations documented, but no parser or stoichiometric validator |
| `lactic_fermentation_reactor_parameters.csv` | 42 | reactor/kinetic controls | 5 | D1 | Required parameters absent; linked protein filename does not match actual filename |
| `lactic_fermentation_scenario_controller.csv` | 7 | strain/scenario selection | n/a | D2 | Controller schema exists; several scenarios self-rate low completeness |
| `membrane_assumption_register.csv` | 10 | explicit assumptions | n/a | D2 | Useful provenance table; not a solver input alone |
| `membrane_equation_registry.csv` | 15 | fouling/flux/rejection equations | n/a | D2 | Equations documented; no parser/tests |
| `membrane_feed_state_coupling_database.csv` | 6 | upstream state modifiers | n/a | D2 | Five of six rows explicitly assumption-based |
| `membrane_module_database.csv` | 6 | module/reference values | n/a | D2 | Five rows are literature-plus-proxy; no validated GreenHub module |
| `membrane_scenario_controller.csv` | 7 | membrane route controls | n/a | D2 | One template and several low-completeness cases |
| `membrane_unit_solver_parameters.csv` | 35 | solver parameters | 6 | D1 | Required values absent; 9 assumption rows and 22 missing source titles |
| `drying_common_unit_and_feed_parameters.csv` | 32 | shared dryer/feed inputs | 12 | D1 | Required upstream/feed values absent; 31 source-title blanks |
| `drying_equation_registry.csv` | 18 | spray/freeze equations | n/a | D2 | Equation schema ready; 7 assumption rows; no parser/tests |
| `drying_scenario_controller.csv` | 5 | dryer route selection | n/a | D2 | Scenarios range from medium to low completeness |
| `freeze_drying_parameters.csv` | 43 | freeze-drying controls | 4 | D1 | Required values absent; 18 assumptions |
| `spray_drying_parameters.csv` | 37 | spray-drying controls | 3 | D1 | Required values absent; 16 assumptions |

## Cross-File Issues

1. `lactic_fermentation_reactor_parameters.csv` references
   `greenhub_dynamic_isoelectric_protein_model_dataset.csv`; the actual file is
   `dynamic_isoelectric_protein_model_dataset.csv`.
2. `status` is overloaded across files as provenance, role, maturity, or completeness.
3. Required flags are not present in every schema and are not centrally validated.
4. Unit strings have no shared normalization registry or dimensional test.
5. References are often absent for engineering priors and calculated rows.
6. No version, checksum, schema version, or loader provenance is exposed to reports.

## Integration Decision

No protein CSV is connected in this audit checkpoint. Activating PR4 or PR6 from these
files would create false precision because required inputs are blank and no validated
loader, dimensional normalization, fallback contract, or regression test exists.

Recommended next step after approval: implement read-only schema validators and typed
records first, then report dataset readiness. Do not connect calculations until the
required blanks and filename mismatch are resolved and representative physical trend
tests are agreed.
