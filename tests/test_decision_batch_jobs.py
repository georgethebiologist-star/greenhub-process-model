import time
import pytest

from Greenhub.application.decision_batch_jobs import DecisionBatchJobs


def wait_for(jobs, job_id, status):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        report = jobs.status(job_id)
        if report["status"] == status:
            return report
        time.sleep(0.01)
    raise AssertionError(f"job did not reach {status}: {jobs.status(job_id)}")


def test_persistent_job_records_each_candidate_and_pareto(tmp_path):
    def evaluator(config):
        x = config["x"]
        return {"feasibility": {"eligible_for_ranking": True}, "objectives": {
            "operating_profit": {"value": x, "eligible": True, "direction": "maximize"},
            "climate": {"value": 10-x, "eligible": True, "direction": "minimize"},
            "installed_capex": {"value": x+1, "eligible": True, "direction": "minimize"},
            "route_trl": {"value": None, "eligible": False, "direction": "maximize"},
        }}
    jobs = DecisionBatchJobs(tmp_path, evaluator)
    initial = jobs.start({"x": 0}, [{"path": "x", "low": 1, "high": 2}], count=2, seed=9)
    complete = wait_for(jobs, initial["job_id"], "completed")
    assert complete["completed_count"] == 2
    assert [row["status"] for row in complete["samples"]] == ["evaluated", "evaluated"]
    assert complete["pareto_fronts"][0]["label"] == "Pareto among sampled feasible scenarios"
    assert jobs.status(initial["job_id"])["samples"] == complete["samples"]


def test_candidate_overrides_preserve_exact_source_point_mapping(tmp_path):
    jobs = DecisionBatchJobs(tmp_path, lambda config: {
        "received": config["simulation"],
        "feasibility": {"eligible_for_ranking": False}, "objectives": {},
    })
    source = [
        {"sample_id": "S-42-0001", "overrides": {"simulation.wet_feed_rate_kg_hr": 12.5,
                                                       "simulation.scenarios.protein_recovery": "PR2"}},
        {"sample_id": "S-42-0002", "overrides": {"simulation.wet_feed_rate_kg_hr": 25,
                                                       "simulation.scenarios.protein_recovery": "PR0"}},
    ]
    started = jobs.start({"simulation": {"scenarios": {"protein_recovery": "PR3"}}},
                         candidate_overrides=source, count=2)
    completed = wait_for(jobs, started["job_id"], "completed")
    assert [row["source_sample_id"] for row in completed["samples"]] == ["S-42-0001", "S-42-0002"]
    first = jobs.candidate(started["job_id"], completed["samples"][0]["sample_id"])
    assert first["configuration"]["simulation"]["wet_feed_rate_kg_hr"] == 12.5
    assert first["outputs"]["received"]["scenarios"]["protein_recovery"] == "PR2"
    assert first["source_sample_id"] == "S-42-0001"


def test_persisted_jobs_can_be_read_from_legacy_result_roots(tmp_path):
    source_root = tmp_path / "archived"
    writer = DecisionBatchJobs(source_root, lambda config: {
        "configuration_echo": config,
        "feasibility": {"eligible_for_ranking": False},
        "objectives": {},
    })
    started = writer.start({"run": "existing"}, [{"path": "run", "low": 1, "high": 1}], count=1)
    complete = wait_for(writer, started["job_id"], "completed")

    reader = DecisionBatchJobs(tmp_path / "current", lambda _config: {}, read_roots=(source_root,))
    assert reader.status(started["job_id"])["status"] == "completed"
    assert reader.candidate(started["job_id"], complete["samples"][0]["sample_id"])["outputs"]["configuration_echo"] == {"run": 1}


def test_candidate_overrides_reject_duplicate_source_ids_and_unsafe_paths(tmp_path):
    jobs = DecisionBatchJobs(tmp_path, lambda config: {})
    with pytest.raises(ValueError, match="unique"):
        jobs.start({}, candidate_overrides=[
            {"sample_id": "same", "overrides": {"simulation.x": 1}},
            {"sample_id": "same", "overrides": {"simulation.x": 2}},
        ], count=2)
    with pytest.raises(ValueError, match="under simulation"):
        jobs.start({}, candidate_overrides=[
            {"sample_id": "one", "overrides": {"other.x": 1}},
        ], count=1)


def test_job_persists_rejection_and_can_resume_after_cancellation(tmp_path):
    calls = []
    def evaluator(config):
        calls.append(config["x"])
        if config["x"] > 1.5: raise ValueError("synthetic rejection")
        return {"feasibility": {"eligible_for_ranking": False}, "objectives": {}}
    jobs = DecisionBatchJobs(tmp_path, evaluator)
    started = jobs.start({"x": 0}, [{"path": "x", "low": 1, "high": 2}], count=3, seed=2)
    done = wait_for(jobs, started["job_id"], "completed")
    assert done["failed_count"] >= 0
    assert len(done["samples"]) == 3
    assert any(row.get("rejection_reason") for row in done["samples"])


def test_cancel_and_resume_skips_already_persisted_candidates(tmp_path):
    import threading
    entered = threading.Event()
    release = threading.Event()
    calls = []
    def evaluator(config):
        calls.append(config["x"])
        if len(calls) == 1:
            entered.set()
            release.wait(2)
        return {"feasibility": {"eligible_for_ranking": False}, "objectives": {}}
    jobs = DecisionBatchJobs(tmp_path, evaluator)
    started = jobs.start({"x": 0}, [{"path": "x", "low": 1, "high": 2}], count=3, seed=4)
    assert entered.wait(2)
    jobs.cancel(started["job_id"])
    release.set()
    cancelled = wait_for(jobs, started["job_id"], "cancelled")
    assert len(cancelled["samples"]) == 1
    jobs.resume(started["job_id"])
    complete = wait_for(jobs, started["job_id"], "completed")
    assert len(complete["samples"]) == 3
    assert len(calls) == 3
