# Digestate and Separation dataset suite

## Scope
Literature-backed inputs for `Greenhub/data/Resource recovery/Digestate_and_Separation/`.
The retained experimental dataset is dominated by mixed agricultural digestates that include
grass/energy crops at several plants; it is **not** a grass-only calibration dataset.

## Files
The eight requested process CSVs contain one observation or required missing parameter per row.
`dataset_manifest.csv`, `source_register.csv`, `equation_registry.csv`, and
`assumption_and_missing_data_register.csv` provide integration and provenance controls.
`reuland_digestate_composition_zenodo_v1_reference.csv` is an additional 1,884-row,
CC BY 4.0 mixed-European digestate comparator. It is explicitly reference-only; see its
sidecar for the source workbook checksum, row-level mapping, units, and transferability limits.
`ferti_dig_french_digestate_summary_caradec_2025_reference.csv` transcribes only the
published aggregate statistics for the French Ferti-Dig collection (n=608). The paper is CC BY 4.0;
the associated raw repository uses separate custom non-commercial terms, so no raw rows were copied.
This aggregate is also reference-only and is not a grass-digestate or nutrient-recovery calibration.

## Data status
Populated rows use `literature-reported`. Blank required inputs use `data_status=missing`.
No numerical assumption values were inserted. Liquid-fraction totals are not relabelled as
dissolved concentrations. Total P is never converted to orthophosphate.

## Units
Source units are preserved. SI normalization is included only when unambiguous.
A concentration in g/kg was not converted to kg/m3 unless density was known; any explanatory
approximation is explicitly excluded from the normalized numeric field.

## Integration notes
Use `python_variable` as the model-facing key and `parameter_id` as the immutable provenance key.
Filter rows by material, process, operating conditions, transferability, and data status.
Do not average across sources automatically.

## Important limitations
- Mixed feedstocks limit transferability to fresh grass or roadside-grass digestate.
- The Reuland registry has broad manure/energy-crop/biowaste categories but no grass-only
  cohort and no consistently identified separation technology; it cannot fill GreenHub-specific
  digestate composition or recovery parameters.
- Density, rheology, particle-size distribution, alkalinity, chloride, sulfate, sulfide,
  dissolved COD and dissolved/orthophosphate P remain high-priority gaps.
- The industrial separation averages in Romio et al. pool screw presses and decanter centrifuges.
- The IEA report reproduces older source tables; use it as technical-report evidence rather than
  a new experimental dataset.
- Seasonal rows are deliberately blank because monthly values must be site-specific.

## Validation
All CSVs are comma-separated UTF-8, have unique IDs within each file, and were checked for
column consistency, parseable numeric values, and populated-value source traceability.

## Fertiliser product-route reference (Phase 7)
`eu_digestate_fertiliser_regulatory_requirements_2019_1009_2026_reference.csv` stages CMC4/CMC5 digestate, CMC12 precipitated phosphate salts, PFC 1(A) organic fertiliser, PFC 1(C) inorganic fertiliser, and the current Dutch Annex Aa categories for plant-only digestate/fractions. These are screening gates only. The final product route, material listing, roadside-grass legal status, conformity assessment, assays and buyer specification are unconfirmed. Struvite may only be assessed against a relevant CMC/PFC route after source-material and product classification; PFC 1(A) limits do not apply to it by default. Regulatory criteria are not measured product values or runtime parameters.

## Clover-grass fractionation and AD nutrient-recovery summary (Phase 3–5/7)
`clover_grass_nutrient_recovery_and_ad_balance_santamaria_2020_reference.csv` complements the existing 69-row Santamaria-Fernandez et al. (2020) table extract. It records reported wet output shares and nutrient-recovery ranges, plus selected CSTR digestate values and source-described nitrogen availability. Ranges shared across crops/analytes remain grouped; source-calculated organic-matter conversion is not merged with carbon conversion; and contradictory C:N prose is retained as a quarantined record. The proof PDF's Table 2 text extraction is malformed, and narrative concentrations remain approximate. The reference is cultivated clover-grass, not roadside grass or a GreenHub mass balance; it is reference-only and does not activate parameters or fertilizer credits. Check the sidecar's external-reuse caution before redistribution.
