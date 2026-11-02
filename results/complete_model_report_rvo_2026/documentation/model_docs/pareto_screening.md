# Pareto analysis status

The former frontend-only Pareto calculator based on `paretoReference.json` has been retired from the website. It is not a BioSTEAM simulation and must not be interpreted as a current optimization result.

The authoritative no-PEF analysis is the BioSTEAM RVO what-if launch described in [RVO Pareto methodology](RVO_PARETO_METHODOLOGY.md). The current UI reads its published output through `GET /api/v1/decision-support/pareto/latest`; paired run metadata and candidate outputs are stored in `Greenhub/results/pareto_rvo_2026/`. Historic proxy source and reference files remain only as repository history and are not imported by the current optimization or hotspot views.
