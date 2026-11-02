# Feedstock Proxy Supersession

## Primary Source

`roadside_grass_composition_scientific.csv` is the primary roadside grass proxy source for safe canonical fields with direct numeric SI values.

## Superseded Old Fields

These older Czubaszek/Wrobel variables are superseded when resolving active proxy values because the new CSV has a direct roadside row for the same canonical field:

- `feed_volatile_solids_dry` -> `fresh_volatile_matter`
- `feed_ash_dm` -> `fresh_ash`
- `feed_total_organic_carbon_dm` -> `fresh_carbon`
- `feed_total_kjeldahl_nitrogen_dm` -> `fresh_nitrogen`
- `feed_sulfur_dm` -> `fresh_sulfur`

## Fallback-Only Old Fields

These older variables remain fallback-only because no direct numeric primary row is currently loaded for the same canonical proxy field:

- `feed_total_solids_wb`
- `feed_moisture_wb`, only if `road_verge_moisture_as_received` is absent or unusable
- `feed_bulk_density`, only if `bulk_density` is absent or unusable

## Primary Fields Loaded Directly

- `road_verge_moisture_as_received` as moisture/as-received
- `fresh_volatile_matter` as volatile solids/volatile matter
- `fresh_ash`
- `fresh_carbon`
- `fresh_hydrogen`
- `fresh_oxygen`
- `fresh_nitrogen`
- `fresh_sulfur`
- `fresh_cn_ratio`
- `bulk_density`
- `protein` as total protein only
- `extractive_sugars` as extractive sugars only

## Reference-Only Fields

- `fresh_bmp_buswell`
- `fresh_bmp_boyle`
- indirect grass-juice rows such as glucose, fructose, sucrose, ions, and COD-related measurement targets

## Still Blocked

Missing rows remain blocked and are not loaded as active proxy values:

- soluble protein
- insoluble protein
- true protein
- soluble sugars as a process-release value
- lipids
- COD and BOD fractions
- liquid density, viscosity, EC, alkalinity, TAN, NH4, NO3, P, K, VFA species
- cellulose, hemicellulose, lignin, NDF, ADF, WSC, starch, amino-acid profile
- particle-size distribution and other physical-property rows marked missing

No old CSV rows were deleted.
