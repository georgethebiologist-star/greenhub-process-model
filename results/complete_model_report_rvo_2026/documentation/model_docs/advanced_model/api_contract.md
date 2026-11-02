# Scientific Application Contract

Status: backend-neutral architecture; no web framework or transport adapter.

## Boundary

The scientific core exposes pure Python services under a future
`Greenhub.application` package. It does not import HTTP, database, frontend, or
deployment code. Frontend, API, and backend directories remain out of scope.

## JSON-Compatible Contracts

`SimulationRequest` contains request ID, scenario selection, month or time horizon,
calculation mode, parameter overrides, random seed when applicable, requested outputs,
and structural-fallback policy.

`ParameterOverride` contains canonical parameter ID, value, unit, reason, mode,
provenance note, and rebuild requirement.

`ScenarioSelection` contains F, PR, AD, BG, and NR IDs plus process order and optional
technology selections.

`SimulationResult` contains run ID, status, timestamps, deterministic result hash,
summary, process areas, streams, units, balances, utilities, products, warnings,
validation issues, plot specifications, and export paths.

`ValidationIssue` contains code, severity, process area, object ID, field, message,
observed value, expected condition, and blocking state.

`PlotSpecification` contains plot ID, title, axes and units, source dataset, process
area, scenario, run ID, assumptions, warnings, and stable export paths.

`ProcessAreaResult` contains area ID and name, active units, inlet/outlet streams,
metrics, balances, utilities, products, assumptions, warnings, validation, and model
levels.

All contracts serialize through JSON-compatible primitives. Missing, not applicable,
not implemented, failed, and unavailable states remain distinct.

## Planned Services

```text
Greenhub/application/
    contracts.py
    simulation_service.py
    parameter_service.py
    scenario_service.py
    result_service.py
    plot_service.py
```

Services will list scenarios, process areas, and editable parameters; resolve defaults;
validate overrides; start and inspect isolated runs; fetch summaries, area/stream/unit
results, balances, plots, and exports.

## Isolation And Reproducibility

Each simulation creates a fresh integrated model and flowsheet. Requests never mutate
global defaults. A run directory records the request, active values, provenance,
checksums, warnings, software versions, Git commit, and calculation modes. Identical
resolved configurations must produce an identical content hash even when run IDs and
timestamps differ.

Progress callbacks and cancellation will be application concerns. Cancellation must
leave no run marked successful and must not expose a partially mutated model to another
request.
