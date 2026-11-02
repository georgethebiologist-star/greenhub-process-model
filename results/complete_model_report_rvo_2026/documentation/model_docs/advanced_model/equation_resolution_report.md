# Equation Resolution Report

Checkpoint 1 does not execute literature equation strings and does not use `eval()`.

## Inventory

- Global equation source rows: 183.
- Unique `(dataset, equation ID)` identities: 179.
- Blocked identities: 169.
- Reference-only identities: 10.
- Active typed equations: 0.
- Reported symbol-mismatch issues: 149.
- Reported unavailable-required-input issues: 149.

The source contains five identical rows for
`Protein recovery/Membrane/energy_data.csv::EQ-ENERGY-001`. The derived registry
collapses them into one blocked identity with `source_row_count=5`; the source CSV is
not edited.

## Activation Gate

An equation remains blocked when its identity is duplicated, source or exact location
is incomplete, expression symbols are unresolved, or required inputs are unavailable.
A source-complete equation remains reference-only until it has an approved typed
implementation with input/output unit contracts, valid ranges, documented failure
behavior, and dimensional, source-reference, trend, boundary, and invalid-input tests.

Machine-readable status is in
`Greenhub/data/global_audit_package/equation_activation_registry.csv`.

## Next Resolution Order

1. Resolve duplicate equation identities without changing scientific values.
2. Reconcile source expressions with symbol-definition fields.
3. Map every required symbol to an eligible canonical parameter.
4. Select one equation needed by the reference pathway.
5. Implement it as an explicit Python function, never arbitrary string evaluation.
6. Reproduce a source calculation and add dimensional and behavioral tests.
7. Connect behind an explicit advanced mode while retaining structural fallback.
