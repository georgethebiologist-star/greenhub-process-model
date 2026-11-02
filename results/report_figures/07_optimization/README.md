# Current Pareto analysis

Use `pareto_rvo_figure_index.csv` as the index for figures generated from the latest no-PEF BioSTEAM launch. The authoritative model outputs are in `Greenhub/results/pareto_rvo_2026/`; reproduce them with `scripts/run_rvo_pareto_analysis.py`, append exact baseline references with `scripts/append_rvo_baseline_references.py`, and regenerate images with `scripts/generate_rvo_pareto_pngs.py`.

This run contains separate active-protein and protein-bypass batches, four paired RVO-labelled what-if financial cases, net-carbon/NPV and support-PV/NPV Pareto fronts, and 3-objective fronts. Three-objective rank 0 is the maximum-NPV endpoint; rank 10 is the minimum-net-carbon endpoint. On the 2D carbon–NPV image, selected 3D-front points may appear dominated in projection by design. Cases A–D are user-defined screening scenarios, not confirmed DEI+/SDE++ awards or tariffs. See [methodology](../../../docs/RVO_PARETO_METHODOLOGY.md) and the figure index for full boundaries and units.

Earlier figures in legacy subfolders are superseded. This launch's PNGs are in the index and new protein-group candidate folders; unindexed legacy files should not be cited as outputs from this run.
