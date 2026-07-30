# Checkpoint 2 Limitations

- Only one literature dataset and one typed equation have D4 activation. Of the 301 audited source datasets, 52 remain blocked, 248 remain reference-only after the single promotion, and none is D5 project-validated.
- REC-001 reports total-N recovery for grass-clover cleared juice. Mapping the fraction to lumped soluble protein excludes non-protein N but still requires GreenHub protein/N measurements.
- No pH kinetics, titration relation, rigorous electrolyte equilibrium, protein denaturation model, precipitation equipment design, separator power, or pathway CAPEX was added.
- `project_data` and `calibrated` modes are contracts, not claims that qualifying values exist.
- Quasi-dynamic and dynamic modes are deliberately blocked. Monthly cases retain the existing independent steady-state treatment.
- The API is in-memory and synchronous. Restarting it loses run lookup state even though files remain; production use needs durable storage, authentication, a WSGI server, and a job queue.
- Result schemas type stable top-level contracts, but several nested engineering result objects remain extensible while later scientific pathways mature.
- Plot coverage is intentionally limited to implemented, defensible result fields. No optimization, ranking, TEA, LCA, uncertainty, or MCDA plot is available.
- Existing scale warnings remain: storage and compressor correlations are used below their recommended ranges in structural cases.
