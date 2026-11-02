# GreenHub Anaerobic Digestion — Feed & BMP Dataset

## Scope
This package supports `Greenhub/data/Biogas production + upgrade/Anaerobic_Digestion/Feed_BMP/`.
It contains source-traceable feed characterization, biochemical fractionation, methane-yield,
inhibition-screening and digestate data for road-verge grass, grass silage, grass biorefinery
press cake and protein/FOS-depleted grass whey.

## Data rules
- Blank numerical cells are intentional and paired with `data_status=missing`.
- No missing value is replaced by zero.
- Experimental measurements, literature-reported values, source-formula calculations and
  missing data are separated through `data_status`.
- Original units and bases are preserved. SI-normalized values are included only for
  unambiguous conversions.
- The theoretical Buswell/Boyle rows are **not experimental BMP results**.
- Proxy materials are explicitly identified in `material_feed_type` and `transferability`.

## Core files
- `ad_feed_characterization.csv`: TS, VS, pH, TKN, phosphorus, sulfur and selected nutrients.
- `ad_bmp_observations.csv`: measured BMP for grass press cake/de-FOS whey, theoretical
  source-calculated values, methane fraction and kinetic time markers.
- `ad_biochemical_fractionation.csv`: crude fiber, cellulose, hemicellulose and lignin.
- `ad_inhibition_feed_data.csv`: source-specific K, Na and P plus explicit missing TAN,
  alkalinity, VFA, COD and particle-size requirements.
- `ad_digestate_characterization.csv`: available digestate ratios and explicit missing fields.
- `equation_registry.csv`: exact symbolic equations, Python expressions, units and limitations.
- `assumption_and_missing_data_register.csv`: unresolved required variables without inserted values.
- `source_register.csv` and `ad_source_register.csv`: source metadata and quality notes.
- `dataset_manifest.csv`: file inventory and row counts.

## Integration notes
Use `parameter_id` as the stable row key and `python_variable` as the proposed model mapping.
Before connecting to BioSTEAM/ADM1, select rows by:
1. exact material stream;
2. data status;
3. original basis;
4. operating conditions;
5. transferability.

Do not average across seasons, preservation methods or BMP bases without an explicit,
documented model rule. Protein, lipid, carbohydrate, inert-solids, TAN, alkalinity, VFA,
full COD fractionation and absolute digestate nutrient concentrations remain important gaps.

## Validation performed
- UTF-8 CSV encoding and comma delimiter;
- consistent required columns;
- unique primary IDs in each file;
- numeric values stored one per cell;
- no formulas or multiple numerical values in numeric cells;
- all populated numerical rows include a source ID and exact source location;
- normalized units checked for dimensional consistency;
- filenames cross-checked against the manifest.

## Important limitation
This is a high-confidence starter dataset, not an exhaustive systematic review. The included
sources were selected because they provide directly traceable tables, equations or project
laboratory results relevant to GreenHub streams. Further primary literature should be added
for protein-depleted grass liquid composition, co-digestion mixtures, inhibition thresholds,
ADM1 biochemical mapping and digestate nutrient speciation.
