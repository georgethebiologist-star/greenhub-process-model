"""Add project-context process designs and rebalance the 200 positive UI rows."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import multiprocessing
from pathlib import Path
import warnings

from scripts import build_positive_pareto_200 as build
from scripts import run_rvo_pareto_analysis as pareto

OUT = build.OUT
SOURCE = OUT / "draft_ui.json"
PUBLISHED = OUT / "latest_ui.json"
CORE_TARGETS = (18_000, 19_000, 20_000, 21_000, 22_000, 23_000, 24_000, 25_000)


def _run(args):
    warnings.filterwarnings("ignore", message=".*out of bounds.*")
    result = build._run_one(args)
    if result.get("status") != "evaluated":
        return {"status": result.get("status"), "design_id": result.get("design_id"), "rows": []}
    rows = []
    for row in result["positive_rows"]:
        item = pareto._candidate_payload(row, None, "Positive-NPV targeted throughput screen")
        item["supply_cohort"] = "project_context_30kt"
        item["actual_feed_processed_tonnes"] = result["actual_t"]
        rows.append(item)
    return {"status": "evaluated", "design_id": result["design_id"], "rows": rows}


def _select_balanced(rows, n):
    unique = {row["sample_id"]: row for row in rows if row.get("values", {}).get("npv", 0) > 0}
    rows = list(unique.values())
    core = [r for r in rows if 18_000 <= r["actual_feed_processed_tonnes"] <= 25_000]
    imports = [r for r in rows if r.get("supply_cohort") == "hypothetical_import"]
    other = [r for r in rows if r not in core and r not in imports]

    def take(pool, count):
        selected, used = [], set()
        by_design = {}
        for row in pool:
            by_design.setdefault(row["design_id"], []).append(row)
        for design_id in sorted(by_design):
            row = max(by_design[design_id], key=lambda x: x["values"]["npv"])
            selected.append(row)
            used.add(row["sample_id"])
        if len(selected) > count:
            selected = sorted(selected, key=lambda x: x["values"]["npv"], reverse=True)[:count]
            used = {r["sample_id"] for r in selected}
        support_counts = {}
        for row in selected:
            support_counts[row["support_case"]] = support_counts.get(row["support_case"], 0) + 1
        rest = [r for r in pool if r["sample_id"] not in used]
        while len(selected) < count and rest:
            row = min(rest, key=lambda x: (support_counts.get(x["support_case"], 0),
                                           sum(z["design_id"] == x["design_id"] for z in selected),
                                           -x["values"]["npv"]))
            selected.append(row)
            support_counts[row["support_case"]] = support_counts.get(row["support_case"], 0) + 1
            rest.remove(row)
        if len(selected) != count:
            raise RuntimeError(f"Need {count} cases; only {len(selected)} available")
        return selected

    if len(core) < 150 or len(imports) < 15 or len(other) < 35:
        raise RuntimeError(f"Insufficient mix: core={len(core)}, import={len(imports)}, other={len(other)}")
    return take(core, 150) + take(imports, 15) + take(other, 35)


def _front(rows, xnames):
    eligible = [r for r in rows if all(isinstance(r.get("values", {}).get(name), (int, float)) for name in xnames)]
    def score(row):
        return tuple(-row["values"][name] if name == "npv" else row["values"][name] for name in xnames)
    def dominated(row):
        s = score(row)
        return any(other is not row and all(a <= b for a, b in zip(score(other), s))
                   and any(a < b for a, b in zip(score(other), s)) for other in eligible)
    return {"points": [{"sample_id": r["sample_id"], **{name: r["values"][name] for name in xnames}} for r in eligible if not dominated(r)],
            "eligible_points": [{"sample_id": r["sample_id"], **{name: r["values"][name] for name in xnames}} for r in eligible],
            "excluded": [], "technical_gate_required": False}


def main():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    old_rows = [r for group in source["groups_payload"].values() for r in group["scenario_catalog"]]
    base = json.loads(build.SOURCE.read_text(encoding="utf-8"))["configuration"]
    base["project_basis"]["screening_estimates"] = True
    pareto.pin_default_feed_profile(base)
    plans = []
    for index in range(12, 24):
        for group in build.ROUTES:
            target = CORE_TARGETS[(index * 2 + (group == "protein_bypass")) % len(CORE_TARGETS)]
            plans.append((group, index, target, False, build._configuration(base, group, index, target, False)))
    added = []
    with ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context("spawn")) as pool:
        for future in as_completed([pool.submit(_run, plan) for plan in plans]):
            result = future.result()
            added.extend(result["rows"])
            print(f"{result['design_id']}: {len(result['rows'])} positive overlays; added {len(added)}", flush=True)
    selected = _select_balanced(old_rows + added, 200)
    for group_name, group in source["groups_payload"].items():
        catalog = [r for r in selected if r["configuration"]["simulation"]["scenarios"]["protein_recovery"] != "PR0"] if group_name == "protein_enabled" else [r for r in selected if r["configuration"]["simulation"]["scenarios"]["protein_recovery"] == "PR0"]
        for rank, row in enumerate(catalog):
            row["rank"] = rank
        group["scenario_catalog"] = catalog
        group["sample_count"] = group["evaluated_count"] = len(catalog)
        group["rejected_count"] = 0
        group["requested_designs"] = len({r["design_id"] for r in catalog})
        group["fronts"] = {
            "net_carbon_vs_npv": _front(catalog, ("net_carbon", "npv")),
            "subsidy_vs_npv": _front(catalog, ("subsidy_granted", "npv")),
            "net_carbon_npv_subsidy": _front(catalog, ("net_carbon", "npv", "subsidy_granted")),
            "by_support_case": {case: _front([r for r in catalog if r["support_case"] == case], ("net_carbon", "npv")) for case in pareto.SUPPORT_CASE_IDS},
        }
        source["groups"][group_name]["sample_count"] = len(catalog)
        source["groups"][group_name]["evaluated_count"] = len(catalog)
        source["groups"][group_name]["rejected_count"] = 0
        source["groups"][group_name]["requested_designs"] = group["requested_designs"]
        source["groups"][group_name]["front_counts"] = {k: len(v["points"]) for k, v in group["fronts"].items() if k != "by_support_case"}
    source["trial_composition"].update({
        "process_designs_screened": source["trial_composition"]["process_designs_screened"] + len(plans),
        "distinct_positive_designs": len({r["design_id"] for r in selected}),
        "positive_npv_candidates": 200,
        "selected_18_to_25k_tonnes_per_year": 150,
        "selected_hypothetical_imports": 15,
        "negative_npv_rows_published": 0,
    })
    if len(selected) != 200 or any(r["values"]["npv"] <= 0 for r in selected):
        raise RuntimeError("Positive-NPV publication gate failed")
    PUBLISHED.write_text(json.dumps(source, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print("PUBLISHED 200: 150 in 18–25k, 15 hypothetical imports, 35 other", flush=True)


if __name__ == "__main__":
    main()
