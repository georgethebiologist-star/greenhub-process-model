# Backend-evaluated Pareto batches

The Decision Support page keeps the seeded 2,000-point local Pareto screen as a fast, explicitly proxy-based preview. Its profit and climate values are never sent to the backend as simulation results.

The **Evaluate 2,000 matching points** action submits the local screening point IDs, feed rates, and route selections to `/api/v1/decision-support/batch-jobs`. It does not submit local proxy scores. Each mapped configuration uses the existing `DecisionSupportService.evaluate()` pipeline (simulation, then post-route TEA/LCA). The job stores the original `source_sample_id`, so a backend result can be compared with its exact local candidate. Incompatible/failed candidates remain recorded with rejection reasons; incomplete objectives are not plotted. Returned objectives remain screening/proxy/incomplete when their underlying evidence is so classified; a backend run is not scientific validation. Generic sampled batches remain available through the same endpoint for other callers.

Job lifecycle endpoints:

- `POST /api/v1/decision-support/batch-jobs`: start; body accepts configuration and exactly one of `specifications` or `candidate_overrides`, plus count (1–2,000), seed, and mode. Each override row contains a unique source `sample_id` and path/value overrides restricted to `simulation.*`.
- `GET /api/v1/decision-support/batch-jobs/{job_id}`: progress and compact candidate summaries.
- `POST .../{job_id}/cancel` and `POST .../{job_id}/resume`: cooperative cancellation and resume; completed candidates are not rerun.
- `GET .../{job_id}/candidates/{sample_id}`: full configuration, report, feasibility and provenance for a selected candidate.

Job records are atomically persisted under the configured results root in `decision_batches/`. They survive worker interruption/restart; call resume to continue a nonterminal persisted job. Current execution uses one daemon worker per job and no distributed queue. A worker process must remain alive while a job is running; interruption preserves completed candidate records. Polling returns compact objective summaries plus source point IDs; full TEA/LCA reports are fetched on candidate selection. Backend output is calculated independently and shown in its own chart; it is not combined with proxy scores into a shared Pareto front.
