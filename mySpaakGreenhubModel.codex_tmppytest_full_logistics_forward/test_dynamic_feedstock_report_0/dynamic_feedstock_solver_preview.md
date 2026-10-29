# Dynamic Feedstock Solver Preview

This artifact is a dynamic-solving preparation report. It does not activate dynamic calculation mode, create model overrides, or change the empirical BioSTEAM model.

## Status

- Time steps: 1
- Resolved field-time values: 10
- Blocked field-time values: 0
- Moisture/TS conflicts reconciled: 1
- Reconciled fields: moisture_wet_basis
- Indirect proxies allowed: False
- Interpolation: disabled
- Range midpoint calculation: disabled
- Calculation ready: False
- Activation readiness: False

## Confidence Distribution

- `derived_from_literature`: 1
- `direct_literature`: 9

## Source Distribution

- `derived`: 1
- `literature`: 9
- `measured`: 0
- `proxy`: 0

## Moisture And Total Solids Reconciliation

- `reconciled_conflict`: 1 time step(s)
- authoritative `total_solids_wet_basis`: 1 time step(s)
- tolerance: 1e-06
- conflicting original values: preserved in CSV provenance and bundle conflict records

## Measured Data

- status: `not_supplied`
- source: `none`
- usable rows: 0
- invalid rows: 0
- example rows skipped: 0

## Blocked Fields

- None in this preview; activation remains blocked by validation and model-integration gates.

## Assumptions

- No engineering assumptions selected.

## Warnings

- `2026-05:moisture_ts_conflict_reconciled:authoritative=total_solids_wet_basis:reconciled=moisture_wet_basis`

## Activation Boundary

The bundles are typed inputs for a future solver, but they remain preview-only. Moisture/TS conflicts are now reconciled transparently; real activation still requires measured-data review, remaining cross-field validation gates, explicit parameter mapping, and regression tests proving the empirical path is unchanged.
