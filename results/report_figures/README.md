# GreenHub report figures

## Current Pareto figures

The current no-PEF Pareto figure library is generated from BioSTEAM model outputs with separate protein-enabled and protein-bypassed groups. Four paired support what-if cases are named with the Netherlands Enterprise Agency (RVO). The cases optimize net carbon versus NPV, public-support present value versus NPV, and the combined three-objective front. The current compiled report and documentation package is in [`../complete_model_report_rvo_2026/`](../complete_model_report_rvo_2026/).

The indexes `figure_index.csv` and `rvo_pareto_figure_index.csv` contain the same current 98 figures, with name, description, source batch, scenario, units and path. Canonical structured outputs are in `Greenhub/results/pareto_rvo_2026/`. The method, support assumptions, equations, data boundaries and scientific caveats are in [`docs/RVO_PARETO_METHODOLOGY.md`](../../docs/RVO_PARETO_METHODOLOGY.md).

Reproduce the current analysis from the model root:

```powershell
\.venv\Scripts\python.exe scripts\run_rvo_pareto_analysis.py
\.venv\Scripts\python.exe scripts\append_rvo_baseline_references.py
\.venv\Scripts\python.exe scripts\generate_rvo_pareto_pngs.py
```

The figure generator preserves the established GreenHub palette and exports publication-sized PNGs. A candidate's detailed hotspot figures are linked to the stored run ID and configuration. Current ranks are drawn from the saved three-objective front; ranks 0 and 10 are rose and green respectively. A candidate can appear dominated when projected onto a two-objective plane.

## Legacy outputs

Some older report exports and raw run artifacts remain in their historical folders because a prior cleanup attempt was rejected. They are marked superseded in local README files and are excluded from the current index. Do not combine their ranks or objectives with the current RVO launch. The current web API reads only `Greenhub/results/pareto_rvo_2026/latest.json` and does not serve the old batch directory.

Legacy Pareto and proxy launchers/generators have been disabled; they now stop with a pointer to the current runner rather than creating another stale rank set. The former frontend-only proxy source and price anchor have been removed from the active application.

The model is steady-state for these optimization cases. No time-resolved candidate kinetics or probabilistic confidence intervals are claimed. Parameter/design sweeps describe sampled scenarios and do not represent probability distributions of future performance.
