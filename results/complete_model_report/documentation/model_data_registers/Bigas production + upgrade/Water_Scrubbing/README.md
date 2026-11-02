# GreenHub Water-Scrubbing Biogas Upgrading Literature Dataset

## Scope
Source-traceable inputs for a BioSTEAM water-scrubbing upgrading model, including absorber operation, equilibrium, geometry, packing, water loop, CO2/CH4/H2S behavior, flash recovery, regeneration, recycle, methane slip, energy, equipment, cost-data gaps, equations, and scenario endpoints.

## Evidence policy
Only directly stated or tabulated numerical values, source-calculated values, and official database values are populated. Missing fields are blank, never zero. Values read only from plots were not digitized. Source assumptions are labeled; no new engineering assumptions were inserted.

## Common schema
Most process CSVs use one observation or parameter per row. `value` and `unit` preserve the source form. `normalized_si_value` is populated only for unambiguous conversions. Operating pressure, temperature, liquid-to-gas ratio, packing, stages, recovery, and product-quality fields are present on every observation; absent source information remains blank.

## Important limitations
- Commercial CAPEX information in SGC Rapport 2013:270 is presented graphically. It is registered as missing rather than digitized.
- A validated H2S–water equilibrium sub-dataset remains missing.
- Exact packing properties such as void fraction and specific area require manufacturer sheets for the exact packing grades.
- Product quality and methane recovery are not interchangeable. Several sources report CH4 enrichment or outlet purity but not methane recovery.
- The low-pressure experimental paper reports a CO2-removal equation whose printed sign appears inconsistent with removal; the exact equation is preserved and flagged.
- NIST Henry constants are for dilute gases in pure water. Ionic chemistry, salts, pH, and high-pressure non-ideality require separate validation.

## Integration
Use `dataset_manifest.csv` for discovery, `source_register.csv` for provenance, `equation_registry.csv` for symbolic and Python-style equations, and `assumption_and_missing_data_register.csv` to gate scenarios that lack defensible inputs. Numerical IDs are unique across the package.

## Validation performed
- CSV delimiter and UTF-8 encoding checked.
- Required observation columns checked.
- Unique parameter/equation/register IDs checked.
- Blank missing values checked against `data_status=missing`.
- No formulas or multiple numeric values were placed in numeric `value` cells.
