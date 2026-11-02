# GreenHub Anaerobic Digestion Kinetics Dataset

## Purpose
Ready-to-use kinetic and physicochemical inputs for:
`Greenhub/data/Biogas production + upgrade/Anaerobic_Digestion/Kinetics/`.

## Model classes
- `ADM1_standard`: canonical/default ADM1 reference parameters. These are general and are never labelled grass-specific.
- `ADM1_source_calibrated`: parameters fitted or changed against an experimental dataset.
- `non_ADM_experimental_observation`: kinetic/temperature observations that are not ADM1 constants.
- `unresolved`: required values left blank because no safely traceable numerical value was available.

## Scientific use
The package distinguishes maximum substrate uptake rate `k_m` from microbial maximum specific growth rate `mu_max`.
For ADM1, growth is calculated from uptake using COD-based biomass yield. Do not silently relabel `k_m` as `mu_max`.

The standard hydrolysis constants of 10 d^-1 are reference high-rate/default values and are generally too fast
to use uncalibrated for lignocellulosic grass solids. A cattle-slurry calibration of 0.31 d^-1 is included only
as a wet agricultural biomass proxy. It is not grass-specific.

A directly relevant grass/maize/green-weed silage calibration paper is registered, but its numerical table remains
blank because it could not be verified from a machine-readable primary table in this build. This is preferable to
inventing or transcribing uncertain values.

## Temperature
Mesophilic reference values and an experimentally validated 25–35 °C relative-rate dataset are included.
Thermophilic kinetic and Arrhenius values remain explicit gaps. No arbitrary Q10 or temperature extrapolation was used.

## Gas transfer
Henry coefficients and `kLa` are ADM1 reference parameters, not equipment-independent physical constants.
Actual `kLa` depends on reactor geometry, mixing, gas holdup, rheology and scale and should be calibrated or
derived from an explicitly sourced mass-transfer correlation.

## Integration
Filter by `model_class`, `calibration_material`, `temperature_regime`, `data_status` and `transferability`.
Use the `normalized_si_value` only when populated. Blank values must remain missing, never zero.

## Validation
- unique IDs;
- one numeric value per cell;
- traceable source and exact location for every populated value;
- UTF-8 comma-separated files;
- no formulas stored in numeric cells;
- no unsupported grass-specific or thermophilic claims.
