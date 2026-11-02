# Advanced Model Validation Plan

Status: Checkpoint 1 governance and regression plan.

## Frozen Compatibility Reference

- Commit: `39dcf17`.
- Scenario: `F2/PR3/AD1/BG2/NR4`, order `A`, July.
- Mode: structural test, formula-balanced Level-1 nutrient-recovery calculation.
- Upstream average feed: `564.516129032258 kg/hr`.
- Integrated boundary inlet: `403.9938456027056 kg/hr`.
- Integrated boundary outlet: `403.99384560661497 kg/hr`.
- Mass residual: `-3.9093492887332104e-09 kg/hr`.
- Gross selected-area electricity: `0.17228326893451418 kW`.
- Gross selected-area heat: `7.036149712795237 kW`.
- Phosphorus product: `0.06440653971565025 kg/hr`.
- Ammonium product solution: `5.629807311037113 kg/hr`.

These values characterize compatibility behavior; they are not validation against
project measurements or final product claims.

## Validation Gates

1. Dataset gate: schema, unique identity, source, exact location, units, basis,
   conditions, transferability, readiness, and quarantine.
2. Parameter gate: canonical identity, normalization, valid range, deterministic
   precedence, applicability, provenance, and override validation.
3. Equation gate: approved typed function, symbol mapping, units, required inputs,
   range, source, reference value, trend, boundary, and failure tests.
4. Unit gate: material conservation, tracked elements, non-negativity, state bounds,
   utilities, design basis, fallback comparison, and repeatability.
5. Pathway gate: one connected flowsheet, recycle convergence, area boundaries,
   products/residuals, shared utilities, and no double counting.
6. Dynamic gate: state initialization, time-grid sensitivity, mass/element drift,
   event behavior, steady-state equivalence, and solver failure reporting.
7. Result gate: JSON/CSV round trip, explicit missing states, checksums, provenance,
   plots from structured data, and deterministic content hash.
8. Compatibility gate: all historical tests, entrypoint, scenario IDs, workbook schema,
   reports, and repeated fresh construction.

## Acceptance Rules

- Existing tolerances are not relaxed to admit a new model.
- No source CSV is modified by loading, selection, override, or simulation.
- Every activated row is absent from quarantine and has explicit eligibility.
- No D4 promotion occurs without calculation, tests, and reporting.
- No D5 promotion occurs without project or independent validation.
- Missing inputs produce a blocking issue, never a silent default.

## Checkpoint 1 Tests

Validate global-audit counts, quarantine coverage, unique quarantine keys, activation
vocabulary, zero active rows, equation blocking, cost blocking, output serialization,
and source-file checksum stability. Then run the complete existing suite and primary
entrypoint.
