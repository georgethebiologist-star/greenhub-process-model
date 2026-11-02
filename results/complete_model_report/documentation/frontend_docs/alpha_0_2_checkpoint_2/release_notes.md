# Alpha 0.2 Checkpoint 2 and Checkpoint 3A Release Notes

## Delivered

- Immutable canonical parameter and candidate registries with deterministic applicability and precedence.
- Validated run overrides, provenance, dashboard editability metadata, and machine CSV exports.
- Versioned `SimulationRequest` and `SimulationResult` contracts with strict JSON handling.
- Isolated run orchestration, structured results, process graph, five plot definitions, static plots, and complete run exports.
- One active D4 literature input, `REC-001`, and one active D4 typed mass-balance equation, `EQ-MB-001`.
- Versioned `/api/v1` WSGI adapter, structured errors, and OpenAPI 3.1 output.
- Seventeen new tests, bringing the regression inventory from 268 to 285 passing tests.

## Scientific Change

Structural mode is unchanged. For PR1 `literature_default`, precipitation recovery resolves to 0.34 from la Cour et al. (2019) rather than the structural workbook value of 0.75. In the controlled July chain, dry protein changes from 4.28306 to 2.54031 kg/h. This activation is literature-driven, unvalidated for GreenHub, and not a final design result.

## Data State

The 301 audited literature datasets now comprise 52 blocked, 248 reference-only, and one active D4 dataset. The original source CSVs and Checkpoint 1 quarantine records are unchanged. The 179 source equation rows remain 169 blocked and 10 reference-only; the new advanced overlay adds one separately approved D4 typed implementation.

## Compatibility And Operations

The integrated factory, historical factories, scenarios, workbook runs, and `python -m Greenhub.main` remain operational. The API development server runs with `python -m api`; OpenAPI and standalone schemas are generated with `python -m Greenhub.application.schema_export`.

Final verification collected and passed all 285 tests. The production entry point completed with overall and component validation passing and regenerated `integrated_greenhub_flowsheet.png` through the configured Graphviz installation.

No frontend was modified. No TEA, LCA, uncertainty, optimization, ranking, MCDA, or unsupported chemistry was added.
