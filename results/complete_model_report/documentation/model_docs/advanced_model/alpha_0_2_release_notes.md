# GreenHub Alpha 0.2 Checkpoint 1 Release Notes

## Added

- A read-only, deterministic dataset quality gate.
- Row-level quarantine with reason, severity, correction, and affected pathways.
- Dataset and equation activation registries with zero automatic activation.
- Explicit unresolved cost ownership and source-file checksums.
- Parameter, dynamic, validation, application-service, result, and plot architecture
  plans.
- Governance regression tests.
- Atomic XLSX report writes that preserve an existing report if a replacement write
  fails and reduce transient Windows/Excel file-handle conflicts.

## Unchanged

- BioSTEAM scientific calculations and thermodynamics.
- Workbook defaults and scenario IDs.
- Integrated and historical factories.
- Structural mode outputs and report compatibility.
- Source literature CSV values.

## Quality Status

- Datasets: 52 blocked, 249 reference-only, 0 active.
- Quarantine: 278 row identities covering 443 issues.
- Equations: 169 blocked, 10 reference-only, 0 active.
- Costs: 24 overlap groups blocked, 0 resolved or selected.
- Scientific maturity: unchanged from the structural alpha.
- Verification: `python -m Greenhub.main` exits successfully and all 268 tests pass.

## Approval Decision For Checkpoint 2

Proceed only after review of the quarantine policy, activation matrix, canonical
parameter record, precedence, and deterministic applicability rules. Checkpoint 2 will
build immutable parameter and override infrastructure but must retain numerical
equivalence with structural mode.
