# Feedstock Basis Gates

This scaffold is report-only. It validates feedstock candidate units and basis labels for future dynamic resolution, but it does not convert values, activate parameters, or change empirical model behavior.

## Expected Basis

| Canonical field | Expected unit or basis |
| --- | --- |
| `moisture_wet_basis` | `kg water/kg wet biomass` |
| `volatile_solids_dry_basis` | `kg VS/kg dry matter` or `kg VS/kg TS` |
| `ash_dry_basis` | `kg/kg dry matter` |
| `carbon_dry_basis` | `kg/kg dry matter` |
| `hydrogen_dry_basis` | `kg/kg dry matter` |
| `oxygen_dry_basis` | `kg/kg dry matter` |
| `nitrogen_dry_basis` | `kg/kg dry matter` |
| `sulfur_dry_basis` | `kg/kg dry matter` |
| `carbon_to_nitrogen_ratio` | `kg C/kg N` |
| `bulk_density` | `kg/m3` |
| `total_protein_dry_basis` | `kg/kg dry matter` |
| `extractive_sugars_dry_basis` | `kg/kg dry matter` |

## Gate Statuses

- `basis_ok`: observed unit exactly matches an expected unit.
- `requires_basis_conversion`: observed unit is compatible but not exact, such as `percent dry matter` for a dry-basis fraction. The reported value is left unchanged.
- `blocked_wrong_basis`: observed unit or basis is incompatible with the canonical field.
- `blocked_no_equation_mapping`: the canonical field has no safe basis expectation in this scaffold.

## Activation Rule

The gate annotates report-only resolver records with `basis_status`, `expected_unit`, `observed_unit`, and `requires_basis_conversion`. It deliberately does not create `model_overrides`, interpolate data, infer missing values, or silently convert units.

See `docs/feedstock_conversion_policy.md` for the separate report-only conversion policy. That policy can flag possible future conversions, but it still does not change numeric values.
