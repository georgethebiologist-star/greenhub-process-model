# Dataset Activation Matrix

Checkpoint 1 decision: no dataset and no row is active or default-eligible.

## Eligibility Policy

| Eligibility | Meaning in Checkpoint 1 |
|---|---|
| blocked | One or more identity, provenance, unit, basis, equation, or readiness gates fail |
| reference_only | Schema-loadable evidence that has not passed GreenHub applicability and unit-level tests |
| eligible_default | Not assigned |
| eligible_calibration | Not assigned |
| eligible_validation | Not assigned |
| active | Not assigned |

D1 and D2 datasets are blocked. D3 datasets without non-cost audit defects are
reference-only. Cost-overlap flags block cost aggregation even when the wider dataset
can remain reference-only.

## Decisions By Area

| Audit category | Blocked | Reference-only | Active |
|---|---:|---:|---:|
| Bigas production + upgrade | 13 | 111 | 0 |
| Centrifuge | 8 | 4 | 0 |
| Pre-treatment | 20 | 20 | 0 |
| Protein recovery | 5 | 52 | 0 |
| Resource recovery | 6 | 62 | 0 |
| Total | 52 | 249 | 0 |

The inherited spelling `Bigas production + upgrade` is retained as source metadata and
is not silently renamed in the audit outputs.

## Quarantine Coverage

The 443 audit issues aggregate to 278 unique `(dataset, row ID, parameter)` quarantine
records. Every quarantine record is blocked and includes reason, severity, required
correction, and affected calculation pathways.

Machine-readable sources:

- `Greenhub/data/global_audit_package/global_quarantine_register.csv`
- `Greenhub/data/global_audit_package/dataset_activation_matrix.csv`
- `Greenhub/data/global_audit_package/source_dataset_checksums.csv`
- `Greenhub/data/global_audit_package/checkpoint1_registry_summary.json`

## Activation Procedure

A later checkpoint may change one row only after source identity, exact location, units,
basis, operating conditions, transferability, required equation inputs, deterministic
selection, scientific tests, and structural fallback comparison all pass. D4 and D5
are not assigned by this matrix.
