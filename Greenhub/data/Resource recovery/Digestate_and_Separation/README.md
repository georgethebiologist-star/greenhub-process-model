# Digestate and Separation dataset suite

## Scope
Literature-backed inputs for `Greenhub/data/Resource recovery/Digestate_and_Separation/`.
The retained experimental dataset is dominated by mixed agricultural digestates that include
grass/energy crops at several plants; it is **not** a grass-only calibration dataset.

## Files
The eight requested process CSVs contain one observation or required missing parameter per row.
`dataset_manifest.csv`, `source_register.csv`, `equation_registry.csv`, and
`assumption_and_missing_data_register.csv` provide integration and provenance controls.

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
- Density, rheology, particle-size distribution, alkalinity, chloride, sulfate, sulfide,
  dissolved COD and dissolved/orthophosphate P remain high-priority gaps.
- The industrial separation averages in Romio et al. pool screw presses and decanter centrifuges.
- The IEA report reproduces older source tables; use it as technical-report evidence rather than
  a new experimental dataset.
- Seasonal rows are deliberately blank because monthly values must be site-specific.

## Validation
All CSVs are comma-separated UTF-8, have unique IDs within each file, and were checked for
column consistency, parseable numeric values, and populated-value source traceability.
