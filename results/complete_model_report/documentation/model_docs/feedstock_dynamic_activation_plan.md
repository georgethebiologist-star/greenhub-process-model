# Feedstock Dynamic Activation Plan

This is the simplified activation plan for the current feedstock proxy and dynamic-resolution work.

## Current State

- The active empirical GreenHub model remains unchanged.
- Feedstock proxy data are report-only. They can be inspected, summarized, and resolved for readiness, but they do not enter calculations.
- Measured GreenHub feedstock data should override all proxy evidence once a validated ingestion path exists.
- Direct literature values can be considered only when the source, unit, basis, and direct/proxy status are clear.
- Indirect proxy values require explicit user choice and must never become defaults.
- Missing values stay blocked. They are useful for readiness reports, not calculations.
- `EQ-CALC-001` is typed and report-only. It can derive wet-basis moisture from wet-basis total solids for reporting, but it does not overwrite observed moisture or activate a model parameter.

## Minimum Activation Checklist

Before any feedstock value can be used by calculations:

- value present
- source present
- unit and basis clear
- direct, fallback, indirect, measured, or derived status clear
- no missing or blocked reason remains
- empirical default behavior has a focused regression test proving it is unchanged

For derived values, also require:

- typed equation only, no CSV string evaluation
- required inputs present
- source equation reviewed
- unit/basis test for input and output
- no overwrite of measured or direct observed data unless explicitly requested

## Practical Next Target

The next best implementation target is a measured-data ingestion template, not another proxy or equation layer.

It should define a small CSV or structured input schema for project measurements:

- `canonical_field`
- `value`
- `unit`
- `time_label` or `static`
- `source_id`
- `lab_reference`
- `notes`

The first implementation should remain report-only. It should validate that measured data have source/lab metadata and matching unit/basis, then show how they would outrank proxies without creating `model_overrides`.

## Activation Boundary

Do not activate dynamic feedstock resolution until there is an explicit parameter override path with tests proving:

- empirical defaults still run unchanged by default
- measured values outrank proxies only when explicitly selected
- indirect values require explicit user selection
- blocked or missing values cannot enter calculations
- derived values do not overwrite observed values automatically
