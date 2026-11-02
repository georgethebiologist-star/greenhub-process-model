# Compatibility-First Migration Plan

Audit date: 2026-07-29

## Principles

- Preserve existing public imports, workbook sheets, scenario IDs, unit IDs, and report
  files.
- Add process-area terminology before moving modules.
- Prove behavioral equivalence with tests and characterization snapshots.
- Deprecate explicitly; never silently reinterpret a historical factory.

## Stages

### Stage 1: Additive Facade

Add one canonical integrated builder with a distinct name such as
`create_integrated_greenhub_system`. It may delegate to `create_phase7_scenario` but must
return the same connected BioSTEAM System plus named process-area views, feed
specification, scenario configuration, warnings, assumptions, validation, metrics,
reports, provenance, and completeness records.

### Stage 2: Reporting Names

Add an integrated process-area report while preserving all Phase 2-7 exports. Keep
historical sheet names in compatibility workbooks; use preferred names in the new
summary.

### Stage 3: Compatibility Markers

Document `create_greenhub_system` as the historical foundation builder. Do not redirect
it automatically because callers may depend on its two-unit object shape. Add explicit
aliases and migration examples.

### Stage 4: Optional Module Packaging

After facade, report, and equivalence tests pass, process-area packages may re-export
existing implementations. Physical file moves should occur one area at a time and only
with import-cycle tests.

### Stage 5: Historical API Deprecation

Only after an alpha release may phase names emit targeted deprecation warnings. Workbook
scenario IDs F/PR/AD/BG/NR should remain stable even if display names change.

## Compatibility Matrix

| Existing API | Migration behavior |
|---|---|
| `create_greenhub_system` | Preserve historical T101/S101 behavior; document scope |
| `create_phase3_scenario` | Preserve; expose through Preparation process-area adapter |
| `create_phase4_scenario` | Preserve; expose through Protein Recovery adapter |
| `create_phase5_scenario` | Preserve; expose through Anaerobic Digestion adapter |
| `create_phase6_scenario` | Preserve; expose through Biogas Upgrading adapter |
| `create_phase7_scenario` | Preserve as compatibility implementation for integrated builder |
| `python -m Greenhub.main` | Preserve command; migrate internals only after tests |
| Phase report files | Preserve; add integrated summary rather than replace |

## ID Migration

No unit or scenario ID migration is proposed in the audit checkpoint. Process-area names
are metadata labels only. If IDs are ever changed, reports must carry old and new IDs and
the old ID must remain an alias for at least one release cycle.

