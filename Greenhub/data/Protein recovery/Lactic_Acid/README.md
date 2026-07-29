# GreenHub Lactic-Acid Protein-Recovery Dataset Audit and Extension

## Scope
This package supports the `Greenhub/data/Protein recovery/Lactic_Acid/` process block. It covers starter cultures, feed composition, metabolic reactions, reactor and equipment requirements, experimental time series, protein recovery responses, scenarios, and fermentation equations.

## Required files
- `strain_database.csv`
- `feed_composition.csv`
- `metabolic_reaction_registry.csv`
- `reactor_parameters.csv`
- `fermentation_time_series.csv`
- `protein_recovery_response.csv`
- `scenario_controller.csv`
- `fermentation_equation_registry.csv`

Supporting files:
- `dataset_manifest.csv`
- `source_register.csv`
- `assumption_and_missing_data_register.csv`
- `validation_report.json`

## Evidence policy
No missing kinetic, inhibition, maintenance, decay, energy, cost, or scale constants were filled with generic values. Literature endpoints and reported ranges are retained exactly. Time-series files contain one row per actual or required sampling time; no kinetic fitting was performed.

## Key direct evidence
The most directly relevant route uses *Lactobacillus salivarius* BC 1001, selected from grass-juice-associated strains for rapid acidification. Fermented red-clover, clover-grass, alfalfa and oilseed-radish juices reached reported final pH values of 4.0–4.7 and produced concentrates containing 39–46% crude protein on a dry-matter basis. A demonstration campaign operated near 10 t fresh biomass/h, processed 444 t grass clover in four days, and produced 1 t dried protein concentrate plus 7 t protein paste.

## Integration rules
1. Never use demonstration campaign duration as fermenter residence time.
2. Never calculate protein recovery from campaign product mass without source-consistent feed protein and product dry matter.
3. Use species-level strain records only as screening records; kinetic values require a strain identifier.
4. Treat *Bacillus coagulans* at pH 6.0 as a lactic-acid-production proxy, not as a direct protein-precipitation case.
5. Keep all missing numerical fields blank.
6. The dynamic BioSTEAM unit should fail or request calibration when mandatory variables are absent.
