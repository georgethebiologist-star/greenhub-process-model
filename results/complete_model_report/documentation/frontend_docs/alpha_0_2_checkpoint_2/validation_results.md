# Validation Results

The staged verification sequence completed successfully:

- baseline targeted governance checks and `python -m Greenhub.main` passed before edits;
- the complete pre-edit suite passed;
- the complete suite passed after parameter infrastructure;
- typed equation and Phase 4 targeted tests passed, followed by the complete post-scientific suite;
- 11 application/API targeted tests passed, followed by the complete post-API suite;
- final verification is recorded in the release notes.

The added test set covers canonical-ID uniqueness, source immutability, precedence, units, bounds, JSON safety, typed equation behavior, request versioning, dynamic-mode blocking, scenario gates, isolated flowsheets, no state leakage, direct-factory equivalence, plot/export completeness, WSGI endpoints, OpenAPI references, structured errors, and no path/NaN/infinity leakage.

The reference structural F2/PR3/AD1/BG2/NR4 July result remains 403.9938456027056 kg/h entering and 403.99384560661497 kg/h leaving, with signed residual `-3.9093492887332104e-09 kg/h`. The two PR1 comparison runs also passed with residual magnitudes below `4e-9 kg/h`.

BioSTEAM equipment correlation warnings and dependency deprecations remain visible. They are warnings about scale/applicability or installed libraries, not suppressed validation results.
