# Pareto analysis API

## Published BioSTEAM analysis

The website's current optimization view reads the latest completed RVO support analysis from:

```text
GET /api/v1/decision-support/pareto/latest
GET /api/v1/decision-support/pareto/latest/figures/{group}
```

The response contains the support assumptions, separate protein-enabled and protein-bypassed groups, their two- and three-objective fronts, and the selected candidate metadata. The canonical batch JSON, plots, reproducibility steps and objective definitions are documented in [RVO Pareto methodology](RVO_PARETO_METHODOLOGY.md). The API reads only `Greenhub/results/pareto_rvo_2026/latest.json`; it does not fall back to historic Pareto batches.

The `figures/{group}` endpoint serves the corresponding current 3D PNG inline for `protein_enabled` or `protein_bypass`; it is the same file indexed in the report-figure library.

Candidate detail is read from the stored BioSTEAM run using:

```text
GET /api/v1/decision-support/runs/{run_id}
GET /api/v1/simulations/{run_id}/units
GET /api/v1/simulations/{run_id}/utilities
```

The UI uses those resources for cost, equipment energy, and operational-climate hotspots. The support cases are user-supplied screening scenarios named with RVO; this API does not assert grant eligibility or awards.

## Ad hoc batch jobs

The generic `/api/v1/decision-support/batch-jobs` lifecycle remains available for callers that submit new candidate configurations. It writes jobs under the configured current `runs/decision_batches/` root. Historical Pareto job directories are not read or resumed by this service. These ad hoc jobs are separate from the published RVO front and do not replace or mutate its manifest.
