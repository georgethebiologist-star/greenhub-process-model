# GreenHub PT0 Feed and Baseline dataset suite

## Dutch availability and mowing evidence

`roadside_grass_availability_evidence.csv` indexes the Dutch roadside-grass
field study by Bakker et al. (2026; DOI `10.1111/1365-2664.70289`). It records
the reported 1.1–6.5 t DM/ha range for June/late-August standing biomass across
10 roadside grasslands in 2023 and six tested mowing schedules. The biomass
range is standing biomass in plots not yet mown; it is not an annual harvest
yield, accessible-area estimate, or delivered-feed quantity. All rows are
staged literature evidence and are not connected to model defaults or the
availability calculation. The study documents one- and two-cut schedule
options, but does not establish that they are permitted or used for every
Dutch road operator. Source sections: Methods 2.2 and Figure 1.

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
