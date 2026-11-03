# GreenHub current RVO Pareto report package

This package replaces the earlier report snapshot for current Pareto interpretation. It was assembled from the no-PEF BioSTEAM launch dated 2026-11-03T12:21:09Z UTC and contains 98 indexed PNG figures, the current report in PDF/Markdown/HTML, and current source evidence.

## Contents

- `GreenHub_RVO_Pareto_Report.pdf`: summary, selected candidate tables, baseline references, and an image atlas. The embedded figures retain their original PNG appearance.
- `GreenHub_RVO_Pareto_Report.md` and `index.html`: searchable text report and visual figure index.
- `figures/`: byte-for-byte copies of the current indexed figures.
- `evidence/current_run/`: complete paired batches and manifest, with all sampled configurations and output fields.
- `evidence/selected_runs/`: detailed model reports, requests, simulation results, provenance, unit/utilities, and balances for selected candidates and baseline references.
- `documentation/model_docs/`: copy of the repository documentation tree.
- `documentation/model_data_registers/`: copy of the full model data/register tree, including advanced-model schemas and API definitions.
- `documentation/frontend_api/`: current UI/API source files used by the optimization display.
- `rvo_pareto_figure_index.csv` and `candidate_ledger.csv`: current figure and candidate indexes.
- `package_file_manifest.csv` and `package_manifest.json`: SHA-256 and file inventory.

The earlier `results/complete_model_report/` folder remains a historical snapshot; do not combine its old figure ranks, data, or conclusions with this package.
