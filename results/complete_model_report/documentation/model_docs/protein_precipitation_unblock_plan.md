# Protein Precipitation Unblock Plan

```yaml
scope: protein_recovery_isoelectric_reference_data
activation_policy: do_not_activate_all
current_behavior_to_preserve: PR1 soluble-protein recovery factor remains unchanged
inspection_date: 2026-07-30

source_files_inspected:
  - Greenhub/data/Protein recovery/Isoelectric/dataset_manifest.csv
  - Greenhub/data/Protein recovery/Isoelectric/validation_report.json
  - Greenhub/data/Protein recovery/Isoelectric/assumption_and_missing_data_register.csv
  - Greenhub/data/Protein recovery/Isoelectric/source_register.csv
  - Greenhub/data/Protein recovery/Isoelectric/equation_registry.csv
  - Greenhub/data/Protein recovery/Isoelectric/*.csv

overall_assessment:
  can_unblock_all_now: false
  reason: >
    The folder-level validation report passes CSV structure checks, but most
    mechanistic precipitation datasets still contain missing mandatory direct
    GreenHub inputs, textual ranges, proxy material states, or equations requiring
    mapping and calibration before process activation.
  validation_report_result: PASS

datasets:
  acid_base_demand.csv:
    classification:
      - safe_to_schema_validate
      - needs_unit_normalization
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Target pH range is present, but acid/base demand rows are missing and target pH cannot determine reagent dose.

  aggregation_coagulation_kinetics.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Kinetic/coagulation values are incomplete and cannot be substituted from equilibrium recovery.

  equipment_scale_cost_demand.csv:
    classification:
      - safe_to_schema_validate
      - needs_unit_normalization
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Screening and manufacturer-style entries need consistent scope, year, power, and cost basis before TEA use.

  ionic_strength_effects.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Existing observations do not close the GreenHub feed-specific salt/ionic-strength response.

  precipitation_kinetics.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Grass-protein precipitation rate constant is explicitly missing.

  product_moisture.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Wet-cake moisture is missing and affects drying duty and mass closure.

  protein_losses.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Some measured/proxy loss records exist, but selected GreenHub wash/separation losses remain missing.

  protein_pI_distributions.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Heterogeneous roadside-grass protein pI distribution is a critical missing input.

  protein_stability.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - blocked_do_not_activate
    reason: Functionality/denaturation during acid hold is not resolved for the GreenHub material.

  purity.csv:
    classification:
      - safe_to_schema_validate
      - needs_mass_balance_tests
    reason: Contains measured crude-protein values with normalized fractions and no assumption blanks, but should remain reference-only until mapped to product reporting with tests.

  recovery.csv:
    classification:
      - safe_to_schema_validate
      - needs_mass_balance_tests
    reason: Contains measured recovery records including the PR1-relevant 0.34 fraction, but broader activation must not change current PR1 behavior without mass-balance tests.

  residence_time.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Residence time is missing and depends on precipitation/separation kinetics.

  separation_efficiency.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Separator capture curve is missing for selected equipment and slurry state.

  solubility_versus_pH.csv:
    classification:
      - safe_to_schema_validate
      - needs_unit_normalization
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Value-bearing rows are mostly final-powder or proxy observations; the raw grass-juice pH curve is explicitly missing.

  solubility_versus_temperature.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Temperature response is not complete for direct GreenHub press juice.

  titration_curves.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_equation_mapping
      - blocked_do_not_activate
    reason: Titration curve row is explicitly missing and must not be inferred from target pH.

  washing_response.csv:
    classification:
      - safe_to_schema_validate
      - needs_missing_values
      - needs_mass_balance_tests
      - blocked_do_not_activate
    reason: Washing loss and ash-removal curves are missing.

equations:
  equation_registry.csv:
    classification:
      - safe_to_schema_validate
      - needs_equation_mapping
      - needs_mass_balance_tests
    ready_items:
      - EQ-MB-001
    blocked_or_conditional_items:
      - EQ-CHARGE-001
      - EQ-SOL-001
      - EQ-ACID-001
      - EQ-KIN-001
      - EQ-COST-001
    reason: >
      The registry itself is structurally valid. Only the generic protein mass
      balance equation is broadly direct; charge, solubility, acid demand,
      kinetics, and cost equations require measured inputs, mapping, or scoped
      calibration before activation.

smallest_safe_first_activation_candidate:
  target: recovery.csv schema-only inventory validation
  activate_process_behavior: false
  why: >
    It is small, already contains the PR1-relevant sourced value, has normalized
    fractions, and can be validated without altering PR1 behavior or adding new
    scientific constants.
  acceptance_criteria:
    - CSV loads with required columns.
    - Fraction rows have numeric normalized_si_value between 0 and 1.
    - Existing PR1-relevant row REC-001 remains 0.34 and reference-only unless explicitly mapped later.
    - No process unit, scenario, API, or frontend changes.

exact_next_implementation_stage:
  name: stage_1_read_only_reference_inventory
  actions:
    - Add a read-only protein precipitation dataset inventory/validator for Isoelectric CSVs.
    - Validate recovery.csv and purity.csv schemas plus normalized fraction bounds.
    - Keep all mechanistic pH, titration, acid-demand, kinetics, residence-time, separator, washing, and cost datasets blocked.
    - Add one focused test for the validator.
    - Do not register new active parameters or change PR1 model outputs.
```
