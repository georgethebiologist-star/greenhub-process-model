# REST API Contract

## Adapter

`api/app.py` is a WSGI adapter over `Greenhub.application`. It contains routing and serialization only. `POST /api/v1/simulations` currently runs synchronously because the repository has no durable job queue; every request still creates an isolated flowsheet and UUID run directory.

## Endpoints

- Discovery: `GET /api/v1/health`, `/model/info`, `/scenarios`, `/process-areas`, `/parameters`, `/parameters/{parameter_id}`.
- Validation: `POST /api/v1/parameters/validate`.
- Execution: `POST /api/v1/simulations`.
- Run resources: `GET /api/v1/simulations/{run_id}/{status|summary|process-areas|streams|units|balances|utilities|validation|graph|plots|provenance|exports}`.
- Plot data: `GET /api/v1/simulations/{run_id}/plots/{plot_id}`.
- Contract: `GET /api/v1/openapi.json`.

## Safety

Bodies are UTF-8 JSON objects limited to 2 MiB. Unknown simulation fields are rejected. Responses use strict serialization with `allow_nan=False`, contain no BioSTEAM objects, expose only run-relative artifact references, and are checked for Windows absolute paths. Expected errors have stable codes; unexpected errors return a generic message without a stack trace. No arbitrary expression execution or source-data writes exist in the adapter.

The local server command is `python -m api`. It is a development server, not a production concurrency or security boundary.
