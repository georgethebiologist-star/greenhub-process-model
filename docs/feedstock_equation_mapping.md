# Feedstock Equation Mapping Readiness

This layer is report-only. It annotates feedstock candidate resolution records with equation mapping readiness, but it does not execute feedstock equations, activate dynamic mode, or change model calculations.

## Statuses

- `no_equation_required_observed_value`: direct observed composition or physical value, such as moisture, ash, C, N, protein, sugars, or bulk density. The candidate can be reported without an equation.
- `equation_available_reference_only`: an equation or calculated source value is present in feedstock evidence, but it remains reference-only.
- `equation_mapping_ready`: reserved for a future reviewed mapping with inputs, units, and tests.
- `requires_equation_mapping`: the field needs an explicit equation mapping before any future activation.
- `blocked_missing_inputs`: required input data are missing.
- `blocked_unimplemented_equation`: an equation is referenced by data, but there is no approved feedstock implementation.

## Current Interpretation

Observed roadside composition values do not need equations for report-only candidate resolution. BMP values, source-fitted Wrobel equations, and calculated source formulas remain reference-only. pH-dependent precipitation, COD fractions, BMP equations, dynamic kinetics, and liquid-fraction process chemistry are not activated.

Resolver records include `equation_mapping_status`, `equation_id`, and `equation_note`. These fields are readiness metadata only and never create `model_overrides`.
