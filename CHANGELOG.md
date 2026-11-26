# Changelog

## 0.2.0-alpha.1 — internal handover candidate

- Added a double-click Windows entry point and launcher that provisions local dependencies, starts the Python API and web interface, waits for readiness, opens the browser, and stops both services on Ctrl+C.
- Updated beginner setup to install a managed CPython 3.12 runtime and made the launcher select Python 3.12 explicitly when multiple versions are installed.
- Added beginner installation and usage guidance, architecture and developer references, and troubleshooting documentation.
- Pinned the CPython 3.12 runtime dependency set and separated the pytest developer dependency; pinned pnpm through the frontend package manifest.
- Removed an obsolete frontend state restore left after storage controls were removed, and made the web host configurable so the local launcher binds only to loopback.
- Removed the hard-coded Windows Graphviz path. CLI diagram export now discovers `dot` on `PATH` and reports a clear optional-dependency message.
- Removed stale BioSTEAM package metadata and manifest files that referenced missing package source; documented unresolved GreenHub code and dataset licensing instead of assigning a license without ownership evidence.
- Removed the tracked pnpm project-store junction and duplicate frontend copy of the project documentation; the root `docs/` folder is now authoritative.
- Made generated dataset-provenance paths repository-relative (or `external/<filename>`) so completeness reports do not expose machine-specific folders.
- Cleaned obsolete presentation-builder sources, stale contract copies, and isolated scratch diagnostics; retained the active Pareto catalogs and moved the decision-support check fixture into `frontend/scripts/fixtures/`.
- Moved the reproducible economic-inventory generator into `scripts/` and documented its command for developers.
- Consolidated the Phase 7 T701 methodology so its steady-state heat-loss estimate and model limitations match the implementation.
- Added a pre-release status note recording successful checks and outstanding validation gates.
- No process equations, scenario identifiers, default scientific parameters, or source datasets were intentionally changed as part of these handover additions.

This version identifies the internal handover candidate; it is not approved for public distribution. The repository remains an alpha research snapshot pending baseline comparison, licensing review, and full pre-release validation.
