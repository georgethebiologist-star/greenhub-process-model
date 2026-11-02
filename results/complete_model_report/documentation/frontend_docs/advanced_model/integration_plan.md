# Advanced Model Integration Plan

Status: Checkpoint 1 architecture, no literature dataset activated.

## Objective

Advance the integrated structural alpha through additive, testable layers while keeping
the current BioSTEAM system, workbook controls, scenario IDs, unit IDs, balances, and
reports operational. The canonical compatibility reference is July
`F2/PR3/AD1/BG2/NR4`, process order `A`, in structural-test mode.

## Non-Negotiable Invariants

- Source scientific CSV files are read-only.
- D3 means schema-loadable, not calculation-ready.
- Missing is never represented by zero.
- No row is activated without identity, source, location, unit, basis, applicability,
  equation-input, and test gates.
- Every run uses a fresh BioSTEAM flowsheet and immutable input/default records.
- Existing structural calculations remain selectable and numerically characterized.
- No frontend, HTTP, deployment, TEA, LCA, MCDA, or unsupported process model is added.

## Checkpoints

### Checkpoint 1: Governance And Architecture

Create plans, record the baseline, quarantine defective rows, classify every dataset
and equation, record unresolved cost ownership, and add integrity tests. Activation
count remains zero.

### Checkpoint 2: Canonical Parameters

Add typed parameter records, unit normalization, provenance chains, deterministic
selection, immutable defaults, override validation, serialization, and run contexts.
This checkpoint must not change scientific outputs.

### Checkpoint 3: Vertical Reference Pathway

Integrate one evidence-complete route only: F2 PEF preparation, screw press,
centrifugation, PR3 isoelectric recovery, dewatering and spray drying, AD1 digestion,
BG2 water scrubbing, NR4 separation and P/N recovery, then shared utility accounting.
Each unit is activated independently after source and equation tests pass. Structural
fallback remains available.

### Checkpoint 4: Area-By-Area Extension

Extend one process area per review. PR4-PR6, advanced AD, BG1 CHP, BG3-BG6 upgrading,
and NR alternatives remain gated until their complete inputs and validation evidence
are available.

## Integration Sequence For One Unit

1. Identify candidate rows and canonical parameter identities.
2. Apply quarantine, schema, provenance, unit, basis, and applicability gates.
3. Resolve every equation symbol and required input.
4. Add typed functions and dimensional, reference, trend, boundary, and failure tests.
5. Connect parameters behind an explicit calculation mode.
6. Compare against the frozen structural baseline.
7. Validate mass, tracked elements, non-negativity, utilities, and repeatability.
8. Update readiness and maturity without claiming project validation.

## Compatibility Boundary

`Greenhub.integration.create_integrated_greenhub_system()` remains the integrated
builder. Historical factories remain calculation implementations during migration.
Advanced services will call this builder through fresh run contexts rather than mutate
module globals or workbook defaults.

## Checkpoint 1 Decision

No vertical-pathway scientific row is activated in this checkpoint. Approval for
Checkpoint 2 should follow review of the quarantine policy, activation matrix,
parameter contract, and baseline evidence.
