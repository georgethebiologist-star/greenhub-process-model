# Current Pareto screening catalog

The Optimization UI and `GET /api/v1/decision-support/pareto/latest` read
`Greenhub/results/pareto_positive_200_2026/latest_ui.json`. The matching offline
preview is `frontend/public/data/greenhub-pareto-positive-200-2026.json`.

The published catalog has 200 positive screening-NPV cases from 48 distinct
BioSTEAM process designs. Every case processes more than 14,000 wet tonnes per
year. Of the 200, 150 process 18,000–25,000 t/year, 15 use hypothetical regional
imports, and the remaining 35 use the user-supplied 30,000 t/year project
supply context. Six import cases process 50,000 t/year. There are 100 cases
with protein recovery and 100 with protein bypass.

Physical designs vary route, throughput and supply cohort. The model evaluates
each process once, then applies the existing hypothetical grant, biomethane and
grass-bonus overlays. Only positive-NPV, product-producing cases are published.
This is a selected screening view: omitting negative cases truncates the
economic distribution. All grants and bonuses are what-if assumptions, and
the project-context supply, import quantities and July/October 60/40 harvest
split are not measured or contracted feed.

The generation code is `scripts/build_positive_pareto_200.py` followed by
`scripts/rebalance_positive_pareto_200.py`. The latter provides the final
throughput mix. Copy its `latest_ui.json` to the offline preview path above
after publication; the running API reads `latest_ui.json` directly. Old Pareto
result directories and previews were removed when
this catalog replaced them. No current figure/report package has been
generated for this new catalog.
