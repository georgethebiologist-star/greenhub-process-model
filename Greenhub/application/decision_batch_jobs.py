"""Persistent, resumable background jobs for backend decision batches."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock, Thread
from uuid import uuid4
import json
import time

from Greenhub.scenario_exploration import pareto_front, sample_configurations, set_path


class DecisionBatchJobs:
    def __init__(self, root: Path, evaluator, *, read_roots=()):
        self.root = Path(root) / "decision_batches"
        self.read_roots = tuple(Path(item) / "decision_batches" for item in read_roots)
        self.root.mkdir(parents=True, exist_ok=True)
        self.evaluator = evaluator
        self._lock = RLock()
        self._workers: dict[str, Thread] = {}

    def start(self, configuration, specifications=None, *, candidate_overrides=None,
              count=128, seed=42, mode="design"):
        # The existing API caps synchronous batches at 128. Background jobs cap
        # a submitted chunk at 2,000 and resume the same persisted job by ID.
        source_ids = None
        if candidate_overrides is not None:
            if specifications is not None:
                raise ValueError("Provide specifications or candidate_overrides, not both.")
            if not isinstance(candidate_overrides, list) or not 1 <= len(candidate_overrides) <= 2000:
                raise ValueError("candidate_overrides must contain 1..2000 candidates.")
            if count != len(candidate_overrides):
                raise ValueError("count must match the number of candidate_overrides.")
            configs = []
            source_ids = []
            for candidate in candidate_overrides:
                if not isinstance(candidate, dict) or not isinstance(candidate.get("sample_id"), str) or not candidate["sample_id"]:
                    raise ValueError("Each candidate override requires a non-empty sample_id.")
                overrides = candidate.get("overrides")
                economics = candidate.get("candidate_economics")
                if not isinstance(overrides, dict) or not overrides:
                    raise ValueError("Each candidate override requires a non-empty overrides object.")
                config = json.loads(json.dumps(configuration))
                for path, value in overrides.items():
                    if not isinstance(path, str) or not (path.startswith("simulation.") or path.startswith("candidate_economics.")):
                        raise ValueError("Candidate override paths must be under simulation or candidate_economics.")
                    set_path(config, path, value)
                if economics is not None:
                    if not isinstance(economics, dict):
                        raise ValueError("candidate_economics must be an object when supplied.")
                    config["candidate_economics"] = economics
                configs.append(config)
                source_ids.append(candidate["sample_id"])
            if len(set(source_ids)) != len(source_ids):
                raise ValueError("Candidate source sample_id values must be unique.")
        else:
            if specifications is None:
                raise ValueError("Provide sampling specifications or candidate_overrides.")
            configs = sample_configurations(configuration, specifications, count, seed, mode, max_count=2000)
        job_id = uuid4().hex
        doc = {"job_id": job_id, "status": "queued", "mode": mode, "seed": seed,
               "requested_count": count, "completed_count": 0, "failed_count": 0,
               "configurations": configs, "samples": [], "cancel_requested": False,
               "created_at": self._now(), "updated_at": self._now(),
               "sampling_method": "Latin hypercube" if mode == "design" else "Monte Carlo inverse-CDF",
               "specifications": specifications, "source_sample_ids": source_ids}
        self._save(doc)
        self._launch(job_id)
        return self.status(job_id)

    def status(self, job_id):
        doc = self._load(job_id)
        public = {k: v for k, v in doc.items() if k not in ("configurations", "samples", "source_sample_ids")}
        public["samples"] = [{"index": row["index"], "sample_id": row["sample_id"],
                              "source_sample_id": row.get("source_sample_id"),
                              "status": row["status"], "rejection_reason": row.get("rejection_reason"),
                              "configuration": row["configuration"],
                              "objectives": (row.get("outputs") or {}).get("objectives"),
                              "feasibility": row.get("feasibility")}
                             for row in doc["samples"]]
        return public

    def candidate(self, job_id, sample_id):
        doc = self._load(job_id)
        row = next((item for item in doc["samples"] if item["sample_id"] == sample_id), None)
        if row is None: raise KeyError(f"Unknown decision batch candidate '{sample_id}'.")
        return row

    def cancel(self, job_id):
        with self._lock:
            doc = self._load(job_id)
            if doc["status"] not in ("completed", "cancelled"):
                doc["cancel_requested"] = True
                doc["updated_at"] = self._now()
                if doc["status"] == "queued": doc["status"] = "cancelling"
                self._save(doc)
        return self.status(job_id)

    def resume(self, job_id):
        with self._lock:
            doc = self._load(job_id)
            if doc["status"] == "completed": return self.status(job_id)
            doc["cancel_requested"] = False
            doc["status"] = "queued"
            doc["updated_at"] = self._now()
            self._save(doc)
            self._launch(job_id)
        return self.status(job_id)

    def _launch(self, job_id):
        worker = self._workers.get(job_id)
        if worker and worker.is_alive(): return
        worker = Thread(target=self._work, args=(job_id,), name=f"greenhub-batch-{job_id[:8]}", daemon=True)
        self._workers[job_id] = worker
        worker.start()

    def _work(self, job_id):
        doc = self._load(job_id)
        doc["status"] = "running"; doc["updated_at"] = self._now(); self._save(doc)
        done = {row["index"] for row in doc["samples"]}
        for index, config in enumerate(doc["configurations"]):
            if index in done: continue
            doc = self._load(job_id)
            if doc.get("cancel_requested"):
                doc["status"] = "cancelled"; doc["updated_at"] = self._now(); self._save(doc); return
            source_ids = doc.get("source_sample_ids") or []
            row = {"index": index, "sample_id": f"backend-{job_id[:8]}-{index+1:04d}",
                   "source_sample_id": source_ids[index] if index < len(source_ids) else None,
                   "configuration": config}
            try:
                output = self.evaluator(config)
                row.update(status="evaluated", outputs=output,
                           feasibility=output.get("feasibility"), provenance=output.get("provenance"))
            except Exception as error:  # Persist individual failures; job should continue.
                row.update(status="rejected", rejection_reason=f"{type(error).__name__}: {error}")
            with self._lock:
                doc = self._load(job_id)
                doc["samples"].append(row)
                doc["completed_count"] = sum(s["status"] == "evaluated" for s in doc["samples"])
                doc["failed_count"] = sum(s["status"] == "rejected" for s in doc["samples"])
                doc["updated_at"] = self._now()
                self._save(doc)
        doc = self._load(job_id)
        reports = [{"sample_id": s["sample_id"], "outputs": s.get("outputs"),
                    "status": s["status"], "error": s.get("rejection_reason")} for s in doc["samples"]]
        try:
            doc["pareto_fronts"] = [pareto_front(reports, "operating_profit", metric)
                                    for metric in ("climate", "installed_capex", "route_trl")]
        except Exception as error:
            doc["pareto_fronts"] = []
            doc["pareto_error"] = f"{type(error).__name__}: {error}"
        doc["status"] = "completed"; doc["updated_at"] = self._now(); self._save(doc)

    def _path(self, job_id):
        if not job_id.isalnum(): raise ValueError("Invalid decision batch job ID.")
        filename = f"{job_id}.json"
        primary = self.root / filename
        if primary.exists(): return primary
        return next((root / filename for root in self.read_roots if (root / filename).exists()), primary)

    def _load(self, job_id):
        path = self._path(job_id)
        if not path.exists(): raise KeyError(f"Unknown decision batch job '{job_id}'.")
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, doc):
        path = self._path(doc["job_id"])
        temp = path.with_name(f"{path.stem}.{uuid4().hex}.tmp")
        temp.write_text(json.dumps(doc, allow_nan=False), encoding="utf-8")
        for attempt in range(20):
            try:
                temp.replace(path)
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.1)

    @staticmethod
    def _now(): return datetime.now(timezone.utc).isoformat()
