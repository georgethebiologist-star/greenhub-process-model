from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Greenhub.application.decision_batch_jobs import DecisionBatchJobs
from Greenhub.application.decision_support_service import DecisionSupportService, default_configuration


def candidates(count: int = 2000, seed: int = 42):
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        ad = rng.choice(("AD0", "AD1", "AD3"))
        rows.append({
            "sample_id": f"actual-42-{index + 1:04d}",
            "overrides": {
                "simulation.wet_feed_rate_kg_hr": rng.uniform(500, 1500),
                "simulation.plant_capacity_kg_hr": rng.uniform(1000, 2000),
                "simulation.scenarios.feed_preparation": rng.choice(("F1", "F2")),
                "simulation.scenarios.protein_recovery": rng.choice(("PR0", "PR1", "PR2", "PR3")),
                "simulation.scenarios.anaerobic_digestion": ad,
                "simulation.scenarios.biogas_upgrading": rng.choice(("BG0", "BG2", "BG3", "BG4")) if ad != "AD0" else "BG0",
                "simulation.scenarios.nutrient_recovery": rng.choice(("NR0", "NR1", "NR2", "NR3", "NR4")) if ad != "AD0" else "NR0",
            },
            "candidate_economics": {
                "labour_reduction": rng.uniform(0, 0.30), "logistics_reduction": rng.uniform(0, 0.25),
                "energy_reduction": rng.uniform(0, 0.25), "protein_yield_uplift": rng.uniform(0, 0.20),
                "nutrient_recovery_uplift": rng.uniform(0, 0.15), "subsidy_rate": 0.20,
                "subsidy_cap_eur": 250000.0, "eligible_capex_fraction": 0.35,
                "tax_rate": 0.258, "project_lifetime_years": 20, "discount_rate": 0.08,
            },
        })
    return rows


def main():
    base = default_configuration()
    base["use_screening_process_assumptions"] = True
    base["use_screening_lca_factors"] = True
    base["financial_assumptions"]["use_screening_price_benchmarks"] = True
    output_root = Path("Greenhub/results/actual_pareto_2000")
    output_root.mkdir(parents=True, exist_ok=True)
    jobs = DecisionBatchJobs(output_root, DecisionSupportService().evaluate)
    status = jobs.start(base, candidate_overrides=candidates(), count=2000, seed=42, mode="design")
    (output_root / "decision_batches" / "job.txt").write_text(status["job_id"], encoding="utf-8")
    while jobs.status(status["job_id"])["status"] in {"queued", "running", "cancelling"}:
        time.sleep(10)
    print(json.dumps(jobs.status(status["job_id"])))


if __name__ == "__main__":
    main()
