# Backend-evaluated Pareto batches

The Explore/Optimization view plots backend-evaluated objective values only. The seeded 2,000-point local sampler is retained inside the “Design a new backend batch” controls solely to generate candidate configurations; its proxy profit and climate scores are not shown as backend results and are never sent as simulation outputs.

The **Evaluate 2,000 matching points** action submits the local screening point IDs, feed rates, and route selections to `/api/v1/decision-support/batch-jobs`. It does not submit local proxy scores. Each mapped configuration uses the existing `DecisionSupportService.evaluate()` pipeline (simulation, then post-route TEA/LCA). The job stores the original `source_sample_id`, so a backend result can be compared with its exact local candidate. Incompatible/failed candidates remain recorded with rejection reasons; incomplete objectives are not plotted. Returned objectives remain screening/proxy/incomplete when their underlying evidence is so classified; a backend run is not scientific validation. Generic sampled batches remain available through the same endpoint for other callers.

Job lifecycle endpoints:

- `POST /api/v1/decision-support/batch-jobs`: start; body accepts configuration and exactly one of `specifications` or `candidate_overrides`, plus count (1–2,000), seed, and mode. Each override row contains a unique source `sample_id` and path/value overrides restricted to `simulation.*`.
- `GET /api/v1/decision-support/batch-jobs/{job_id}`: progress and compact candidate summaries.
- `POST .../{job_id}/cancel` and `POST .../{job_id}/resume`: cooperative cancellation and resume; completed candidates are not rerun.
- `GET .../{job_id}/candidates/{sample_id}`: full configuration, report, feasibility and provenance for a selected candidate.

Job records are atomically persisted under the configured results root in `decision_batches/`. The default API can also read the existing `results/actual_pareto_2000/decision_batches/` saved run when present, without changing the public job endpoints. They survive worker interruption/restart; call resume to continue a nonterminal persisted job. Current execution uses one daemon worker per job and no distributed queue. A worker process must remain alive while a job is running; interruption preserves completed candidate records. Polling returns compact objective summaries plus source point IDs; full TEA/LCA reports are fetched on candidate selection. The UI shows a sampled Pareto front for backend-returned, objective-eligible pairs; climate is minimized and may still be based on a partial inventory, so technical/evidence readiness and missing LCA inputs must be checked per candidate.

Candidate economics are an explicit screening overlay. The detail view reports base revenue/OPEX, optimization savings/uplift, subsidy, subsidy-adjusted capital, tax, annual capital recovery, and the optimized after-tax-profit objective. The report's base NPV/IRR/payback values are not silently re-labelled as subsidy-adjusted financial KPIs.
