# GreenHub Literature Dataset Audit

- Audited CSV datasets: 301
- Total flagged issues: 443
- Readiness counts: {'D3': 253, 'D2': 25, 'D1': 23}
- Issue counts by type: {'equation_symbol_mismatch': 149, 'equation_required_inputs_unavailable': 149, 'conflicting_bases': 7, 'duplicate_identifier_within_dataset': 58, 'missing_direct_source': 15, 'missing_exact_source_location': 15, 'conflicting_units': 1, 'potential_cost_double_counting': 49}

## Main findings

- Readiness was assigned conservatively. No dataset was promoted to D4 or D5 in this packaging task.
- D1 indicates duplicated identifiers within a dataset or broken file references.
- D2 indicates structurally loadable datasets whose equation packages still have unresolved input or symbol gaps.
- D3 indicates datasets that are loadable at schema level, but not calculation-connected by this audit.
- Potential cost overlap flags indicate places where CAPEX-like variables appear in multiple datasets and should be reviewed before any TEA integration.

## Output package

- global_dataset_manifest.csv
- global_source_register.csv
- global_unit_registry.csv
- global_equation_registry.csv
- global_missing_data_register.csv
- global_dataset_readiness.csv
- global_variable_dictionary.csv
- global_cost_overlap_register.csv
- global_validation_issues.csv
- global_validation_summary.json
