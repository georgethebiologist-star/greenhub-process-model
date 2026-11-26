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

A directly relevant grass/maize/green-weed silage calibration paper is registered. Its fitted grass-silage rates
are now transcribed as a separate four-row reference file, `grass_silage_adm1_biernacki_2013_reference.csv`,
using Table 17, p.102 of the author's open 2014 dissertation. These are fitted estimates (not direct measurements),
and remain `reference_only`: they are not calibrated to GreenHub fresh roadside grass, press cake, or protein-route
residuals. They must not be treated as runtime defaults. The GreenHub residual-specific values remain missing.

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

## Reference-only cross-context validation data
`bmp_interlaboratory_hafner_2026_bottle_calculated_reference.csv` contains the
open study's author-calculated, bottle-level BMP values from six assay substrates
across two tests and 31 laboratories. `bmp_calc` is in mL CH4 per g substrate VS
added. It supports BMP method validation and reproducibility analysis only; it
is not a GreenHub grass-yield factor, continuous-digester yield, or runtime
default. Preserve all source records, including outliers; any screening must be
an explicit separate analysis.

## Validation
- unique IDs;
- one numeric value per cell;
- traceable source and exact location for every populated value;
- UTF-8 comma-separated files;
- no formulas stored in numeric cells;
- no unsupported grass-specific or thermophilic claims.
