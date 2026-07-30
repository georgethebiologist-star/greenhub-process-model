# Canonical Parameter Architecture

Status: design contract for Checkpoint 2; no runtime registry implemented here.

## Record Model

The future `Greenhub.parameters` package will use frozen dataclasses and standard-library
serialization. A canonical parameter record must carry:

- canonical ID, display name, description, process area, unit type and unit ID;
- technology, scenario, component, material/feed type, and process position;
- original value and unit, normalized SI value and unit, and basis;
- temperature, pressure, pH, solids, scale, valid range, and operating conditions;
- source, exact source location, evidence class, transferability class, and directly
  reported uncertainty;
- integration eligibility, default eligibility, provenance chain, and warnings.

Blank optional context remains `None`. A required blank blocks resolution. Numerical
zero is valid only when the source or calculation explicitly reports zero.

## Value Status

Only these statuses are allowed: `measured_project`, `calibrated_project`,
`literature_direct`, `fitted_by_source`, `calculated_from_source_equation`,
`manufacturer_direct`, `explicit_user_override`, `structural_placeholder`, `missing`,
and `not_applicable`.

The audit package currently uses some different labels. They must be mapped explicitly;
unknown labels may not be silently coerced into eligible evidence.

## Resolution Precedence

1. Explicit run-specific user override.
2. Saved project override.
3. Measured project value.
4. Calibrated project value.
5. Eligible direct literature value selected for applicability.
6. Existing workbook value.
7. Explicit structural placeholder.
8. Missing and calculation gate.

The resolved record retains every rejected candidate and the full provenance chain.
Overrides never mutate the source record or source CSV.

## Deterministic Applicability Selection

Selection first applies hard gates for identity, process, technology, units, basis,
valid range, required operating context, and integration eligibility. Remaining
candidates are compared through inspectable dimensions: material similarity,
technology match, scale, temperature, pH, solids, pressure, process position, evidence
quality, and declared transferability.

Checkpoint 2 must define the scoring policy in configuration and tests. No numerical
weights are invented here. If required context or a defensible tie-break is absent, the
selector returns missing with rejected candidates and warnings instead of guessing.

## Dashboard Contract

Parameters are classified as user operating control, design parameter, scientific
model parameter, or fixed identity/provenance parameter. Defaults are immutable.
Overrides are separate records with requester, timestamp, reason, original value,
replacement value, unit, validation outcome, and rebuild requirement.

- Operating controls are normally editable.
- Design parameters are editable only in design mode.
- Scientific parameters require expert mode and preserved provenance.
- Identity and provenance fields are not normally editable.

## Planned Package

```text
Greenhub/parameters/
    __init__.py
    models.py
    registry.py
    loaders.py
    selectors.py
    units.py
    provenance.py
    overrides.py
    validation.py
    serialization.py
```

The registry will cache immutable parsing by file checksum. Resolved run state remains
isolated and is never cached as mutable BioSTEAM state.
