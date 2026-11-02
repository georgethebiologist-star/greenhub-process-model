# GreenHub Alpha Restoration Checkpoint

Date: 2026-07-29

## Added

- Evidence-first repository, Git, requirement, scientific, dataset, restoration, migration, and baseline audits under `docs/audit/`.
- `create_integrated_greenhub_system()` and independently addressable process-area views.
- An integrated process-area CSV and multi-sheet Excel report.
- One completeness row per active unit with explicit missing-data states and E0-E5 maturity.
- Regression tests for integration, repeated builds, compatibility, completeness, and reports.

Verification status: `python -m Greenhub.main` exits 0, Graphviz output is present, the
integrated mass residual is about `-3.91e-9 kg/h`, and all 264 collected tests pass.

## Preserved

- One connected BioSTEAM system and flowsheet.
- All current workbook scenario IDs, unit IDs, historical factories, validators, metrics, and established outputs.
- The visible BioSTEAM cost warning for the undersized compressor correlation.
- The required Graphviz PATH update immediately before `system.diagram()`.

## Not Restored Or Activated

- No confirmed deleted scientific capability was recoverable from available Git history.
- CHP and shared utilities remain missing because validated engineering inputs or recoverable historical code are unavailable.
- Protein-recovery CSV models remain disconnected because required values and schema validation are incomplete.
- No TEA, LCA, uncertainty, ranking, or MCDA scope was added.

See `docs/audit/baseline_test_results.md` and `docs/audit/implementation_log.md` for commands and verification evidence.
