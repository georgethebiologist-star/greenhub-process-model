# GreenHub non-PEF PNG library

The curated report library is listed in `figure_index.csv`. Every selected baseline and Pareto case uses F1 grass preparation without PEF. The six baseline composite pages are in `01_baseline/combined/`; every selected candidate has the same six pages in `08_candidate_comparison/biosteam/{all,protein_bypass,matched_protein_bypass}/rank_00..rank_10/combined/`. Additional dense figures cover route comparisons, technical profiles, attributional climate burden, screening economics, hotspots, random design sweeps and deterministic sensitivity.

The compact grass diagram has an exact first split on **1 kg wet grass**. Later columns display selected modeled intermediate and product streams, with no invented residual mass. Gas volumes are dry ideal-gas Nm³ at 273.15 K and 101,325 Pa. The 20-year pages show cumulative cash and cumulative revenue by product. Rank 0 is the highest screening profit and is rose on Pareto plots; rank 10 has the lowest partial attributional burden and is green.

Run these commands from the repository root with the existing environment:

```powershell
.\.venv\Scripts\python.exe -m results.report_figures.run_biosteam_frontiers
.\.venv\Scripts\python.exe -m results.report_figures.run_matched_protein_bypass
.\.venv\Scripts\python.exe -m results.report_figures.run_no_pef_baseline
.\.venv\Scripts\python.exe results\report_figures\generate_biosteam_frontier_pngs.py
.\.venv\Scripts\python.exe results\report_figures\generate_dense_candidate_pngs.py
.\.venv\Scripts\python.exe -m results.report_figures.generate_no_pef_analysis_pngs
.\.venv\Scripts\python.exe -m results.report_figures.finalize_no_pef_library
```

The finalizer removes superseded curated PNGs, including prior F2/PEF, offset and sparse candidate plots. Historical `source_runs/*/plots` files remain raw simulation artifacts and are excluded from the figure index. `FIGURE_METHODOLOGY.md` gives the selection, units, financial and LCA boundaries, sensitivity assumptions, and limitations. No candidate kinetic curves or calibrated outcome uncertainty intervals are available from these steady-state runs.
