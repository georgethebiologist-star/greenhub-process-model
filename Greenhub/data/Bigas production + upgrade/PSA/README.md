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

## Full-scale operating, LCA and LCCA comparator (Brandis, 2020/2021)
`kohlheb_2020_brandis_fullscale_psa_lca_reference.csv` adds a 49-row extract from Kohlheb et al. (2021 online; DOI `10.1007/s12155-020-10205-9`, CC BY 4.0). It records raw/product gas composition, nominal plant capacity, plant-wide electricity, PSA pressure levels, operator-reported methane-to-air emissions, the study's PSA upgrader life-cycle boundary and GWP, normalized hotspot contributions, and historical LCCA inputs/results.

This is a single German PSA plant using energy-crop biogas with 10–15% grass silage in the upstream digester feed, not GreenHub roadside-grass residual gas. Plant-wide power is not disaggregated by unit. The paper gives a 1.5%/95,265 Nm³/year figure-1 methane-loss label and separately uses an operator-reported 0.2%/12,194 Nm³/year methane emission-to-air value; those are preserved as distinct concepts because the source does not reconcile them and the process flow includes off-gas oxidation. The product-flow figure is not reconciled with the lifetime output calculation. Category-specific units for most Table 2 LCA indicators are unavailable in the retrieved table text, so those values remain quarantined. Cost year is unstated. Everything is reference-only; no generic PSA or GreenHub defaults are set.

## Validation
All CSVs are comma-separated, UTF-8 encoded, contain unique IDs, and use one parameter or observation per row.
