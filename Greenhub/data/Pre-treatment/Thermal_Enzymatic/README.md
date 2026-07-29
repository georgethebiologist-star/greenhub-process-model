# GreenHub Thermal and Enzymatic Pretreatment Dataset Suite

Path: `Greenhub/data/Pre-treatment/Thermal_Enzymatic/`

## Scope
This package covers no treatment, mild thermal treatment, enzyme-assisted treatment, and combined mild thermal plus enzyme treatment for fresh grass, alfalfa, clover, green juice and wet green-biomass pulp.

## Main datasets
- `thermal_treatment_parameters.csv`
- `thermal_kinetics.csv`
- `enzyme_database.csv`
- `enzymatic_treatment_response.csv`
- `enzymatic_kinetic_models.csv`

Supporting files:
- `thermal_enzymatic_equation_registry.csv`
- `thermal_enzymatic_scenario_controller.csv`
- `dataset_manifest.csv`
- `source_register.csv`
- `assumption_and_missing_data_register.csv`
- `validation_report.csv`

## Interpretation guardrails
1. Thermal green-juice coagulation is a downstream protein-recovery operation. It must not automatically be treated as a biomass cell-disruption response.
2. Supplier activity, optimum ranges and dosage recommendations are labelled `manufacturer-reported`. They are not measured grass-conversion results.
3. The accessible alfalfa enzyme study reports a 1.4–1.6-fold extraction enhancement across Viscozyme L and Pectinex Ultra SP-L at 1.5–6 mg/g dry alfalfa. The abstract does not map each response to each individual condition, so individual response cells remain blank.
4. Michaelis–Menten, inhibition, deactivation and Arrhenius equations are registry structures only. No Km, Vmax, Ki, deactivation constant, activation energy or pre-exponential factor is inferred.
5. Combined thermal-plus-enzyme operation is blocked until the sequence and residual enzyme activity after heating are known.
6. Missing numerical values remain blank and must never be replaced with zero.

## Integration readiness
Schemas, scenario routing, supplier metadata and traceable source-level process conditions are ready. Mechanistic dynamic simulation remains blocked for thermal and enzymatic scenarios until condition-resolved response and kinetic data are obtained.
