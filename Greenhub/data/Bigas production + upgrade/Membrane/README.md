# GreenHub Membrane biogas-upgrading literature dataset

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

`variable_methane_feed_membrane_upgrading_energy_slip_buivydas_2024_reference.csv` preserves Table 1–2 measured means and reported deviations from four 35 Nm³/h membrane-upgrader inlet cases (50–80% methane). It is reference-only. The inlet is blended using upgraded-gas recycle, so this flow is not net raw digester gas. Methane slip was actively controlled at the reported 0.5% of inlet methane; the table's `% vol` label is preserved and the denominator ambiguity flagged. The deviation statistic and normal-volume reference conditions are not specified in the tables. This evidence is not a generic scale-up curve or a GreenHub runtime value.

Source: Buivydas, Navickas and Venslauskas (2024), DOI [10.3390/su16083323](https://doi.org/10.3390/su16083323); [open article](https://www.mdpi.com/2071-1050/16/8/3323).
