# GreenHub research evidence package

This directory contains a repository based scientific draft and its reproducible baseline and matched nutrient route runs. The manuscript's F2/PEF reference and conclusion predate the current no-PEF RVO Pareto analysis; they are not a report of the new optimization launch. The current separate analysis is documented in `../docs/RVO_PARETO_METHODOLOGY.md`, with canonical data under `../Greenhub/results/pareto_rvo_2026/` and PNGs under `../results/report_figures/`.

## Main files

- `GreenHub_scientific_report.docx` and `.md`: editable report and source text.
- `baseline_report.json`: complete fresh reference run, including technical, TEA, LCA, provenance and warnings.
- `route_comparison.csv`: four matched nutrient routes at the same July feed and operating basis.
- `baseline_kpis.csv`, `products.csv`, `balances.csv`, `parameter_evidence.csv`, `tea_*.csv`, `lca_inventory.csv`, `warnings.csv`: extracted tabular evidence.
- `figures/` and `figure_catalogue.csv`: nine figures in SVG and PNG, with a catalogue.
- `reference_configuration.json`: unchanged decision-support default configuration used for the baseline.
- `model_runs/` and `comparison_runs/`: native exported run artifacts.

## Reproduction

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe -m scientific_report.reproduce
.\.venv\Scripts\python.exe -m scientific_report.compare_routes
.\.venv\Scripts\python.exe scientific_report\make_figures.py
& 'C:\Users\katrb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scientific_report\build_docx.py
```

The reference is a July steady state extrapolated over 8,760 h. It does not represent measured annual or seasonal operations. Installed CAPEX, complete OPEX, revenue, NPV, IRR and complete climate impacts remain unresolved. The decision-support candidate economic overlay is not an eligible investment metric when these accounts are incomplete. No actual-model Pareto optimum is claimed.

The DOCX was structurally checked, but page rendering could not be completed in this environment because the bundled LibreOffice executable was unavailable. Review pagination and table breaks in Word before manuscript submission.
