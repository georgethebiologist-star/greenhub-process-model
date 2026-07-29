# GreenHub PSA biogas-upgrading literature dataset

This directory is an independent technology suite. It is not merged with the other upgrading technologies.

## Data policy
Only directly stated, tabulated, source-fitted, manufacturer-reported, or unambiguously converted numerical values are populated. Missing values are blank and use `data_status=missing`. Source optimization bounds use `data_status=assumption`; they are not GreenHub defaults.

## Integration
- Use `dataset_manifest.csv` for file discovery.
- Use `source_register.csv` for provenance.
- Use `equation_registry.csv` for symbolic and Python-style equations.
- Use `scenario_controller.csv` only as sourced scenario endpoints.
- Gate unavailable inputs through `limitation_and_missing_data_register.csv`.

## Limitations
Cost figures are old-source euros and must retain their original cost year until a documented cost-index conversion is performed. Graph-only cost curves were not digitized. Pilot or material-test data must not be represented as universal industrial performance. All transferability fields must be checked before use in the GreenHub model.

## Validation
All CSVs are comma-separated, UTF-8 encoded, contain unique IDs, and use one parameter or observation per row.
