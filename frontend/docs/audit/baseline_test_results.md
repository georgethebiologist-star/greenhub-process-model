# Baseline Test And Runtime Results

Audit date: 2026-07-29

## Environment

| Item | Baseline |
|---|---|
| Python | 3.12.13, 64-bit MSC v.1944 |
| BioSTEAM | 2.53.11 |
| ThermoSTEAM | 0.53.5 |
| pandas | 3.0.5 |
| openpyxl | 3.1.5 |
| Branch/commit | `early-front-end` / `6ba0493c007df20c9f94dbf78b9214911c738044` |
| Worktree before audit | Clean |

## Active Workbook Configuration

| Field | Value |
|---|---|
| Nutrient recovery | NR4, order A |
| Upstream chain | F2 / PR3 / AD1 / BG2 |
| Month | July |
| Input basis | `structural_test` |
| Structural-test mode | True |
| Phase 7 parameter records | 134 |

## Test Baseline

Command:

```powershell
.\.venv\Scripts\pytest.exe -q --disable-warnings
```

Result: **262/262 tests passed**, exit code 0. The repository sharding plugin runs large
BioSTEAM phase files in fresh subprocesses to avoid retained-registry/memory artifacts.

## Main Baseline

Command:

```powershell
.\.venv\Scripts\python.exe -m Greenhub.main
```

Result: exit code 0. Graphviz generated `Greenhub/results/phase7_flowsheet.png`, and all
selected, comparison, limitation, CSV, seasonal, and Excel outputs were generated.

Selected run evidence:

| Quantity | Value |
|---|---:|
| Monthly grass feed | 420,000 kg |
| Average upstream feed | 564.516 kg/h |
| Digestate processed | 243.619440 kg/h |
| Complete Phase 7 boundary input/output | 403.994 kg/h / 403.994 kg/h |
| Overall mass residual | about -3.91e-9 kg/h |
| Water residual | 0 kg/h |
| C/H/O/N/K/Mg/Ca/S/Cl/Na residuals | 0 kg/h at reported precision |
| P residual | about -1.39e-17 kg/h |
| Phase 7 local electricity | 0.172283 kW |
| Phase 7 gross/external heat | 7.036150 kW / 7.036150 kW |
| Recovered heat credit | 0 kW |

The visible `C611` CostWarning is environmental/model-range evidence, not a test failure:
the structural compressor duty is below the validated BioSTEAM correlation range. It is
not suppressed.

## Post-Implementation Regression

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m Greenhub.main
```

Result: **264/264 collected tests passed** through the repository's clean subprocess
shards, including the two new integrated-interface tests. The main entrypoint exited 0,
the integrated mass residual remained about `-3.91e-9 kg/h`, and Graphviz generated both
`integrated_greenhub_flowsheet.png` and the compatibility copy `phase7_flowsheet.png`.

The new 17-sheet `integrated_greenhub_report.xlsx` was imported, formula-error scanned,
and visually rendered sheet by sheet. The scan found no `#REF!`, `#DIV/0!`, `#VALUE!`,
`#NAME?`, or `#N/A` cells. The completeness outputs contain 51 selected-unit rows plus
38 rows for implemented alternative, conditional-recycle, or compatibility configurations.
