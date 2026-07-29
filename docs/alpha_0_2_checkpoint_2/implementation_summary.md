# Alpha 0.2 Checkpoint 2 Implementation Summary

## Scope

This checkpoint adds the parameter, application-service, result, graph, plot, export, and API foundations requested after the read-only Checkpoint 1 audit. It also completes Checkpoint 3A by activating one scientifically bounded protein-precipitation pathway. Existing workbook and Python factories remain the calculation authority.

## Implemented

- `Greenhub.parameters` provides immutable definitions and candidates, explicit units, validation, deterministic selection, overrides, provenance, and dashboard control metadata.
- `SimulationRequest` and `SimulationResult` are versioned, JSON-safe dataclasses. Unknown request fields, null overrides, NaN, and infinity are rejected.
- Each application run receives a UUID, fresh BioSTEAM flowsheet, isolated run directory, state history, resolved parameters, checksums, software versions, graph, plots, validation, and exports.
- `EQ-MB-001` is the only newly approved D4 typed equation. `REC-001` is the only literature dataset newly promoted to an active D4 calculation input.
- `api/app.py` exposes `/api/v1` as a thin standard-library WSGI adapter. No scientific logic is implemented in HTTP code or frontend files.
- Machine contracts are generated under `Greenhub/data/advanced_model/`.

## Compatibility

`python -m Greenhub.main`, workbook-driven runs, historical factories, scenario IDs, the integrated factory, and structural defaults are preserved. `Greenhub.parameters` re-exports the historical `PARAMETER_REGISTRY` and `parameter_table()` symbols because the new package supersedes the former module path.

The repository had no live backend framework to reuse: `backend/` was empty and `api/` contained only stale bytecode. The minimal WSGI adapter therefore uses Python's standard library and adds no competing web dependency.
