# GreenHub Water-Scrubbing Biogas Upgrading Literature Dataset

## Scope
Source-traceable inputs for a BioSTEAM water-scrubbing upgrading model, including absorber operation, equilibrium, geometry, packing, water loop, CO2/CH4/H2S behavior, flash recovery, regeneration, recycle, methane slip, energy, equipment, cost-data gaps, equations, and scenario endpoints.

## Evidence policy
Only directly stated or tabulated numerical values, source-calculated values, and official database values are populated. Missing fields are blank, never zero. Values read only from plots were not digitized. Source assumptions are labeled; no new engineering assumptions were inserted.

## Common schema
Most process CSVs use one observation or parameter per row. `value` and `unit` preserve the source form. `normalized_si_value` is populated only for unambiguous conversions. Operating pressure, temperature, liquid-to-gas ratio, packing, stages, recovery, and product-quality fields are present on every observation; absent source information remains blank.

## Important limitations
- Commercial CAPEX information in SGC Rapport 2013:270 is presented graphically. It is registered as missing rather than digitized.
- A literature-backed dilute pure-water H2S solubility temperature response is now available and connected to A611 in BG2 literature-default mode. It does not resolve the H2S reference absorption fraction, pH/speciation, electrolyte effects, high-pressure non-ideality, or packed-column transfer coefficients.
- Exact packing properties such as void fraction and specific area require manufacturer sheets for the exact packing grades.
- Product quality and methane recovery are not interchangeable. Several sources report CH4 enrichment or outlet purity but not methane recovery.
- The low-pressure experimental paper reports a CO2-removal equation whose printed sign appears inconsistent with removal; the exact equation is preserved and flagged.
- NIST Henry constants are for dilute gases in pure water. Ionic chemistry, salts, pH, and high-pressure non-ideality require separate validation.

## H2S temperature response activation
`h2s_temperature_parameter.csv` records the piecewise IUPAC-evaluated Clarke & Glew fits for H2S mole-fraction solubility in water: `ln(x)=A_low+B_low/T` from 273.2–283.2 K and `ln(x)=A_high+B_high/T+C_high ln(T)+D_high*T` from 283.2–603.2 K. The relative response is the exact source-fit ratio `x(T)/x(Tref)`; temperatures are in kelvin. All nine fit coefficients/bounds are registered as quality B / D4 and are selected only for BG2 `literature_default` or `expert_override` calculations. They modify the temperature response of the existing Level-1 apparent H2S absorption fraction; they do not replace that structural calibration or make water scrubbing a stage model. In structural mode, the previous empirical temperature response remains unchanged.

## Integration
Use `dataset_manifest.csv` for discovery, `source_register.csv` for provenance, `equation_registry.csv` for symbolic and Python-style equations, and `assumption_and_missing_data_register.csv` to gate scenarios that lack defensible inputs. Numerical IDs are unique across the package.

## Farm-scale vacuum-scrubber electricity observations
`wantz_2023_hpsw_experiment_energy_points_reference.csv` records the source-stated operating context and approximate electricity measurements for two farm prototype tests (Experiments 31 and 35). The manuscript reports a two-hour electricity-meter measurement, approximate electrical demands of 25 and 16.6 kW, and approximately 0.8 kWh per Nm3 raw biogas for each point. These values are configuration-specific and are not GreenHub defaults. The public author-uploaded preprint did not identify an explicit reuse license; the PDF is not included and external redistribution requires a rights review.

## Validation performed
- CSV delimiter and UTF-8 encoding checked.
- Required observation columns checked.
- Unique parameter/equation/register IDs checked.
- Blank missing values checked against `data_status=missing`.
- No formulas or multiple numeric values were placed in numeric `value` cells.
