# Dynamic Model Strategy

Status: Checkpoint 3C activates deterministic L4 seasonal inventory and time-profile
simulation. No calibrated continuous dynamic scientific model is activated.

## Resolution Policy

Use the lowest defensible level for each operation:

| Level | Meaning |
|---|---|
| L0 | Routing or identity |
| L1 | Fixed empirical transformation |
| L2 | State-dependent empirical model |
| L3 | Stoichiometric, equilibrium, or kinetic steady-state model |
| L4 | Quasi-dynamic inventory or time-profile model |
| L5 | Calibrated dynamic model with reported uncertainty |

Mixers and mathematical splitters remain algebraic unless physical inventory is added.
Connecting a time-series CSV does not by itself increase model level.

## Implemented Checkpoint 3C Layer

```text
Greenhub/time_grid.py
Greenhub/feed_profiles.py
Greenhub/storage_inventory.py
Greenhub/application/feed_profile_service.py
Greenhub/application/seasonal_service.py
```

The controller supports monthly and daily quasi-dynamic grids. Each nonzero time step
rebuilds and simulates the existing integrated model, scales only the feed, evaluates
eligible unit capacities, and propagates a conserved storage inventory. It does not
place scientific time loops in `main.py`. Continuous-dynamic, batch, and hybrid modes
remain blocked until approved equations and required inputs pass their gates.

Profiles may be direct masses, normalized weights scaled to an explicit annual target,
CSV records, or the existing master workbook. Missing profile periods contribute zero
with a warning. Monthly workbook data are not interpolated into daily values.

## Dynamic State Contract

Every state defines name, unit, initial value, derivative or update function, bounds,
tolerance, source equation, model applicability, required parameters, and conservation
relationship. Events and controller actions are explicit records.

## Numerical Safeguards

- Reject negative inventories and concentrations beyond numerical tolerance.
- Guard division by zero, singular systems, invalid ranges, and unstable time steps.
- Stop on failed recycle convergence instead of returning partial success.
- Report mass and tracked-element drift at every output time.
- Compare multiple time steps before accepting a quasi-dynamic or dynamic mode.
- Preserve deterministic schedules and result hashes when no stochastic model is used.

## Priority Sequence

1. Seasonal feed availability and storage inventory.
2. Storage degradation after project measurements establish rates.
3. Pretreatment exposure and release.
4. Protein precipitation residence time and drying trajectory.
5. Membrane fouling and cleaning.
6. Digestion inventory, startup, and stability.
7. Adsorption/ion-exchange breakthrough and ammonia stripping response.
8. Plant-wide utility demand and equipment availability.

Checkpoint 3C preserves the existing steady-state and monthly-independent paths as
compatibility references. Storage capacity has no invented default: an omitted
`seasonal.storage_capacity_kg` means unbounded storage and produces a warning. Storage
degradation, water and dry-matter loss, growth, and weather response are reported as
not implemented because no eligible project data or approved equations are available.
