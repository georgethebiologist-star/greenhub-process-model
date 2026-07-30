# GreenHub Alpha 0.2 Checkpoint 3C Release Notes

## Scope

Checkpoint 3C adds a deterministic seasonal controller around the existing integrated
BioSTEAM model. It does not redesign process units or add a continuous ODE model.

## Added

- Inclusive monthly and daily time-grid generation, defaulting to May-November 2026.
- Direct, normalized, CSV, and master-workbook feed-supply profiles with provenance.
- Conserved storage inventory, initial inventory, overflow, age, scheduling, and
  capacity-limited throughput.
- Per-step integrated products, utilities, ProcessState snapshots, capacity utilization,
  bottlenecks, and mass and elemental residuals.
- Additive result/export fields, seasonal plot specifications, and API resources for
  feed profiles, time series, inventory, utilization, and seasonal summaries.
- Tests for grids, profile scaling, zero-feed periods, storage conservation, overflow,
  capacity limits, repeated service isolation, serialization, and API execution.

## Compatibility

Steady-state requests keep their previous execution path. The controller invokes the
existing integrated factory and simulation for every nonzero step, so process chemistry,
scenario selection, parameter precedence, and ProcessState contracts remain shared.
No source literature CSV, frontend file, workbook default, or D4 dataset status is changed.

## Explicit Simplifications

- Storage is unbounded when `seasonal.storage_capacity_kg` is absent because no validated
  project storage capacity is available.
- Storage degradation, water loss, dry-matter loss, growth, and weather response are not
  calculated by default because eligible rates and equations are unavailable. An opt-in
  first-order degradation model is available: when the resolved parameter
  `seasonal.storage_degradation_rate_per_day` is supplied, the seasonal controller will
  apply a first-order mass loss to the stored inventory and record explicit provenance
  and limitations. Supplying no rate preserves previous behavior (no silent mass loss).
- Inventory composition is perfectly mixed and withdrawals are proportional.
- Daily mode requires a daily profile and explicit schedule; monthly data are not silently
  interpolated.
- The quasi-dynamic controller is a sequence of steady-state process evaluations with a
  discrete inventory update, not a continuous dynamic plant model.
