# GreenHub PT0 Feed and Baseline dataset suite

Target path: `Greenhub/data/Pre-treatment/Feed_and_Baseline/`

This suite contains source-traceable observations for untreated green biomass and the PT0 no-pretreatment case.

## Rules
- One observation per row.
- Source units are preserved; SI-normalized values are only supplied for unambiguous conversions.
- Missing values remain blank and use `data_status=missing`.
- Proxy meadow data are explicitly labelled and must not be treated as roadside-grass defaults.
- Source-fitted equations are not universal laws and must not be extrapolated.

## Files
`pretreatment_feed_composition.csv`, `pretreatment_feed_physical_properties.csv`,
`seasonal_feed_variability.csv`, `no_pretreatment_baseline.csv`,
`source_register.csv`, `equation_registry.csv`,
`assumption_and_missing_data_register.csv`, `optional_calculated_summary.csv`,
and `dataset_manifest.csv`.

## Integration readiness
The schemas and identifiers are ready for ingestion and provenance checks. The package is not yet fully parameterized because direct grass-juice physical properties, soluble/insoluble protein, sugars, COD, untreated pressing yield, untreated release, cell-disintegration index, and PT0 energy demand remain unresolved.

## Limitations
Roadside-grass composition comes from one seasonal experimental study. Structural carbohydrate data use a managed meadow proxy. No graph values were digitized; only equations printed by the source were transcribed. “Immediate” processing from the DCA report is retained without inventing a numeric storage limit.
