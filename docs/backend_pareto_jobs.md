# Pareto analysis API

## Published BioSTEAM analysis

The website's current optimization view reads the positive-NPV screening catalog from:

```text
GET /api/v1/decision-support/pareto/latest
```

The response contains 200 positive screening-NPV cases, their saved process configurations, support assumptions, and bounded Pareto fronts. It is served from `Greenhub/results/pareto_positive_200_2026/latest_ui.json`. See [current Pareto screening catalog](pareto_screening.md) for the selection and supply basis. Figure and report endpoints return 404 until figures are generated for this catalog.

The UI replays a selected candidate's saved configuration through:

```text
POST /api/v1/decision-support/evaluate
```

This returns products, cost, utility, and operational-climate outputs for the exact saved request. The support cases are user-supplied screening scenarios; this API does not assert grant eligibility or awards. Decision-support requests that omit `candidate_economics` apply no CAPEX grant or operating premium by default.

## Ad hoc batch jobs

The generic `/api/v1/decision-support/batch-jobs` lifecycle remains available for callers that submit new candidate configurations. It writes jobs under the configured current `runs/decision_batches/` root. Historical Pareto job directories are not read or resumed by this service. These ad hoc jobs are separate from the published RVO front and do not replace or mutate its manifest.
