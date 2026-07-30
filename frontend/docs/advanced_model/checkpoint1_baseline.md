# Checkpoint 1 Baseline

Captured before Checkpoint 1 edits on 2026-07-29.

## Repository And Runtime

- Branch: `main`.
- Commit: `39dcf17` (`loaded datasets + turned global`).
- Python: 3.12.13.
- BioSTEAM: 2.53.11.
- ThermoSTEAM: 0.53.5.
- pandas: 3.0.5.
- openpyxl: 3.1.5.
- SciPy: 1.18.0.
- Existing test baseline: 264 tests passed through the repository's isolated shards.
- Primary command: `python -m Greenhub.main`, exit code 0.

## Active Reference Configuration

| Field | Value |
|---|---|
| Scenario chain | F2/PR3/AD1/BG2/NR4 |
| Nutrient-recovery order | A |
| Month | July |
| Sample | grass_baseline |
| Monthly feed | 420000 kg |
| Average upstream feed | 564.516129032258 kg/hr |
| Mode | structural_test |

## Reference Outputs

| Metric | Value |
|---|---:|
| Integrated boundary inlet | 403.9938456027056 kg/hr |
| Integrated boundary outlet | 403.99384560661497 kg/hr |
| Mass residual | -3.9093492887332104e-09 kg/hr |
| Water residual | -2.842170943040401e-14 kg/hr |
| Carbon residual | -2.220446049250313e-16 kg/hr |
| Nitrogen residual | 0.0 kg/hr |
| Phosphorus residual | -1.3877787807814457e-17 kg/hr |
| Digestate processed | 243.61944012512674 kg/hr |
| Phosphorus product stream | 0.06440653971565025 kg/hr |
| Ammonium product solution | 5.629807311037113 kg/hr |
| Gross selected-area electricity | 0.17228326893451418 kW |
| Gross selected-area heat | 7.036149712795237 kW |

These values are regression evidence, not project validation. The run identifies itself
as structural, does not rank configurations, reports no active CHP/shared utility
network, and retains out-of-range equipment cost warnings.

## Dataset Audit Baseline

- Manifest datasets: 301.
- Readiness: D1=23, D2=25, D3=253, D4=0, D5=0.
- Reported issues: 443.
- Source CSVs are immutable inputs for Checkpoint 1.

The source for model values is the generated compatibility reports under
`Greenhub/results`; the source for dataset counts is
`Greenhub/data/global_audit_package/global_validation_summary.json`.

## Post-Checkpoint Verification

- The complete suite passes: 268 tests (264 baseline plus four Checkpoint 1 tests).
- `python -m Greenhub.main` exits with code 0 and produces the integrated flowsheet,
  compatibility outputs, and Phase 7 workbooks.
- The post-checkpoint mass residual remains `-3.9093492887332104e-09 kg/hr`; reported
  elemental residuals remain zero at display precision.
- No source scientific CSV is modified and no global dataset or equation is active.
- Atomic report replacement is an output-integrity change only; it does not modify
  process calculations, scenario selection, or workbook inputs.
