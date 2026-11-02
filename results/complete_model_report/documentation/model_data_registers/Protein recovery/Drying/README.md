# GreenHub Drying Dataset Audit and Extension

## Scope
Ready-to-use CSV datasets for spray drying and freeze drying of grass protein, leaf protein, plant-protein concentrates, fermentation-derived protein solids, and explicitly labelled proxy protein products.

## Required files
- spray_drying_observations.csv
- spray_drying_parameters.csv
- freeze_drying_observations.csv
- freeze_drying_parameters.csv
- drying_thermal_properties.csv
- drying_quality_response.csv
- drying_equation_registry.csv
- drying_scenario_controller.csv

Supporting files:
- source_register.csv
- assumption_and_missing_data_register.csv
- dataset_manifest.csv
- validation_report.json
- UNRESOLVED_MANDATORY_INPUTS.md

## Evidence policy
Every populated numerical value includes a source, basis, material class, proxy classification, and transferability explanation. Missing grass-specific values remain blank. No milk-powder, whey-protein, BSA, enzyme, or pharmaceutical formulation value is treated as direct grass-protein performance.

## Key audit changes
The legacy GreenHub drying package contained useful mechanistic equations but also scenario values for feed solids, temperatures, droplet distributions, cyclone efficiency, wall losses, sorption, collapse temperature, cake resistance and protein stability. These are now either:
- direct observations;
- plant-protein proxies;
- dairy/pharmaceutical/animal-protein proxies;
- fundamental equations;
- or blank mandatory calibration inputs.

## Data loading rules
1. Load direct grass data before all proxies.
2. Proxy rows require explicit scenario permission.
3. Inlet air temperature is not product temperature.
4. Freeze-drying equations may be transferable while pharmaceutical numerical parameters are not.
5. Keep each experimental run or sampling time as a separate observation row.
6. Do not fit missing quality, drying or cost parameters unless explicitly requested.
