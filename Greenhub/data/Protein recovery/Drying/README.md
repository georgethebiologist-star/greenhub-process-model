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
- drying_energy_literature_benchmarks.csv (reference-only cross-technology evidence)
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

## Energy evidence and activation

`drying_energy_literature_benchmarks.csv` consolidates reported spray-drying
energy envelopes, a freeze/sublimation literature range, and grass/wheatgrass
biorefinery energy benchmarks. It keeps each source's own basis (per kg water,
per kg powder, or per Mg dry feed) and is strictly reference-only. In particular,
the reported grass-clover pilot heat per dry-feed mass is not converted into a
per-water dryer efficiency because the matched evaporation mass and dryer
boundary are not supplied. Likewise, generic freeze-drying ranges do not provide
a GreenHub freeze-drying scalar. The optional freeze-drying proxy therefore
reports an energy blocker instead of using the former unsupported 1.50 kWh/kg
water fallback. Existing spray-drying legacy proxy values and default behavior
are unchanged.

## Phase 4 product-quality comparator

`perennial_ryegrass_green_protein_concentrate_quality_ravindran_2021_reference.csv`
records 15 reported values and process statements from Ravindran et al. (2021),
DOI `10.3390/cleantechnol3030039` (CC BY 4.0). It includes Table 6
feed-basis protein, fibre and amino-acid comparison values, Results 3.1
proximate analysis, the approximate 90% DM belt-dried endpoint, gross energy,
and the textual protein partition around pressing. Results 3.1 does not state a
clear dry-matter versus as-received basis for its percentages, and process
details are proprietary. Ranges remain ranges; no midpoint, missing basis, or
balance closure is inferred. This cultivated-ryegrass comparator remains
`reference_only`, with no runtime mapping, default, dryer-energy input, or
product-price eligibility.
