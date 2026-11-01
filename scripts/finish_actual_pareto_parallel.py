from __future__ import annotations

import json
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.scenario_exploration import pareto_front

SERVICE = None


def init_worker():
    global SERVICE
    SERVICE = DecisionSupportService()


def evaluate_one(item):
    index, config = item
    try:
        output = SERVICE.evaluate(config)
        compact = {"objectives": output.get("objectives"),
                   "feasibility": output.get("feasibility"),
                   "provenance": output.get("provenance"),
                   "candidate_economics": output.get("candidate_economics"),
                   "products": output.get("products"),
                   "tea": output.get("tea")}
        return index, {"status": "evaluated", "outputs": compact,
                       "feasibility": compact.get("feasibility"),
                       "provenance": compact.get("provenance")}
    except Exception as error:
        return index, {"status": "rejected",
                       "rejection_reason": f"{type(error).__name__}: {error}"}


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, doc):
    temp = path.with_name(path.stem + ".checkpoint.tmp")
    temp.write_text(json.dumps(doc, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def main():
    root = Path("Greenhub/results/actual_pareto_2000/decision_batches")
    job_id = (root / "job.txt").read_text(encoding="utf-8").strip()
    path = root / f"{job_id}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    existing = {row["index"]: row for row in doc.get("samples", [])}
    doc["status"] = "running"
    doc["cancel_requested"] = False
    doc["parallel_workers"] = 8
    doc["updated_at"] = now()
    save(path, doc)

    pending = [(i, config) for i, config in enumerate(doc["configurations"])
               if i not in existing]
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=8, mp_context=context,
                             initializer=init_worker) as pool:
        futures = [pool.submit(evaluate_one, item) for item in pending]
        for done, future in enumerate(as_completed(futures), 1):
            index, result = future.result()
            config = doc["configurations"][index]
            source_ids = doc.get("source_sample_ids") or []
            existing[index] = {
                "index": index,
                "sample_id": f"backend-{job_id[:8]}-{index + 1:04d}",
                "source_sample_id": source_ids[index] if index < len(source_ids) else None,
                "configuration": config,
                **result,
            }
            samples = [existing[i] for i in sorted(existing)]
            doc["samples"] = samples
            doc["completed_count"] = sum(s["status"] == "evaluated" for s in samples)
            doc["failed_count"] = sum(s["status"] == "rejected" for s in samples)
            doc["updated_at"] = now()
            if done == 1 or done % 25 == 0 or done == len(futures):
                save(path, doc)

    samples = [existing[i] for i in sorted(existing)]
    reports = [{"sample_id": s["sample_id"], "outputs": s.get("outputs"),
                "status": s.get("status"), "error": s.get("rejection_reason")}
               for s in samples]
    doc["samples"] = samples
    doc["pareto_fronts"] = [pareto_front(reports, "operating_profit", metric)
                            for metric in ("climate", "installed_capex", "route_trl")]
    doc["status"] = "completed"
    doc["updated_at"] = now()
    save(path, doc)
    print(json.dumps({"job_id": job_id, "status": doc["status"],
                      "completed": doc["completed_count"],
                      "failed": doc["failed_count"]}))


if __name__ == "__main__":
    main()
