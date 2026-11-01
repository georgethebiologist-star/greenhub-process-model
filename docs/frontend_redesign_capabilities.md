# GreenHub frontend redesign: capability and limitation notes

The redesigned navigation presents four primary work areas: Dashboard, Configure, Explore, and Reports. Model settings remain in a secondary area. The default dashboard requests the existing Python simulation service using the supported `quasi_dynamic` resolution; the legacy planning proxy remains separately labelled and is not presented as process simulation.

## What the interface currently does

- Dashboard loads a live quasi-dynamic annual result on entry, displays the backend monthly series when returned, and shows the result source, balance status, and limitations. A clearly labelled fixture is retained only as a service-unavailable preview.
- Configure exposes the annual grass availability/processing schedule, season window, route selection, evidence mode, reference month, and optional grass-reaction storage parameters. Composition fields in “Feed characterization context” are informational only and do not overwrite workbook-backed process chemistry.
- Explore separates pathway/performance, offline cost and climate hotspot previews, two local optimization preview graphs (profit vs net climate offset and profit vs screening CAPEX), and a steady-state comparison. The hotspot/optimization previews use a deterministic local screening sample (seed 42); they do not read current Dashboard/Configure values or call the backend. They are labelled offline previews, not BioSTEAM results or validated Pareto fronts.
- Dashboard TEA/LCA summary is calculated after the process run via the existing post-route decision service. It uses explicitly identified screening prices where configured; absent cost, revenue, finance, or impact data remain incomplete. Climate is the only currently characterized impact category presented as an impact score. The offline Explore previews do not reuse or imply those live report values.
- Reports includes existing backend artifacts plus a JSON reproducibility bundle (exact process request, returned simulation result, and post-route TEA/LCA report when available) and a compact CSV KPI summary. The JSON bundle is not a replacement for backend-generated engineering reports.

## Important interpretation limits

- “Quasi-dynamic” refers to the backend's supported monthly/seasonal integration. It is not a continuous-time process model or a validated transient plant digital twin.
- The default feed schedule is a configurable scenario assumption, not a location-specific measured harvest forecast. Staged VARTA chemistry is not automatically substituted into the process model.
- The steady-state comparison is a secondary reference-month calculation. It is not experimental validation and does not apply storage reactions; if storage is enabled for the primary calculation, the comparison is not storage-matched.
- The Dashboard's post-route TEA/LCA request is separate from process chemistry. Break-even is an OPEX-revenue threshold only. Payback, IRR, and NPV appear only when returned as mathematically meaningful by the backend; missing inputs are not converted to zero.
- A characterized climate subtotal is not a complete LCA. Other impact categories, full upstream inventories, and complete emissions remain unavailable unless the backend supplies them with traceable factors and boundary definitions.
- Feed composition inputs that are not calculation-connected are labelled planning context. They must not be interpreted as active model controls.

## Verification

From `frontend/`, run `npm run lint`, `npm run check:decision`, and `npm run build`. The decision check exercises backend-compatible decision request construction, evidence/readiness display safeguards, and the deterministic 2,000-scenario sampler. Backend API and simulation tests remain necessary for validating a deployed end-to-end run.
