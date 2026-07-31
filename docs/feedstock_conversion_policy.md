# Feedstock Conversion Policy

This policy is report-only. It describes whether a feedstock candidate unit could be accepted or converted in a future reviewed pathway, but it does not convert values, write model overrides, or activate calculations.

## Statuses

- `allowed_exact_unit`: observed unit exactly matches the expected unit. No conversion is required.
- `allowed_with_no_numeric_change`: observed unit is a known equivalent label. The reported value is left unchanged.
- `possible_but_requires_explicit_conversion`: a simple conversion may be possible later, but it must be reviewed and implemented explicitly.
- `dimension_specific_no_generic_conversion`: pH and C:N ratio are field-specific and cannot use a generic feedstock conversion rule.
- `blocked_unknown_unit`: the unit pairing is not recognized for the canonical field.

## Explicit Conversion Families

The report-only policy recognizes these as possible future conversion families, but does not perform them:

- percentage to `kg/kg`
- `g/kg` to `kg/kg`
- `mg/L` to `kg/m3`

Range values are never collapsed to a midpoint. A future explicit conversion step must preserve `value_min` and `value_max` separately.

## Resolver Metadata

Feedstock candidate resolution records now include:

- `conversion_policy_status`
- `conversion_required`
- `conversion_allowed`
- `conversion_note`

These fields are for readiness reporting only. They do not alter `value`, `value_min`, `value_max`, empirical defaults, seasonal behavior, or model calculations.
