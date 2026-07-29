# GreenHub Direct Isoelectric Protein-Recovery Dataset Audit and Extension

## Scope
This package audits and extends the scientific inputs required for direct isoelectric precipitation in `Greenhub/data/Protein recovery/Isoelectric/`.

It deliberately separates direct observations from proxy-material observations, source equations, manufacturer information, model assumptions, and missing mandatory inputs. Unsupported numerical defaults from the legacy combined dataset were not carried forward as facts.

## Files
The package contains topic-specific CSV files for pI, pH and temperature solubility, ionic strength, titration and reagent demand, precipitation and aggregation kinetics, residence time, recovery, purity, losses, separation, washing, moisture, stability, and equipment/scale/cost demand. It also contains:

- `dataset_manifest.csv`
- `source_register.csv`
- `equation_registry.csv`
- `assumption_and_missing_data_register.csv`
- `validation_report.json`

## Core schema
Observation files use one parameter or observation per row and include:
`parameter_id`, `python_variable`, `value`, `unit`, normalized SI fields, basis, process, material/feed, original protein source, extraction method, operating conditions, data status, full source metadata, exact source location, notes, uncertainty, and transferability.

## Data-status rules
- `measured`: numerical observation reported from an experiment.
- `literature-reported`: numerical or categorical result explicitly reported by the source.
- `calculated_from_source_formula`: calculated only from a cited formula and cited source inputs.
- `manufacturer-reported`: manufacturer specification.
- `fitted_by_source`: fitted by the original source.
- `assumption`: model structure or required input description; numerical value remains blank.
- `missing`: unresolved input; numerical value remains blank.

## Important limitations
1. Final-powder solubility is not treated as raw green-juice equilibrium solubility.
2. Total nitrogen recovery is not automatically treated as true protein recovery.
3. Precipitation yield is not treated as solid-liquid separator capture.
4. No single pI is assigned to the complete grass-protein pool.
5. Generic cost scaling is retained only as a rule-of-thumb equation; equipment-specific costs, power and scale factors remain unresolved unless supported.
6. Kinetic and residence-time constants remain blank because no defensible grass-specific time-series dataset was located in the audited sources.
7. Proxy materials are explicitly labelled and must not be silently transferred.

## Integration readiness
The package is immediately usable as a validated evidence layer and missing-data controller. The equilibrium, dynamic, separator, reagent-demand and TEA submodels are only partially parameterized until the critical items in `assumption_and_missing_data_register.csv` are measured or sourced.

Recommended integration logic:
- Load only rows whose `data_status` is compatible with the selected scenario.
- Filter by `material_feed_type`, `protein_source`, `extraction_method`, and operating conditions.
- Do not use proxy rows unless the scenario explicitly allows proxies.
- Treat textual ranges as ranges; do not convert them to midpoints automatically.
- Fail validation when a mandatory variable has no direct value for the chosen feed class.
