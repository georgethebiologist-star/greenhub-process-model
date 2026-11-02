# Restoration Plan

Audit date: 2026-07-29

## Priority 0: Data-Loss Or Broken-Integration Risks

1. Obtain the pre-snapshot Git history or Phase 6-to-7 patch. Current Git cannot verify
   the reported large deletion.
2. Preserve the current 262-test baseline and all public scenario IDs.
3. Do not activate disconnected protein CSV models with missing required values.
4. Keep `python -m Greenhub.main` and Graphviz/report generation operational.

No confirmed data-loss defect is restorable from current Git evidence.

## Priority 1: Scientifically Important Missing Functionality

1. CHP and plant-wide utility production are required by the Phase 6 prompt but absent.
   Restore only from historical code or validated efficiency/temperature/emission data;
   do not invent defaults.
2. Add an additive, machine-readable completeness register exposing missing mass,
   energy, sizing, cost, lifetime, consumable, and validation data per active unit.
3. Add a process-area facade over the existing integrated graph without moving code.
4. Add regression tests for the facade and completeness report.

## Priority 2: Architecture And Naming Migration

1. Introduce preferred process-area names in a new facade and integrated report.
2. Preserve phase modules as compatibility layers.
3. Document that historical `create_greenhub_system` builds only T101/S101.
4. Migrate `main.py` only after equivalence tests; avoid a repository-wide rename.

## Priority 3: Dataset Integration

1. Add typed, read-only schema validators for the protein CSVs.
2. Normalize units and validate cross-file references.
3. Resolve required blanks using measured project data or explicit scenario gating.
4. Connect one route at a time only with mass/element/trend/report tests.

## Priority 4: Engineering Completeness

1. Obtain vendor/pilot separator, membrane, dryer, digester, scrubber, PSA, MEA,
   nutrient-recovery, and storage data.
2. Add approved cost year/currency/correlation ranges, equipment life, maintenance,
   consumables, and utility-production models.
3. Validate kinetics/equilibria and operational ranges before E5 claims.

## Priority 5: Documentation And Cleanup

1. Replace normal user-facing phase labels with process-area names while retaining IDs.
2. Consolidate duplicated methodology and limitation text.
3. Keep generated files and cache guidance explicit; do not delete historical outputs
   without a retention decision.

## Controlled Implementation At This Checkpoint

Because the task does not provide an explicit approval tool, only additive Priority 1
work is authorized after these audit documents: process-area views, completeness
reporting, compatibility documentation, and tests. No module moves, scenario-ID changes,
dataset activation, CHP invention, or destructive cleanup are authorized.

