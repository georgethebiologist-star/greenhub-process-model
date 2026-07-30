# Dynamic Model Strategy

Status: solver-independent design; no dynamic scientific model activated.

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

## Planned Layer

```text
Greenhub/dynamics/
    state.py
    time_grid.py
    integrators.py
    schedules.py
    events.py
    controllers.py
    storage.py
    results.py
```

The layer will support steady-state, monthly-independent, quasi-dynamic, batch,
continuous-dynamic, and hybrid-sequential modes. `main.py` will not contain scientific
time loops. SciPy 1.18.0 is installed, but an ODE integrator will be used only after an
equation package and all required inputs pass their gates.

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

Checkpoint 1 adds no dynamic state. The existing monthly-independent steady states are
the compatibility reference for later steady-state-equivalence tests.
