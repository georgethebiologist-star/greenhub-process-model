"""Publish 200 positive-NPV, high-throughput GreenHub screening scenarios.

Physical routes are simulated once; the existing post-route evaluator pairs each
with the same 24 hypothetical support cases used by the prior Pareto study.
Negative-NPV rows are never written into the new publication.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
import json
import multiprocessing
import os
from pathlib import Path
import time

from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.application.simulation_service import SimulationService
from Greenhub.pareto_reporting import pareto_ui_projection
from scripts import run_rvo_pareto_analysis as pareto

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Greenhub/results/pareto_positive_200_2026"
SOURCE = ROOT / "results/report_figures/no_pef_F1.json"
TARGET_COUNT = 200
SEED = 20261109
ROUTES = {
    "protein_enabled": (
        ("PR3", "AD1", "BG4", "NR4", "A"),
        ("PR1", "AD1", "BG2", "NR4", "B"),
        ("PR2", "AD1", "BG2", "NR2", "A"),
        ("PR3", "AD3", "BG4", "NR3", "A"),
        ("PR1", "AD3", "BG3", "NR6", "A"),
        ("PR2", "AD1", "BG4", "NR1", "A"),
        ("PR3", "AD1", "BG2", "NR6", "A"),
        ("PR1", "AD3", "BG4", "NR4", "C"),
    ),
    "protein_bypass": (
        ("PR0", "AD1", "BG2", "NR4", "C"),
        ("PR0", "AD1", "BG4", "NR4", "A"),
        ("PR0", "AD3", "BG2", "NR3", "A"),
        ("PR0", "AD1", "BG3", "NR2", "A"),
        ("PR0", "AD3", "BG4", "NR6", "A"),
        ("PR0", "AD1", "BG2", "NR1", "A"),
        ("PR0", "AD3", "BG3", "NR4", "B"),
        ("PR0", "AD1", "BG4", "NR3", "A"),
    ),
}
CORE_TARGETS = (18_000, 19_000, 20_000, 21_000, 22_000, 23_000, 24_000, 25_000,
                16_000, 17_000, 26_000, 28_000, 29_000)
IMPORT_TARGETS = (35_000, 40_000, 45_000, 50_000)


def _configuration(base: dict, group: str, index: int, target_t: int, imported: bool) -> dict:
    item = pareto.make_designs(base, group, 1, SEED + index + (0 if group == "protein_enabled" else 10_000))[0]
    config = item["configuration"]
    sim = config["simulation"]
    route = ROUTES[group][index % len(ROUTES[group])]
    sim["scenarios"] = dict(zip(("protein_recovery", "anaerobic_digestion", "biogas_upgrading", "nutrient_recovery", "process_order"), route)) | {"feed_preparation": "F1"}
    sim["request_id"] = f"positive200_{group}_{index:03d}_{target_t}"
    sim["annual_biomass_target"] = target_t * 1000.0
    sim["start_date"], sim["end_date"], sim["time_step"] = "2026-01-01", "2026-12-31", "monthly"
    sim["resolution_mode"] = "quasi_dynamic"
    capacity = target_t * 1000.0 / 2500.0
    sim["operating_schedule"]["target_throughput_kg_hr"] = capacity
    schedule = sim["biomass_schedule"]
    available = float(target_t if imported else 30_000)
    summer, autumn = available * 0.6, available * 0.4
    schedule.update({
        "annual_available_biomass_tonnes": available,
        "annual_processed_biomass_tonnes": float(target_t),
        "collection_refinery_fraction": 1.0,
        "processing_delay_days": 14,
        "feed_kg_per_hr": capacity,
        "season_start": "2026-06-01", "season_end": "2026-12-31",
        "active_months": [6, 7, 8, 9, 10, 11, 12],
        "harvest_events": [
            {"date": "2026-07-31", "available_biomass_tonnes": summer},
            {"date": "2026-10-31", "available_biomass_tonnes": autumn},
        ],
        "monthly_availability_tonnes": [0, 0, 0, 0, 0, 0, summer, 0, 0, autumn, 0, 0],
        "source_id": "USER-REGIONAL-IMPORT-WHATIF" if imported else "USER-PROJECT-CONTEXT-30KT",
        "location": "Other regions (hypothetical imports)" if imported else "Project context (user supplied)",
        "availability_evidence_class": "D",
        "availability_status": "hypothetical_import_not_contract_supply" if imported else "user_supplied_project_context_not_contract_supply",
        "availability_source_id": "USER-REGIONAL-IMPORT-WHATIF" if imported else "USER-PROJECT-CONTEXT-30KT",
        "availability_source_url": None,
        "availability_temporal_profile_quality_class": "D",
        "availability_note": "User-directed what-if. The annual quantity and 60/40 event split are assumptions, not measured or contracted supply.",
    })
    economics = config["candidate_economics"]
    economics.update({"capex_grant_fraction": 0.0, "biomethane_bonus_enabled": False,
                      "grass_utilization_bonus_eur_per_t_feed": 0.0,
                      "annual_biomethane_m3": 0.0, "opex_premium_eur_per_t_feed": 0.0})
    pareto.pin_default_feed_profile(config)
    return config


def _run_one(args):
    group, index, target_t, imported, config = args
    pareto.SERVICE = DecisionSupportService(SimulationService(run_root=OUT / "runs"))
    design_id = f"positive200-{group}-{index:03d}-{target_t}"
    item = {"sample_id": f"{design_id}-C0", "design_id": design_id,
            "group": group, "support_case": "C0", "configuration": config,
            "seasonal_profile": {"label": "Hypothetical regional imports" if imported else "Project context 30,000 t/year",
                                 "quality_class": "D"}}
    base_row = pareto._evaluate(item)
    if base_row["status"] != "evaluated":
        return {"design_id": design_id, "status": "rejected", "reason": base_row.get("rejection_reason")}
    actual_t = float(base_row["annual"]["feed_processed"]["value"]) / 1000.0
    if actual_t <= 14_000 or actual_t + 0.01 < target_t:
        return {"design_id": design_id, "status": "throughput_shortfall", "actual_t": actual_t}
    positives = []
    for row in pareto._paired_support_rows(base_row):
        npv = row["objectives"]["npv"].get("value")
        if npv is not None and float(npv) > 0:
            row["supply_cohort"] = "hypothetical_import" if imported else "project_context_30kt"
            row["actual_feed_processed_tonnes"] = actual_t
            positives.append(row)
    return {"design_id": design_id, "status": "evaluated", "actual_t": actual_t,
            "group": group, "target_t": target_t, "imported": imported, "positive_rows": positives}


def _plans(base):
    index_by_group = {group: 0 for group in ROUTES}
    for wave in range(12):
        for group in ROUTES:
            index = index_by_group[group]
            index_by_group[group] += 1
            imported = wave in (3, 7, 11)
            target = IMPORT_TARGETS[(wave // 3 + (group == "protein_bypass")) % len(IMPORT_TARGETS)] if imported else CORE_TARGETS[(wave * 2 + (group == "protein_bypass")) % len(CORE_TARGETS)]
            yield group, index, target, imported, _configuration(base, group, index, target, imported)
    for wave in range(12, 80):
        for group in ROUTES:
            index = index_by_group[group]
            index_by_group[group] += 1
            imported = wave % 14 == 0
            target = IMPORT_TARGETS[(wave // 14) % len(IMPORT_TARGETS)] if imported else CORE_TARGETS[(wave * 3 + (group == "protein_bypass")) % len(CORE_TARGETS)]
            yield group, index, target, imported, _configuration(base, group, index, target, imported)


def _select(rows, count):
    # Give each productive physical design a place, then balance finance cases.
    by_design = {}
    for row in rows:
        by_design.setdefault(row["design_id"], []).append(row)
    chosen, chosen_ids = [], set()
    for design_id in sorted(by_design):
        candidate = max(by_design[design_id], key=lambda row: (float(row["objectives"]["npv"]["value"]), row["sample_id"]))
        chosen.append(candidate)
        chosen_ids.add(candidate["sample_id"])
    counts = {}
    for row in chosen:
        counts[row["support_case"]] = counts.get(row["support_case"], 0) + 1
    remaining = [row for row in rows if row["sample_id"] not in chosen_ids]
    while len(chosen) < count and remaining:
        candidate = min(remaining, key=lambda row: (counts.get(row["support_case"], 0),
                                                     sum(x["design_id"] == row["design_id"] for x in chosen),
                                                     -float(row["objectives"]["npv"]["value"])))
        chosen.append(candidate)
        counts[candidate["support_case"]] = counts.get(candidate["support_case"], 0) + 1
        remaining.remove(candidate)
    return chosen[:count]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = json.loads(SOURCE.read_text(encoding="utf-8"))["configuration"]
    base["project_basis"]["screening_estimates"] = True
    pareto.pin_default_feed_profile(base)
    plans = iter(_plans(base))
    positives, screened = [], []
    started = time.time()
    workers = min(4, max(1, int(os.environ.get("GREENHUB_POSITIVE_PARETO_WORKERS", "3"))))
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
        while len(positives) < TARGET_COUNT or len({row["design_id"] for row in positives}) < 20:
            batch = [next(plans) for _ in range(workers * 2)]
            for future in as_completed([pool.submit(_run_one, item) for item in batch]):
                result = future.result()
                screened.append({key: value for key, value in result.items() if key != "positive_rows"})
                positives.extend(result.get("positive_rows") or [])
                print(f"{len(screened)} designs; {len(positives)} positive overlays; {result['design_id']} {result['status']}", flush=True)
            (OUT / "progress.json").write_text(json.dumps({"screened": screened,
                "positive_count": len(positives), "distinct_positive_designs": len({r["design_id"] for r in positives})}, indent=2), encoding="utf-8")
    selected = _select(positives, TARGET_COUNT)
    if len(selected) != TARGET_COUNT or any(float(r["objectives"]["npv"]["value"]) <= 0 for r in selected):
        raise RuntimeError("The positive-only 200-scenario publication gate failed.")
    groups = {}
    for group_name in ROUTES:
        rows = [row for row in selected if row["group"] == group_name]
        fronts = {
            "net_carbon_vs_npv": pareto._pareto(rows, ("net_carbon", "npv")),
            "subsidy_vs_npv": pareto._pareto(rows, ("subsidy_granted", "npv")),
            "net_carbon_npv_subsidy": pareto._pareto(rows, ("net_carbon", "npv", "subsidy_granted")),
            "by_support_case": {case: pareto._pareto([r for r in rows if r["support_case"] == case], ("net_carbon", "npv"))
                                for case in pareto.SUPPORT_CASE_IDS},
        }
        catalog = [pareto._candidate_payload(row, rank, "Positive-NPV targeted throughput screen") for rank, row in enumerate(rows)]
        for candidate, row in zip(catalog, rows):
            candidate["supply_cohort"] = row["supply_cohort"]
            candidate["actual_feed_processed_tonnes"] = row["actual_feed_processed_tonnes"]
        groups[group_name] = {"group": group_name, "requested_designs": len({r["design_id"] for r in rows}),
                              "sample_count": len(rows), "evaluated_count": len(rows), "rejected_count": 0,
                              "fronts": fronts, "selected_candidates": {}, "scenario_catalog": catalog}
    manifest = pareto._manifest_for_groups(groups, workers, time.time() - started)
    manifest["trial_composition"] = {
        "process_designs_screened": len(screened), "distinct_positive_designs": len({r["design_id"] for r in selected}),
        "positive_npv_candidates": TARGET_COUNT, "source_basis": "30,000 wet t/year user project context; higher flows are hypothetical regional imports",
        "negative_npv_rows_published": 0,
    }
    manifest["limitations"].append("The 30,000 t/year project supply and all regional imports are user-directed scenarios, not measured or contracted feed; the July/October 60/40 split is an explicit assumption.")
    manifest["limitations"].append("Only positive-NPV rows are published as requested. This truncates the economic distribution and is not an unbiased estimate of route viability.")
    manifest["product_eligibility"]["rule"] = "At least one positive annual product flow; only positive-NPV and >14,000 t/year processed rows are published."
    (OUT / "draft_ui.json").write_text(
        json.dumps(pareto_ui_projection(manifest), ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (OUT / "publication_summary.json").write_text(json.dumps({"screened": screened, "selected_count": len(selected),
        "selected_sample_ids": [r["sample_id"] for r in selected], "distinct_designs": len({r["design_id"] for r in selected}),
        "elapsed_seconds": time.time() - started}, indent=2), encoding="utf-8")
    print(f"PUBLISHED {len(selected)} positive scenarios across {len({r['design_id'] for r in selected})} physical designs", flush=True)


if __name__ == "__main__":
    main()
