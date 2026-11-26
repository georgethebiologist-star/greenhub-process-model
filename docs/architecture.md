# GreenHub architecture

GreenHub keeps the scientific process model independent of its user interface and transport layer. The local interface uses two services; this leaves the Python API available for a future hosted deployment.

```text
Browser (React UI, localhost:3000)
        │ /api/v1 requests
        ▼
Node/Express web server (frontend/server.ts)
        │ forwards scientific API requests
        ▼
Python WSGI API (api/app.py, localhost:8000)
        │ application services and versioned contracts
        ▼
Greenhub model core ──► input datasets, parameters, process equations
        │
        ├──► simulation results and validation reports
        └──► separate post-simulation TEA, LCA, reporting, and optimization
```

## Main directories

| Path | Responsibility |
| --- | --- |
| `Greenhub/` | Scientific model, process units, equations, parameters, application services, TEA/LCA, and versioned input data. |
| `api/` | Transport adapter for the Python services; `python -m api` starts its local development server. |
| `frontend/src/` | React user interface and visualization components. |
| `frontend/server.ts` | Local web server, development UI middleware, and API forwarding. |
| `frontend/dist/` | Generated frontend build; recreate it with `corepack pnpm build` in `frontend/`. |
| `docs/` | User, method, data, release, and research audit documentation. |
| `tests/` | Python tests for the scientific model, services, and API. |
| `scripts/` | Research data registration, analysis, and reporting utilities. Review a script's inputs and outputs before running it. |
| `Greenhub/data/` | Input workbooks, evidence registers, data manifests, and source records. |
| `Greenhub/results/` | Run and analysis outputs; generated results are not model inputs unless explicitly registered. |

`biorefinery_platform/` provides platform catalog functionality. `outputs/`, `scratch/`, `tmp/`, IDE settings, virtual environments, package stores, and test caches may contain local or generated artifacts; do not treat them as authoritative model source data. Existing tracked research artifacts are preserved pending a separate provenance review.

## Repository map

```text
.
├── api/                         Python WSGI API and local server entry point
├── biorefinery_platform/        Shared project registry and catalog schemas
├── docs/                        User, architecture, methodology, data, audit notes
├── frontend/
│   ├── src/components/          React screens and reusable controls
│   ├── src/data/                API contracts, scenario metadata, display helpers
│   ├── package.json             Frontend commands and pinned pnpm version
│   ├── pnpm-lock.yaml           Resolved frontend dependency graph
│   └── server.ts                Development UI server and Python API proxy
├── Greenhub/
│   ├── application/             Contracts, services, API-facing orchestration
│   ├── data/                    Input workbooks, evidence and source registers
│   ├── parameters/              Parameter definitions and override resolution
│   ├── results/                 Run artifacts and research analysis outputs
│   └── *.py                     Process model, equations, TEA, LCA, reports
├── scripts/                     Research data builders and analysis tools
├── tests/                       Model, API, and application test suite
├── Start GreenHub.bat           Double-click Windows entry point
├── launch.ps1                   Windows local launcher
├── requirements.txt             Pinned runtime Python dependency set
├── requirements-dev.txt         Test tools layered on runtime dependencies
└── README.md                    Project start and documentation navigation
```

The root folders `outputs/`, `results/`, `scientific_report/`, `scratch/`, `tmp/`, and dated `.codex*` directories are present in this working copy as generated or historical working artifacts. Their provenance has not been fully reconciled, so they are not listed as permanent product architecture and were not removed during the handover work.

## Calculation boundary

The process model constructs and simulates the process flowsheet. Application services validate requests and parameters and expose simulation runs. TEA and LCA consume the resulting process inventories after simulation. Optimization evaluates selected scenarios and objectives through these interfaces; it does not replace the process equations. API and frontend layers are adapters and presentation code, not authoritative scientific calculation implementations.

## Core module map

| Responsibility | Main files |
| --- | --- |
| Thermodynamics and pseudo-components | `Greenhub/chemicals.py`, `Greenhub/component_metadata.py` |
| Workbook and feed inputs | `Greenhub/input_data.py`, `Greenhub/phase*_inputs.py`, `Greenhub/data/` |
| Unit calculations | `Greenhub/phase3_units.py` through `Greenhub/phase7_units.py`, `Greenhub/phase6_upgrading.py` |
| Integrated process factories | `Greenhub/integration.py`, `Greenhub/systems.py`, `Greenhub/phase7_systems.py` |
| Parameters and equations | `Greenhub/parameters/`, `Greenhub/scientific_equations.py` |
| Validation and metrics | `Greenhub/phase*_validation.py`, `Greenhub/phase*_metrics.py`, `Greenhub/validation.py` |
| Application and API contracts | `Greenhub/application/`, `api/app.py` |
| TEA, LCA, and reporting | `Greenhub/tea*.py`, `Greenhub/lca*.py`, `Greenhub/*reporting*.py` |
| UI components and visualizations | `frontend/src/components/`, `frontend/src/data/` |

## Compatibility and extension

Historical scenario IDs, workbook sheet names, unit IDs, and public factories are compatibility surfaces. Preserve them when adding behavior. A rename or move needs equivalence tests, updated references, and an explicit migration note.

To add a unit operation, document its basis, inputs, outputs, equations, units, ranges, fallback behavior, and missing data. Implement the process calculation, connect the unit through the relevant scenario factory, and add unit and boundary tests. Add design, utility, or cost calculations only where evidence supports them; update the applicable model-completeness and provenance registers.

The Python API's default development entry point is `api/__main__.py`. The frontend's npm scripts and dependencies are declared in `frontend/package.json`. `launch.ps1` starts these two local services and stops its child processes when interrupted.

## Deployment note

The frontend's production build is served by the Node/Express server when `NODE_ENV=production`; requests under `/api/v1` are forwarded to the Python API. This production path was smoke-checked locally: the compiled page and proxied API health endpoint both returned successfully. A hosted deployment can run these as separately managed services and set `GREENHUB_BACKEND_URL`. This preserves the Python service boundary and avoids making a local development server part of production hosting.
