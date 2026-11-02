# GreenHub Common Biogas Conditioning Dataset

Path target: `Greenhub/data/Biogas production + upgrade/Biogas_Upgrading/Common_Conditioning/`

## Contents
This package contains the ten requested process CSVs plus a manifest, source register, master equation registry, and assumption/missing-data register.

## Common parameter schema
Each populated numerical row has a unique `parameter_id`, a Python-safe variable name, source unit and SI-normalized value, basis, process, feed/material, conditions, valid range, status, full source metadata, exact source location, uncertainty, transferability, and (for specifications) country and year.

Allowed statuses used here:
`measured`, `literature-reported`, `calculated_from_source_formula`, `manufacturer-reported`, `fitted_by_source`, `assumption`, and `missing`.

## Integration rules
1. Import only rows whose status is permitted by the active GreenHub scenario.
2. Never convert blank values to zero.
3. Apply country and specification-year filters before selecting biomethane limits.
4. Treat `project_specific`, `proxy`, and `low` transferability rows as scenario-gated evidence, not universal defaults.
5. Do not use source-tool assumptions automatically. They remain explicit, even when the source provides a number.
6. Equations must be evaluated only inside their stated temperature, pressure, material, and model limitations.
7. Cost rows are not yet sufficient for a complete TEA. Current vendor quotations and scope-normalized purchase costs are still required.

## Main limitations
The strongest data coverage is for raw-gas composition, Danish 2020 gas-quality limits, pilot ammonia scrubbing, selected siloxane adsorption, process temperatures/pressures, and documented dryer capability. Media capacity and breakthrough for a selected H2S product, common particle-filtration performance, compressor efficiency/power, component-level equipment prices, consumable costs, and defensible scaling exponents remain unresolved and are left blank.

Grass-specific contaminant data are scarce in the selected sources. Generic digester, wastewater, manure-lagoon, landfill-gas, and technical-gas proxies are explicitly labelled.

## Validation performed
- UTF-8 comma-separated files;
- unique IDs within every parameter file;
- required columns present;
- blank missing values preserved;
- numerical formatting checked;
- normalized SI conversions checked for unambiguous cases;
- source IDs cross-checked against `source_register.csv`;
- country/year kept in separate fields;
- every populated numerical value linked to a source and exact location.
