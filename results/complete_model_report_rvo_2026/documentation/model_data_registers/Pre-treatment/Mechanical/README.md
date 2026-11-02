# GreenHub Mechanical Pre-treatment Dataset Suite

Path: `Greenhub/data/Pre-treatment/Mechanical/`

## Scope
This package covers PT0 no pretreatment, PT1 chopping, PT2 maceration, PT3 wet milling/refining, and PT4 high-shear homogenization before pressing or extraction. Populated experimental rows prioritize fresh grass, clover, lucerne, and mixed green biomass. Dry comminution equations are kept separate and explicitly marked as low-transferability.

## Files
- `mechanical_equipment_parameters.csv`: equipment identities, ratings, dimensions, downstream press coupling, and explicit EU/NL price/scaling gaps.
- `mechanical_particle_size_response.csv`: feed moisture calculations and structured missing rows for PSD, energy and temperature response.
- `mechanical_release_performance.csv`: measured product dry matter, crude protein and ash from fresh-biomass maceration trials, plus reported overall crude-protein recovery.
- `mechanical_dynamic_models.csv`: model registry links and implementation status.
- `mechanical_scenario_controller.csv`: PT0–PT4 scenario routing, required variables and fallback guardrails.
- `dataset_manifest.csv`, `source_register.csv`, `equation_registry.csv`, and `assumption_and_missing_data_register.csv`: package governance and traceability.

## Data-status rules
`measured`, `literature-reported`, `calculated_from_source_formula`, `manufacturer-reported`, `fitted_by_source`, `assumption`, and `missing` are used as requested. Blank numeric cells are intentional and must not be replaced with zero.

## Important limitations
1. The directly relevant maceration report provides strong comparative fresh-biomass evidence but does not publish tabulated initial/final particle-size distributions, net equipment energy values, treatment temperature rise, direct juice yield, or soluble-protein release.
2. Product-composition rows describe downstream fiber press cake and protein concentrate after pressing and heat separation. They must not be interpreted as isolated pretreatment release coefficients.
3. Public EU/Netherlands purchase prices tied to the exact cited equipment and delivery scope were not found. Price and scaling fields remain blank; dated vendor quotations are required.
4. Kick, Rittinger and Bond equations originate from dry mineral comminution. They are included only as candidate equation forms and must not be applied to wet grass without experimental calibration.
5. PT4 manufacturer ratings define a hardware envelope for wet food suspensions, not validated grass-processing performance.

## Integration readiness
The scenario controller, schemas, source registry and equation registry are ready for code integration. Predictive dynamic simulation remains blocked for scenarios lacking measured power, flow, active volume, particle-size response and release-response data. The model should raise a missing-data validation error rather than silently inserting defaults.

## Validation performed
- Comma-separated UTF-8 files with one parameter or observation per row.
- Unique IDs checked across every file.
- Required traceability fields included in all scientific parameter tables.
- SI normalization supplied only for unambiguous conversions.
- Formula text is stored only in equation/model fields, not numeric cells.
- Material state is explicit; dry and wet datasets are not combined without flags.
