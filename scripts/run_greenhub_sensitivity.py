"""Evidence-based GreenHub sensitivity analysis on the current seasonal model.

The script reads the current frontend preview configuration and source tables at
runtime, samples explicitly documented ranges, and extracts numeric outputs by
recursive path discovery. It writes full reports as compressed JSONL and updates
summary tables/figures as runs complete, so an interrupted long run is resumable.

Run from the repository root with the project environment:
    .venv/Scripts/python scripts/run_greenhub_sensitivity.py --count 1000
"""
from __future__ import annotations

import argparse
import csv
import gzip
import inspect
import json
import math
import random
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Greenhub.sensitivity_archive import (
    ReportShardWriter,
    iter_report_records,
    report_archives,
    write_report_records,
)

PREVIEW = ROOT / "frontend/public/data/greenhub-default-preview.json"
VARTA = ROOT / "Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_fiber_measurements.csv"
BIOCHEM = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP/ad_biochemical_fractionation.csv"
PRICES = ROOT / "Greenhub/data/tea/netherlands_industrial_product_price_benchmarks.csv"
COMPOSITION = ROOT / "Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json"
MASTER_WORKBOOK = ROOT / "Greenhub/data/greenhub_feed_inputs.xlsx"


def file_sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pin_loaded_workbook_paths(snapshot: Path) -> int:
    """Redirect imported GreenHub workbook constants/defaults to an immutable copy."""
    original = MASTER_WORKBOOK.resolve()
    snapshot = snapshot.resolve()
    changed = 0
    for module_name, module in tuple(sys.modules.items()):
        if not module_name.startswith("Greenhub") or module is None:
            continue
        for name, value in tuple(vars(module).items()):
            if isinstance(value, Path) and value.resolve() == original:
                setattr(module, name, snapshot)
                changed += 1
                continue
            if not inspect.isfunction(value):
                continue
            defaults = value.__defaults__
            if defaults:
                revised = tuple(snapshot if isinstance(item, Path) and item.resolve() == original else item
                                for item in defaults)
                if revised != defaults:
                    value.__defaults__ = revised
                    changed += 1
            kwdefaults = value.__kwdefaults__
            if kwdefaults:
                revised = {key: snapshot if isinstance(item, Path) and item.resolve() == original else item
                           for key, item in kwdefaults.items()}
                if revised != kwdefaults:
                    value.__kwdefaults__ = revised
                    changed += 1
    return changed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(record: dict[str, str], key: str) -> float | None:
    raw = record.get(key)
    if raw in (None, "", "NA", "n/a"):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def source_catalog() -> dict[str, Any]:
    rows = read_csv(VARTA)
    # These are actual 2026 grass/road-verge material samples. Exclude explicit
    # press, process, input/output and product samples for the feed composition.
    feed_rows = []
    for row in rows:
        name = (row.get("sample_name_english") or "").lower()
        if not any(token in name for token in ("grass", "greenhub", "mengselstroom 01a")):
            continue
        if any(token in name for token in ("pressed", "geperst", "processed", "output", "input")):
            continue
        values = {key: number(row, key) for key in (
            "dry_matter_fraction", "nitrogen_g_kg_dm", "phosphorus_g_kg_dm",
            "potassium_g_kg_dm", "crude_protein_g_kg_dm")}
        if all(values[key] is not None for key in ("dry_matter_fraction", "nitrogen_g_kg_dm", "phosphorus_g_kg_dm", "potassium_g_kg_dm")):
            feed_rows.append({"sample": row.get("sample_name_english"), **values})
    protein_rows = [row for row in feed_rows if row["crude_protein_g_kg_dm"] is not None]

    carb_rows = read_csv(BIOCHEM)
    by_season: dict[str, dict[str, float]] = defaultdict(dict)
    for row in carb_rows:
        pid = row.get("parameter_id", "")
        if not pid.startswith("BF_FG-") or not any(x in pid for x in ("CELLULOSE", "HEMICELLULOSE")):
            continue
        season = "spring" if "-Sp_" in pid else "summer" if "-Su_" in pid else "autumn" if "-Au_" in pid else None
        compound = "hemicellulose" if "HEMICELLULOSE" in pid else "cellulose"
        mean = number(row, "normalized_si_value")
        uncertainty = row.get("uncertainty", "")
        # Source records report SD in percentage points. Parse the final number.
        import re
        found = re.search(r"SD\s+([0-9.]+)", uncertainty, re.I)
        if season and mean is not None:
            by_season[season][compound] = mean
            by_season[season][compound + "_sd"] = float(found.group(1)) / 100.0 if found else 0.0
    seasons = [s for s in ("spring", "summer", "autumn") if {"cellulose", "hemicellulose"} <= set(by_season[s])]

    price_map: dict[str, tuple[float, float, str]] = {}
    keys = {
        "Protein product": ("dry_protein_product", 1 / 1000, "EUR/kg"),
        "Biomethane (user all-in direct basis)": ("biomethane", 1.0, "EUR/m3"),
        "Press cake": ("press_cake", 1 / 1000, "EUR/kg"),
        "Ammonium product": ("ammonium_product", 1 / 1000, "EUR/kg"),
        "Phosphorus/struvite product": ("phosphorus_product", 1 / 1000, "EUR/kg"),
        "Potassium concentrate": ("potassium_concentrate", 1 / 1000, "EUR/kg"),
        "Nutrient-rich solids": ("nutrient_rich_solids", 1 / 1000, "EUR/kg"),
    }
    for row in read_csv(PRICES):
        if row.get("product") not in keys:
            continue
        key, factor, model_unit = keys[row["product"]]
        low, high = number(row, "industrial_price_low"), number(row, "industrial_price_high")
        if low is not None and high is not None:
            price_map[key] = (low * factor, high * factor, model_unit, row.get("unit", ""))

    profile = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    base = {key: float(value["wet_mass_fraction"]) for key, value in profile["compounds"].items()}
    base_protein_dm = sum(base[k] for k in ("SolubleProtein", "SuspendedProtein")) / float(profile["dry_matter_fraction"]) * 1000
    base_carb_dm = sum(base[k] for k in ("Cellulose", "Hemicellulose")) / float(profile["dry_matter_fraction"])
    return {
        "varta_feed_samples": feed_rows,
        "varta_protein_samples": protein_rows,
        "carbohydrate_by_season": {season: by_season[season] for season in seasons},
        "carbohydrate_seasons": seasons,
        "price_ranges": {key: {"low": v[0], "high": v[1], "model_unit": v[2], "benchmark_low": number(next(r for r in read_csv(PRICES) if keys.get(r.get("product"), (None,))[0] == key), "industrial_price_low"),
                               "benchmark_high": number(next(r for r in read_csv(PRICES) if keys.get(r.get("product"), (None,))[0] == key), "industrial_price_high"),
                               "benchmark_unit": v[3]} for key, v in price_map.items()},
        "price_keys": {key: key for key in price_map},
        "base_composition": base,
        "base_dry_matter_fraction": float(profile["dry_matter_fraction"]),
        "base_protein_g_per_kg_dm": base_protein_dm,
        "base_cellulose_hemicellulose_fraction_dm": base_carb_dm,
    }


def sample_input(rng: random.Random, catalog: dict[str, Any]) -> dict[str, Any]:
    feed_rows = catalog["varta_feed_samples"]
    nutrients = rng.choice(feed_rows)
    proteins = catalog["varta_protein_samples"]
    protein = rng.choice(proteins)
    season = rng.choice(catalog["carbohydrate_seasons"])
    carb = catalog["carbohydrate_by_season"][season]
    # Reported mean +/- SD, truncated only at the physical zero boundary.
    cellulose = max(0.0, rng.gauss(carb["cellulose"], carb["cellulose_sd"]))
    hemicellulose = max(0.0, rng.gauss(carb["hemicellulose"], carb["hemicellulose_sd"]))
    juice = rng.triangular(0.20, 0.70, 0.457447)
    return {
        "juice_yield_kg_per_kg_wet_feed": juice,
        "protein_g_kg_dm": protein["crude_protein_g_kg_dm"],
        "protein_source_sample": protein["sample"],
        "varta_nutrients_g_kg_dm": {key: nutrients[key] for key in (
            "nitrogen_g_kg_dm", "phosphorus_g_kg_dm", "potassium_g_kg_dm")},
        "nutrient_source_sample": nutrients["sample"],
        "carbohydrate_season_source": season,
        "cellulose_fraction_dm": cellulose,
        "hemicellulose_fraction_dm": hemicellulose,
    }


def configure_sample(base: dict[str, Any], catalog: dict[str, Any], inputs: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    config = json.loads(json.dumps(base))
    sim = config["simulation"]
    composition = dict(sim["feed_composition"])
    dry_matter = catalog["base_dry_matter_fraction"]
    baseline = catalog["base_composition"]

    protein_ids = [key for key in composition if key in ("SolubleProtein", "SuspendedProtein")]
    protein_factor = inputs["protein_g_kg_dm"] / catalog["base_protein_g_per_kg_dm"]
    for key in protein_ids:
        composition[key] = baseline[key] * protein_factor

    carb_ids = [key for key in composition if key in (
        "EntrappedSugars", "Starch", "Cellulose", "Hemicellulose", "Pectin",
        "Glucose", "Fructose", "Sucrose", "Xylose", "Arabinose", "Galactose", "Mannose", "Maltose")]
    base_cell = baseline["Cellulose"] / dry_matter
    base_hemi = baseline["Hemicellulose"] / dry_matter
    sampled_total = inputs["cellulose_fraction_dm"] + inputs["hemicellulose_fraction_dm"]
    base_total = base_cell + base_hemi
    # Preserve the source cellulose:hemicellulose ratio; the source reports
    # both together by season with SDs and does not support other carb splits.
    carb_factor = sampled_total / base_total if base_total else 1.0
    for key in carb_ids:
        composition[key] = baseline[key] * carb_factor

    nutrient_groups = {
        "nitrogen": ("Ammonium", "OrganicNitrogen", "ParticulateNitrogen", "NitrateIon", "NitriteIon"),
        "phosphorus": ("OrganicPhosphorus", "DissolvedPhosphorus", "ParticulatePhosphorus", "Orthophosphate"),
        "potassium": ("ParticulatePotassium", "PotassiumIon"),
    }
    target_map = inputs["varta_nutrients_g_kg_dm"]
    baseline_varta = {"nitrogen": 21.0, "phosphorus": 2.8, "potassium": 29.1}
    for element, ids in nutrient_groups.items():
        value = target_map[{"nitrogen":"nitrogen_g_kg_dm", "phosphorus":"phosphorus_g_kg_dm", "potassium":"potassium_g_kg_dm"}[element]]
        factor = value / baseline_varta[element] if baseline_varta[element] else 1.0
        for key in ids:
            if key in composition:
                composition[key] = baseline[key] * factor

    # Close the measured wet basis while keeping the model's measured moisture
    # fixed and proportionally distributing residual dry matter among other
    # compounds. This is a compositional closure, not a new measurement.
    target_solids = 1.0 - composition.get("Water", 0.0)
    changed = set(protein_ids + carb_ids + [k for ids in nutrient_groups.values() for k in ids])
    changed = {key for key in changed if key in composition}
    changed_total = sum(composition[key] for key in changed)
    other_ids = [key for key in composition if key != "Water" and key not in changed]
    other_total = sum(baseline[key] for key in other_ids)
    residual = max(0.0, target_solids - changed_total)
    if changed_total > target_solids and changed_total > 0:
        factor = target_solids / changed_total
        for key in changed:
            composition[key] *= factor
        residual = 0.0
    if other_total:
        for key in other_ids:
            composition[key] = baseline[key] * residual / other_total
    total = sum(composition.values())
    composition = {key: value / total for key, value in composition.items()}
    sim["feed_composition"] = composition
    sim["calculation_mode"] = "expert_override"
    sim["request_id"] = f"sensitivity-{rng.getrandbits(64):016x}"
    sim["expert_scientific_overrides"] = [{
        "parameter_id": "phase3.juice_yield_kg_per_kg_wet_feed",
        "value": inputs["juice_yield_kg_per_kg_wet_feed"],
        "unit": "kg/kg wet feed",
        "reason": "Sensitivity run; user-requested 0.20–0.70 wet juice yield interval.",
        "requester": "GreenHub sensitivity analysis",
        "provenance_note": "Triangular screening distribution; bounds user-specified, mode based on direct raw-press literature output 34.4/75.2 = 0.457447; not a project calibration.",
    }]

    # Product sale-price ranges come from the maintained Dutch/EU evidence
    # register. Uniform sampling is a transparent screening convention only.
    price_ranges = catalog["price_ranges"]
    prices = config.setdefault("financial_assumptions", {}).setdefault("product_prices", {})
    for key, bounds in price_ranges.items():
        if key in prices and isinstance(prices[key], dict):
            price = rng.uniform(bounds["low"], bounds["high"])
            prices[key]["value_eur_per_unit"] = price
            prices[key]["source_status"] = "evidence_range_uniform_screening"
            prices[key]["basis"] = f"Uniform sensitivity sample within maintained benchmark range, converted to model units: {bounds['low']}–{bounds['high']} {bounds['model_unit']} (original benchmark {bounds['benchmark_low']}–{bounds['benchmark_high']} {bounds['benchmark_unit']}); uniformity is not an empirical probability distribution."
            inputs[f"price_{key}"] = price
    # The user's supplied Dutch support range is a policy/screening assumption.
    economics = config.setdefault("candidate_economics", {})
    economics["biomethane_bonus_eur_per_m3"] = rng.uniform(1.28, 2.46)
    economics["opex_premium_eur_per_nm3_biomethane"] = economics["biomethane_bonus_eur_per_m3"]
    economics["capex_grant_fraction"] = rng.choice([0.0, 0.30, 0.45, 0.60])
    economics["grant_awarding_organization"] = "RVO (hypothetical DEI+ rate; eligibility/award not verified)" if economics["capex_grant_fraction"] else "None (no CAPEX grant)"
    economics["grant_scenario_id"] = {0.0:"C0",0.30:"C30",0.45:"C45",0.60:"C60"}[economics["capex_grant_fraction"]]
    return config


def flatten_numeric(value: Any, prefix: str = "") -> dict[str, float]:
    found: dict[str, float] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ("configuration", "provenance", "process_parameter_evidence", "warnings", "limitations", "readiness", "maturity_summary", "feasibility"):
                continue
            path = f"{prefix}.{key}" if prefix else str(key)
            found.update(flatten_numeric(child, path))
    elif isinstance(value, (list, tuple)):
        # Lists of state snapshots are indexed so every numeric result endpoint
        # can be cataloged without assuming current output schemas.
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            found.update(flatten_numeric(child, path))
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        found[prefix] = float(value)
    return found


def find_endpoint_units(value: Any, prefix: str = "") -> dict[str, str]:
    """Discover numeric value/unit pairs without assuming a fixed report schema."""
    found: dict[str, str] = {}
    if isinstance(value, dict):
        numeric, unit = value.get("value"), value.get("unit")
        if isinstance(numeric, (int, float)) and not isinstance(numeric, bool) and isinstance(unit, str):
            found[f"{prefix}.value" if prefix else "value"] = unit
        for key, child in value.items():
            if key in ("configuration", "provenance", "process_parameter_evidence", "warnings", "limitations", "readiness", "maturity_summary", "feasibility"):
                continue
            path = f"{prefix}.{key}" if prefix else str(key)
            found.update(find_endpoint_units(child, path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.update(find_endpoint_units(child, f"{prefix}[{index}]"))
    return found


def numeric_summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {key: None for key in ("min", "p05", "median", "mean", "p95", "max", "sd")}
    ordered = sorted(values)
    def q(p: float) -> float:
        pos = (len(ordered) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
    mean = sum(ordered) / len(ordered)
    sd = math.sqrt(sum((x - mean) ** 2 for x in ordered) / max(1, len(ordered) - 1))
    return {"min":ordered[0], "p05":q(.05), "median":q(.5), "mean":mean, "p95":q(.95), "max":ordered[-1], "sd":sd}


def objective_extract(report: dict[str, Any]) -> dict[str, Any]:
    annual, tea = (report.get(k) or {} for k in ("annual", "tea"))
    objectives = report.get("objectives") or {}
    totals = tea.get("totals") or {}
    finance = tea.get("financial_kpis") or {}
    lca_totals = (report.get("lca") or {}).get("totals") or {}
    utilities = annual.get("utilities") or {}
    balance = annual.get("balance") or {}
    return {
        "run_id": report.get("run_id"),
        "feed_processed_t_y": ((annual.get("feed_processed") or {}).get("value", 0) or 0) / 1000,
        "npv_eur": (objectives.get("npv") or {}).get("value"),
        "operating_profit_eur_y": (objectives.get("operating_profit") or {}).get("value"),
        "ghg_kg_co2e_y": (objectives.get("climate") or {}).get("value"),
        "net_carbon_t_c_y": (objectives.get("net_carbon") or {}).get("value"),
        "capex_eur": totals.get("total_installed_capex_eur") or totals.get("high_direct_capex_eur"),
        "opex_eur_y": totals.get("annual_opex_eur"),
        "revenue_eur_y": totals.get("annual_revenue_eur"),
        "public_support_pv_eur": totals.get("total_public_support_pv_eur"),
        "annual_support_eur_y": totals.get("annual_operating_support_eur_per_year"),
        "irr_fraction": finance.get("irr"),
        "simple_payback_years": finance.get("simple_payback_years"),
        "npv_without_support_eur": finance.get("npv_without_public_support_eur"),
        "ghg_kg_co2e_per_t_feed": lca_totals.get("kg_co2e_per_tonne_wet_feed"),
        "electricity_mwh_y": ((utilities.get("electricity") or {}).get("value", 0) or 0) / 1000,
        "heat_mwh_y": ((utilities.get("heating") or {}).get("value", 0) or 0) / 1000,
        "cooling_mwh_y": ((utilities.get("cooling") or {}).get("value", 0) or 0) / 1000,
        "mass_closure_pct": balance.get("overall_closure_pct"),
        "technically_eligible": (report.get("feasibility") or {}).get("eligible_for_ranking"),
    }


def update_endpoint_stats(stats: dict[str, dict[str, Any]], path: str, value: float, rng: random.Random, reservoir_size: int = 128) -> None:
    item = stats.setdefault(path, {"count":0,"mean":0.0,"m2":0.0,"min":value,"max":value,"sample":[]})
    item["count"] += 1
    count = item["count"]
    delta = value - item["mean"]
    item["mean"] += delta / count
    item["m2"] += delta * (value - item["mean"])
    item["min"] = min(item["min"], value)
    item["max"] = max(item["max"], value)
    sample = item["sample"]
    if len(sample) < reservoir_size:
        sample.append(value)
    else:
        replacement = rng.randrange(count)
        if replacement < reservoir_size:
            sample[replacement] = value


def write_progress(out_dir: Path, rows: list[dict[str, Any]], endpoints: dict[str, dict[str, Any]], all_reports_path: Path, metadata: dict[str, Any]) -> None:
    with (out_dir / "monte_carlo_kpis.csv").open("w", newline="", encoding="utf-8") as f:
        fields = sorted({key for row in rows for key in row})
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    summaries = {}
    for path, item in endpoints.items():
        if item["count"] < 2: continue
        quantiles = numeric_summary(item["sample"])
        summaries[path] = {"count":item["count"],"min":item["min"],"max":item["max"],"mean":item["mean"],
                           "sd":math.sqrt(item["m2"]/(item["count"]-1)),"p05_reservoir":quantiles["p05"],
                           "median_reservoir":quantiles["median"],"p95_reservoir":quantiles["p95"],
                           "quantile_note":"Exact when count ≤128; otherwise quantiles use a uniform reservoir sample of at most 128 values."}
    (out_dir / "endpoint_summaries.json").write_text(json.dumps(summaries, indent=2, allow_nan=False), encoding="utf-8")
    archives = report_archives(out_dir)
    metadata["report_archives"] = [
        {"file": path.name, "size_bytes": path.stat().st_size}
        for path in archives
    ]
    metadata["report_archive_limit_bytes"] = 95 * 1024 * 1024
    (out_dir / "run_status.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if len(rows) % 25 == 0:
        print(f"Completed {len(rows)} / {metadata['requested_count']}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261106)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--local-only", action="store_true", help="run baseline and one-at-a-time range endpoints")
    parser.add_argument("--time-step", choices=("monthly", "weekly", "daily"), default="monthly",
                        help="seasonal resolution used for every sampled simulation (monthly retains all seasonal months)")
    args = parser.parse_args()
    if not 1 <= args.count <= 10000:
        parser.error("--count must be 1..10000")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = (args.output or ROOT / "results" / "sensitivity_analysis" / f"seasonal_mc_{stamp}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    run_root = out_dir / "temporary_runs"
    run_root.mkdir(exist_ok=True)
    snapshot_dir = out_dir / "input_snapshot"
    snapshot_dir.mkdir(exist_ok=True)
    workbook_snapshot = snapshot_dir / MASTER_WORKBOOK.name
    if not workbook_snapshot.exists():
        shutil.copy2(MASTER_WORKBOOK, workbook_snapshot)
    preview = json.loads(PREVIEW.read_text(encoding="utf-8"))
    base = json.loads(json.dumps(preview["decisionReport"]["configuration"]))
    base.pop("existing_run_id", None)
    base.pop("logistics_result", None)
    base["simulation"].pop("existing_run_id", None)
    base["simulation"]["time_step"] = args.time_step
    catalog = source_catalog()
    rng = random.Random(args.seed)
    rows: list[dict[str, Any]] = []
    endpoints: dict[str, dict[str, Any]] = {}
    endpoint_units: dict[str, str] = {}
    reports_path = out_dir
    legacy_reports = out_dir / "all_endpoint_reports.jsonl.gz"
    if args.resume and legacy_reports.exists():
        write_report_records(out_dir, iter_report_records(out_dir))
    if args.resume and report_archives(out_dir):
        for rec in iter_report_records(out_dir):
            if "summary" in rec:
                rows.append(rec["summary"])
            for path, value in rec.get("numeric_endpoints", {}).items():
                update_endpoint_stats(endpoints,path,float(value),rng)
            if isinstance(rec.get("report"), dict):
                endpoint_units.update(find_endpoint_units(rec["report"]))
    metadata = {
        "schema":"greenhub-sensitivity-run-1.0", "requested_count":args.count, "seed":args.seed,
        "completed_count":len(rows), "sampling":"Monte Carlo with explicit source-based ranges; uniform price and policy intervals are screening samplers, not calibrated probability distributions.",
        "model_configuration_source":str(PREVIEW.relative_to(ROOT)), "seasonal_run":True,
        "time_step":args.time_step, "time_step_note":"Monthly simulations retain calendar-month seasonality; weekly/daily fluctuations are not represented." if args.time_step=="monthly" else "",
        "base_run_id":preview.get("run",{}).get("run_id"), "resolution_mode":base["simulation"].get("resolution_mode"),
        "master_input_workbook_snapshot":str(workbook_snapshot.relative_to(ROOT)),
        "master_input_workbook_sha256":file_sha256(workbook_snapshot),
        "juice_yield_basis":"triangular 0.20–0.70 kg juice/kg wet feed; mode 0.457447 from direct press output 34.4/75.2.",
        "feed_composition_basis":"VARTA 2026 feed sample bootstrap for nutrients and crude protein; roadside-grass literature mean±SD by season for cellulose and hemicellulose; 14.3% dry matter fixed to current measured GreenHub whole-grass profile; non-water closure preserves 100% wet mass.",
        "economic_basis":"Current baseline grants/support eligibility choices plus user-provided C0/C30/C45/C60 grant levels and €1.28–€2.46/Nm³ biomethane premium sensitivity; product market intervals from maintained source register. Uniform/categorical sampling means screening coverage, not frequencies or probabilities.",
        "source_sample_counts":{"varta_feed":len(catalog["varta_feed_samples"]),"varta_protein":len(catalog["varta_protein_samples"]),"carbohydrate_seasons":catalog["carbohydrate_seasons"]},
        "input_distribution_summary":{"protein_samples_g_kg_dm":[r["crude_protein_g_kg_dm"] for r in catalog["varta_protein_samples"]],"carbohydrate_means_sd":catalog["carbohydrate_by_season"],"product_price_ranges":catalog["price_ranges"]},
    }
    (out_dir / "sensitivity_method.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "methodology.md").write_text(
        "# GreenHub sensitivity analysis methodology\n\n"
        "This analysis runs the current model configuration read from `frontend/public/data/greenhub-default-preview.json`; source files are resolved relative to the repository root. The master input workbook is snapshotted under `input_snapshot/` and GreenHub workbook paths are redirected to that immutable copy before model construction, preventing concurrent workbook saves from mixing input versions. The sampled simulations use the quasi-dynamic process model on a monthly calendar grid, preserving seasonal feed availability and monthly variation while omitting within-month weekly fluctuations. Full numeric reports, configurations, and warnings are retained in ordered `all_endpoint_reports_NNN.jsonl.gz` shards, each below 95 MiB; endpoint paths and discovered units are catalogued separately.\n\n"
        "## Input ranges and evidence\n\n"
        "- Juice yield: triangular screening range 0.20–0.70 kg juice/kg wet feed, mode 0.457447, computed from the direct raw-press result 34.4/75.2 in the maintained mechanical-press literature register (Pedersen et al., DOI 10.3390/proteomes13010008). This is a transferability-limited mode, not a roadside-grass calibration.\n"
        "- Protein: empirical resampling of recorded VARTA 2026 crude-protein concentrations in unpressed grass samples; current baseline dry matter is held at the VARTA GreenHub whole-grass value of 14.3%. The small sample count is reported in `sensitivity_method.json`.\n"
        "- Nitrogen, phosphorus, potassium: joint row-wise resampling of VARTA 2026 grass samples, with each element applied as a proportional change to its current model pools.\n"
        "- Cellulose and hemicellulose: seasonal means and standard deviations from the maintained roadside-grass biochemical fractionation dataset (Czubaszek et al., DOI 10.3390/en16114488). A season is selected for range coverage; reported SDs are used as normal screening variation, truncated at zero.\n"
        "- Product prices: sampled inside the low/high intervals in `Greenhub/data/tea/netherlands_industrial_product_price_benchmarks.csv`, converted to the active model units. Uniform sampling is a range-coverage convention, not a market probability distribution.\n"
        "- Biomethane support and CAPEX grants: user-supplied €1.28–€2.46/Nm³ and C0/C30/C45/C60 options are included as policy screening assumptions. Grant levels are category-balanced; neither the category weights nor support rates are award probabilities or eligibility claims.\n\n"
        "Changed feed compounds are compositionally closed to the existing measured moisture and 100% wet-mass basis by proportional scaling of residual solids. This closure preserves the mass basis but is not an additional measurement. Unspecified input correlations are not inferred. Local sensitivity uses actual one-factor endpoint runs; global rank correlations are associations within this screening design, not causal effects. Monte Carlo quantiles are screening ranges and must not be interpreted as confidence intervals.\n",
        encoding="utf-8")

    from Greenhub.application.decision_support_service import DecisionSupportService
    from Greenhub.application.simulation_service import SimulationService
    if args.local_only:
        pin_loaded_workbook_paths(workbook_snapshot)
        return run_local_sensitivity(base, catalog, out_dir, args.seed, workbook_snapshot)
    start = time.monotonic()
    # BioSTEAM global state is guarded by a model lock; this loop is deliberately
    # serial and resumable. Each sample's files are removed after report capture.
    with ReportShardWriter(out_dir) as reports:
        for index in range(len(rows), args.count):
            sample_rng = random.Random(args.seed + index)
            sampled = sample_input(sample_rng, catalog)
            config = configure_sample(base, catalog, sampled, sample_rng)
            case_root = run_root / f"case_{index + 1:04d}"
            service = None
            evaluator = None
            try:
                pin_loaded_workbook_paths(workbook_snapshot)
                service = SimulationService(run_root=case_root)
                evaluator = DecisionSupportService(simulations=service)
                pin_loaded_workbook_paths(workbook_snapshot)
                report = evaluator.evaluate(config)
                flat = flatten_numeric(report)
                endpoint_units.update(find_endpoint_units(report))
                row = {"sample":index + 1, "status":"evaluated", **sampled, **objective_extract(report),
                       "juice_yield":sampled["juice_yield_kg_per_kg_wet_feed"],
                       "protein_multiplier":sampled["protein_g_kg_dm"] / catalog["base_protein_g_per_kg_dm"],
                       "carbohydrate_multiplier":(sampled["cellulose_fraction_dm"] + sampled["hemicellulose_fraction_dm"]) / catalog["base_cellulose_hemicellulose_fraction_dm"],
                       "capex_grant_fraction":config["candidate_economics"]["capex_grant_fraction"],
                       "nitrogen_g_kg_dm":sampled["varta_nutrients_g_kg_dm"]["nitrogen_g_kg_dm"],
                       "phosphorus_g_kg_dm":sampled["varta_nutrients_g_kg_dm"]["phosphorus_g_kg_dm"],
                       "potassium_g_kg_dm":sampled["varta_nutrients_g_kg_dm"]["potassium_g_kg_dm"],
                       "biomethane_bonus_eur_per_m3":config["candidate_economics"]["biomethane_bonus_eur_per_m3"]}
                for path, value in flat.items():
                    update_endpoint_stats(endpoints,path,value,rng)
                reports.write(json.dumps({"sample":index + 1,"summary":row,"inputs":sampled,"configuration":config,
                                          "numeric_endpoints":flat,"report":report}, ensure_ascii=False, allow_nan=False) + "\n")
                reports.flush()
            except Exception as exc:
                row = {"sample":index + 1,"status":"failed",**sampled,"error":f"{type(exc).__name__}: {exc}"}
                reports.write(json.dumps({"sample":index + 1,"summary":row,"inputs":sampled,"error":row["error"]}, ensure_ascii=False) + "\n")
                reports.flush()
            rows.append(row)
            # Release retained result objects and delete only the isolated case
            # directory created by this script.
            if service is not None:
                for run_id in tuple(service.repository.list_ids()):
                    service.repository._runs.pop(run_id, None)
            del evaluator, service
            if case_root.exists():
                shutil.rmtree(case_root)
            metadata["completed_count"] = len(rows)
            metadata["elapsed_seconds"] = round(time.monotonic() - start, 1)
            if len(rows) % 25 == 0 or len(rows) == args.count:
                write_progress(out_dir, rows, endpoints, reports_path, metadata)
    metadata["elapsed_seconds"] = round(time.monotonic() - start, 1)
    metadata["completed_count"] = len(rows)
    metadata["failed_count"] = sum(row.get("status") != "evaluated" for row in rows)
    (out_dir / "endpoint_units.json").write_text(json.dumps(endpoint_units, indent=2, ensure_ascii=False), encoding="utf-8")
    write_progress(out_dir, rows, endpoints, reports_path, metadata)
    make_figures(out_dir, rows)
    print(f"Finished: {len(rows)} runs, {metadata['failed_count']} failed. Results: {out_dir}", flush=True)
    return 0


def run_local_sensitivity(base: dict[str, Any], catalog: dict[str, Any], out_dir: Path, seed: int,
                          workbook_snapshot: Path | None = None) -> int:
    """Actual one-factor-at-a-time endpoint runs, with economic cases reusing the simulated baseline."""
    from Greenhub.application.decision_support_service import DecisionSupportService
    from Greenhub.application.simulation_service import SimulationService
    from copy import deepcopy

    local_dir = out_dir / "local_sensitivity"
    local_dir.mkdir(exist_ok=True)
    run_root = local_dir / "temporary_runs"
    run_root.mkdir(exist_ok=True)
    rng = random.Random(seed)
    baseline_config = deepcopy(base)
    baseline_config["simulation"]["request_id"] = f"sensitivity-local-baseline-{seed}"
    service = SimulationService(run_root=run_root / "baseline")
    evaluator = DecisionSupportService(simulations=service)
    print("Running seasonal baseline for local sensitivity…", flush=True)
    baseline_report = evaluator.evaluate(baseline_config)
    baseline_run_id = baseline_report["run_id"]
    baseline_values = objective_extract(baseline_report)
    rows = [{"case":"baseline","parameter":"baseline","value":"current configuration","status":"evaluated",**baseline_values}]
    cases: list[tuple[str, Any, str]] = []
    cases.extend(("juice yield", value, "kg/kg wet feed") for value in (0.20, 0.70))
    proteins = [row["crude_protein_g_kg_dm"] for row in catalog["varta_protein_samples"]]
    cases.extend(("protein concentration", value, "g/kg DM") for value in (min(proteins), max(proteins)))
    for season in ("spring", "summer", "autumn"):
        item = catalog["carbohydrate_by_season"][season]
        cases.append((f"carbohydrate {season}", item["cellulose"]+item["hemicellulose"], "fraction of dry matter"))
    feed = catalog["varta_feed_samples"]
    for key, label in (("nitrogen_g_kg_dm","N"),("phosphorus_g_kg_dm","P"),("potassium_g_kg_dm","K")):
        cases.extend((f"nutrient {label}", value, "g/kg DM") for value in (min(r[key] for r in feed), max(r[key] for r in feed)))
    cases.extend(("biomethane support", value, "€/Nm³") for value in (1.28, 2.46))
    cases.extend(("CAPEX grant", value, "fraction") for value in (0.0, 0.30, 0.45, 0.60))
    for product, bounds in catalog["price_ranges"].items():
        cases.extend((f"product price {product}", value, bounds["model_unit"]) for value in (bounds["low"], bounds["high"]))

    base_composition = dict(baseline_config["simulation"]["feed_composition"])
    profile_comp = catalog["base_composition"]
    dm = catalog["base_dry_matter_fraction"]
    for index, (parameter, value, unit) in enumerate(cases, 1):
        case_config = deepcopy(baseline_config)
        case_config["simulation"]["request_id"] = f"sensitivity-local-{seed}-{index:03d}"
        case_config["simulation"].pop("expert_scientific_overrides", None)
        if parameter == "juice yield":
            case_config["simulation"]["calculation_mode"] = "expert_override"
            case_config["simulation"]["expert_scientific_overrides"] = [{
                "parameter_id":"phase3.juice_yield_kg_per_kg_wet_feed","value":value,
                "unit":"kg/kg wet feed","reason":"Local sensitivity endpoint from user-specified range.",
                "requester":"GreenHub sensitivity analysis","provenance_note":"User specified 0.20–0.70 interval; direct source is a cross-check, not calibration."}]
        elif parameter == "protein concentration":
            factor=value/catalog["base_protein_g_per_kg_dm"]
            for key in ("SolubleProtein","SuspendedProtein"):
                case_config["simulation"]["feed_composition"][key]=profile_comp[key]*factor
        elif parameter.startswith("carbohydrate"):
            season=parameter.split()[-1]
            entry=catalog["carbohydrate_by_season"][season]
            selected=(entry["cellulose"]+entry["hemicellulose"]) if season != "spring" else value
            factor=selected/catalog["base_cellulose_hemicellulose_fraction_dm"]
            for key in ("EntrappedSugars","Starch","Cellulose","Hemicellulose","Pectin","Glucose","Fructose","Sucrose","Xylose","Arabinose","Galactose","Mannose","Maltose"):
                if key in case_config["simulation"]["feed_composition"]:
                    case_config["simulation"]["feed_composition"][key]=profile_comp.get(key,0)*factor
        elif parameter.startswith("nutrient "):
            element=parameter.split()[-1]
            key_map={"N":("nitrogen_g_kg_dm",("Ammonium","OrganicNitrogen","ParticulateNitrogen","NitrateIon","NitriteIon"),21.0),
                     "P":("phosphorus_g_kg_dm",("OrganicPhosphorus","DissolvedPhosphorus","ParticulatePhosphorus","Orthophosphate"),2.8),
                     "K":("potassium_g_kg_dm",("ParticulatePotassium","PotassiumIon"),29.1)}
            field, pool_ids, base_value=key_map[element]
            factor=value/base_value
            for key in pool_ids:
                if key in case_config["simulation"]["feed_composition"]:
                    case_config["simulation"]["feed_composition"][key]=profile_comp.get(key,0)*factor
        else:
            case_config["existing_run_id"]=baseline_run_id
            case_config["simulation"]["request_id"] = baseline_config["simulation"]["request_id"]
            econ=case_config.setdefault("candidate_economics",{})
            if parameter=="biomethane support":
                econ["biomethane_bonus_eur_per_m3"]=value
                econ["opex_premium_eur_per_nm3_biomethane"]=value
            elif parameter=="CAPEX grant":
                econ["capex_grant_fraction"]=value
                econ["grant_awarding_organization"]="RVO (hypothetical; award eligibility not verified)" if value else "None (no CAPEX grant)"
            elif parameter.startswith("product price "):
                product=parameter.removeprefix("product price ")
                price_key=product if product in catalog["price_ranges"] else None
                if price_key:
                    case_config.setdefault("financial_assumptions",{}).setdefault("product_prices",{})[price_key]["value_eur_per_unit"]=value
        if parameter.startswith(("protein concentration","carbohydrate","nutrient ")):
            comp=case_config["simulation"]["feed_composition"]
            target=1.0-comp.get("Water",0)
            sum_solids=sum(v for k,v in comp.items() if k!="Water")
            if sum_solids:
                scale=target/sum_solids
                for key in comp:
                    if key!="Water": comp[key]*=scale
            case_config.pop("existing_run_id",None)
            # composition edits are independent of the structural juice override
        try:
            report=evaluator.evaluate(case_config)
            row={"case":f"{parameter}={value}","parameter":parameter,"value":value,"unit":unit,"status":"evaluated",**objective_extract(report)}
            rows.append(row)
            with gzip.open(local_dir/"local_reports.jsonl.gz","at" if (local_dir/"local_reports.jsonl.gz").exists() else "wt",encoding="utf-8") as f:
                f.write(json.dumps({"input":row,"report":report},ensure_ascii=False,allow_nan=False)+"\n")
        except Exception as exc:
            rows.append({"case":f"{parameter}={value}","parameter":parameter,"value":value,"unit":unit,"status":"failed","error":f"{type(exc).__name__}: {exc}"})
            print(f"Local case failed ({parameter}={value}): {exc}",flush=True)
        if index % 2 == 0:
            with (local_dir/"local_sensitivity.csv").open("w",newline="",encoding="utf-8") as f:
                fields=sorted({k for r in rows for k in r})
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        print(f"Local sensitivity {index}/{len(cases)}: {parameter}={value}",flush=True)
    with (local_dir/"local_sensitivity.csv").open("w",newline="",encoding="utf-8") as f:
        fields=sorted({k for r in rows for k in r})
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    make_local_tornado(local_dir,rows,baseline_values)
    local_metadata = {
        "analysis": "one_factor_at_a_time_actual_model_runs",
        "seasonal_resolution": f"{base['simulation'].get('time_step', 'monthly')} quasi-dynamic, 2026 calendar seasonality",
        "case_count": len(rows) - 1,
        "evaluated_count": sum(row.get("status") == "evaluated" for row in rows[1:]),
        "failed_count": sum(row.get("status") != "evaluated" for row in rows[1:]),
        "base_configuration": str(PREVIEW.relative_to(ROOT)),
        "baseline_run_id": baseline_run_id,
        "baseline_feed_t_per_year": baseline_values.get("feed_processed_t_y"),
        "baseline_npv_eur": baseline_values.get("npv_eur"),
        "baseline_ghg_kg_co2e_per_year": baseline_values.get("ghg_kg_co2e_y"),
        "npv_tornado": "Percentage change from baseline NPV; economic factors use the saved baseline process result.",
        "emissions_tornado": "Percentage change from baseline attributional GHG; only modeled physical input factors are varied.",
        "parameter_groups": list(dict.fromkeys(row.get("parameter") for row in rows[1:] if row.get("parameter"))),
        "master_input_workbook_snapshot": str(workbook_snapshot.resolve().relative_to(ROOT)) if workbook_snapshot else None,
        "master_input_workbook_sha256": file_sha256(workbook_snapshot) if workbook_snapshot else None,
        "data": "local_sensitivity.csv and local_reports.jsonl.gz",
        "figure": "local_sensitivity_tornado.png",
    }
    (local_dir / "local_sensitivity_method.json").write_text(
        json.dumps(local_metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Local sensitivity finished: {local_dir}",flush=True)
    return 0


def make_local_tornado(local_dir: Path, rows: list[dict[str, Any]], baseline: dict[str, Any]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    parameters=[]
    for row in rows[1:]:
        if row.get("status")!="evaluated": continue
        param=str(row.get("parameter"))
        try: kpi_npv=float(row.get("npv_eur"))
        except (TypeError,ValueError): kpi_npv=None
        try: kpi_ghg=float(row.get("ghg_kg_co2e_y"))
        except (TypeError,ValueError): kpi_ghg=None
        base_npv=baseline.get("npv_eur"); base_ghg=baseline.get("ghg_kg_co2e_y")
        if kpi_npv is not None and isinstance(base_npv,(int,float)) and base_npv:
            npv_pct=100*(kpi_npv-base_npv)/abs(base_npv)
        else: npv_pct=None
        ghg_pct=100*(kpi_ghg-base_ghg)/abs(base_ghg) if kpi_ghg is not None and isinstance(base_ghg,(int,float)) and base_ghg else None
        parameters.append((param,npv_pct,ghg_pct))
    def clean_name(name: str) -> str:
        if name.startswith("carbohydrate "): return "Carbohydrate concentration"
        if name=="nutrient N": return "Nitrogen concentration"
        if name=="nutrient P": return "Phosphorus concentration"
        if name=="nutrient K": return "Potassium concentration"
        if name=="product price dry_protein_product": return "Protein product price"
        if name=="product price press_cake": return "Press cake price"
        if name=="product price ammonium_product": return "Ammonium product price"
        if name=="product price phosphorus_product": return "Phosphorus product price"
        if name=="product price potassium_concentrate": return "Potassium product price"
        if name=="product price nutrient_rich_solids": return "Nutrient solids price"
        if name=="product price biomethane": return "Biomethane price"
        return name.title()
    summaries=[]
    def group_name(raw: str) -> str:
        return "carbohydrate concentration" if raw.startswith("carbohydrate ") else raw
    for name in dict.fromkeys(group_name(item[0]) for item in parameters):
        matching=[item for item in parameters if group_name(item[0])==name]
        npv=[item[1] for item in matching if item[1] is not None]
        ghg=[item[2] for item in matching if item[2] is not None]
        summaries.append((clean_name(name),min(npv) if npv else None,max(npv) if npv else None,min(ghg) if ghg else None,max(ghg) if ghg else None,name))
    if not summaries: return
    fig,axes=plt.subplots(1,2,figsize=(11,max(4.5,.35*len(summaries))),constrained_layout=True)
    for ax,low_i,high_i,title,color in ((axes[0],1,2,"NPV change (%)","#cf6a9b"),(axes[1],3,4,"Emissions change (%)","#3f9456")):
        items=[s for s in summaries if s[low_i] is not None and s[high_i] is not None]
        if title.startswith("Emissions"):
            items=[s for s in items if s[5].startswith(("juice yield","protein concentration","carbohydrate ","nutrient "))]
        else:
            items=[s for s in items if max(abs(s[low_i]),abs(s[high_i]))>0.05]
        items.sort(key=lambda item:max(abs(item[low_i]),abs(item[high_i])))
        for y,item in enumerate(items):
            low,high=item[low_i],item[high_i]
            ax.plot([low,high],[y,y],lw=5,color=color,solid_capstyle="round")
            ax.scatter([low,high],[y,y],s=24,color=color,zorder=3)
        ax.set_yticks(range(len(items)),[item[0] for item in items]); ax.axvline(0,color="#0b3b3e",lw=.8)
        ax.set_xlabel(title); ax.set_title(title); ax.spines[["top","right"]].set_visible(False);ax.grid(axis="x",alpha=.15)
    fig.suptitle("Local sensitivity range endpoints",fontweight="bold",color="#0b3b3e")
    fig.savefig(local_dir/"local_sensitivity_tornado.png",dpi=180,bbox_inches="tight");plt.close(fig)


def make_figures(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        (out_dir / "figure_generation_unavailable.txt").write_text(str(exc), encoding="utf-8")
        return
    usable = [row for row in rows if row.get("status") == "evaluated"]
    if not usable:
        return
    out = out_dir / "figures"
    out.mkdir(exist_ok=True)
    plt.rcParams.update({"figure.dpi":120,"savefig.dpi":160,"font.size":9,"axes.titlesize":11,"axes.labelsize":9})
    palette = {"ink":"#0b3b3e","green":"#3f9456","blue":"#6b9bd2","rose":"#cf6a9b","gold":"#d5a61a","orange":"#b97635"}
    # Global Monte Carlo distributions: paired financial and climate panels.
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.2), constrained_layout=True)
    panels = [("npv_eur","NPV (€)",palette["blue"]),("operating_profit_eur_y","Operating profit incl. grass bonus (€/year)",palette["rose"]),
              ("ghg_kg_co2e_y","Attributional emissions (t CO₂-eq/year)",palette["orange"]),("net_carbon_t_c_y","Net carbon (t C/year)",palette["green"])]
    for ax,(key,label,color) in zip(axes.ravel(),panels):
        values=[float(row[key])/(1000 if key=="ghg_kg_co2e_y" else 1) for row in usable if isinstance(row.get(key),(int,float))]
        if values:
            ax.hist(values,bins=30,color=color,alpha=.84,edgecolor="white",linewidth=.4)
            ax.axvline(float(np.median(values)),color=palette["ink"],lw=1.2,ls="--",label=f"Median {np.median(values):,.2f}")
            ax.set_xlabel(label); ax.set_ylabel("Simulations"); ax.legend(frameon=False,fontsize=8)
            ax.spines[["top","right"]].set_visible(False); ax.grid(axis="y",alpha=.16)
    fig.suptitle("Seasonal Monte Carlo outcomes",color=palette["ink"],fontweight="bold")
    fig.savefig(out/"monte_carlo_kpi_distributions.png",bbox_inches="tight"); plt.close(fig)

    sales_margin = [row.get("product_sales_margin_eur_y") for row in usable]
    operating_profit = [row.get("operating_profit_including_grass_bonus_eur_y") for row in usable]
    paired = [(float(sales), float(profit)) for sales, profit in zip(sales_margin, operating_profit)
              if isinstance(sales, (int, float)) and isinstance(profit, (int, float))]
    if paired:
        fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
        ax.hist([row[0] / 1000 for row in paired], bins=30, color=palette["rose"], alpha=.72,
                label="Product-sales margin before bonus")
        ax.hist([row[1] / 1000 for row in paired], bins=30, color=palette["gold"], alpha=.72,
                label="Operating profit incl. grass bonus")
        ax.axvline(0, color=palette["ink"], lw=1)
        ax.set(xlabel="Annual margin / operating income (€ thousand)", ylabel="Simulations",
               title="Operating profit depends on the grass logistics bonus")
        ax.legend(frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.16)
        fig.savefig(out/"sales_margin_vs_operating_profit.png", bbox_inches="tight")
        plt.close(fig)

    # Multi-objective outputs with support and emissions; retain all samples.
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),constrained_layout=True)
    x=[row.get("public_support_pv_eur") for row in usable]; y=[row.get("npv_eur") for row in usable]
    good=[i for i,(a,b) in enumerate(zip(x,y)) if isinstance(a,(int,float)) and isinstance(b,(int,float))]
    if good:
        colors=[palette["green"] if usable[i].get("net_carbon_t_c_y",0)<=0 else palette["blue"] for i in good]
        axes[0].scatter([x[i] for i in good],[y[i] for i in good],c=colors,s=16,alpha=.62,edgecolors="none")
        axes[0].set(xlabel="Public support PV (€)",ylabel="NPV (€)",title="NPV and public support")
    x=[row.get("ghg_kg_co2e_y") for row in usable]; y=[row.get("npv_eur") for row in usable]
    good=[i for i,(a,b) in enumerate(zip(x,y)) if isinstance(a,(int,float)) and isinstance(b,(int,float))]
    if good:
        axes[1].scatter([x[i]/1000 for i in good],[y[i] for i in good],c=palette["blue"],s=16,alpha=.62,edgecolors="none")
        axes[1].set(xlabel="Emissions (t CO₂-eq/year)",ylabel="NPV (€)",title="NPV and emissions")
    for ax in axes:
        ax.spines[["top","right"]].set_visible(False); ax.grid(alpha=.16)
    fig.savefig(out/"monte_carlo_tradeoffs.png",bbox_inches="tight"); plt.close(fig)

    # Spearman tornado summaries against every numeric input and KPI. These are
    # monotone association screens, not causal effects or calibrated GSA indices.
    input_keys=["juice_yield","protein_multiplier","carbohydrate_multiplier","nitrogen_g_kg_dm","phosphorus_g_kg_dm",
                "potassium_g_kg_dm","capex_grant_fraction","biomethane_bonus_eur_per_m3",
                "price_ammonium_product","price_nutrient_rich_solids","price_biomethane","price_dry_protein_product",
                "price_phosphorus_product","price_potassium_concentrate","price_press_cake"]
    input_labels={"juice_yield":"Juice yield","protein_multiplier":"Protein concentration","carbohydrate_multiplier":"Carbohydrate concentration",
                  "nitrogen_g_kg_dm":"Nitrogen","phosphorus_g_kg_dm":"Phosphorus","potassium_g_kg_dm":"Potassium",
                  "capex_grant_fraction":"CAPEX grant","biomethane_bonus_eur_per_m3":"Biomethane support",
                  "price_ammonium_product":"Ammonium price","price_nutrient_rich_solids":"Nutrient-solids price",
                  "price_biomethane":"Biomethane price","price_dry_protein_product":"Protein price",
                  "price_phosphorus_product":"Phosphorus price","price_potassium_concentrate":"Potassium price","price_press_cake":"Press-cake price"}
    kpis=["npv_eur","operating_profit_eur_y","ghg_kg_co2e_y","net_carbon_t_c_y"]
    try:
        from scipy.stats import spearmanr
        fig,axes=plt.subplots(1,2,figsize=(13,7),constrained_layout=True)
        for ax,kpi,title in zip(axes,["npv_eur","ghg_kg_co2e_y"],["NPV sensitivity","Emissions sensitivity"]):
            corrs=[]
            for key in input_keys:
                pairs=[(float(row[key]),float(row[kpi])) for row in usable if isinstance(row.get(key),(int,float)) and isinstance(row.get(kpi),(int,float))]
                rho=float(spearmanr([a for a,b in pairs],[b for a,b in pairs]).statistic) if len(pairs)>2 else 0
                corrs.append((input_labels.get(key,key.replace("_"," ")),rho))
            if kpi=="ghg_kg_co2e_y":
                corrs=[item for item in corrs if item[0] not in ("CAPEX grant","Biomethane support","Ammonium price","Nutrient-solids price","Biomethane price","Protein price","Phosphorus price","Potassium price","Press-cake price")]
            corrs.sort(key=lambda pair:abs(pair[1]))
            ax.barh([c[0] for c in corrs],[c[1] for c in corrs],color=[palette["green"] if c[1]>=0 else palette["rose"] for c in corrs])
            ax.axvline(0,color=palette["ink"],lw=.8); ax.set_xlim(-1,1); ax.set_xlabel("Spearman ρ"); ax.set_title(title)
            ax.spines[["top","right"]].set_visible(False); ax.grid(axis="x",alpha=.16)
        fig.savefig(out/"global_sensitivity_rank_correlations.png",bbox_inches="tight"); plt.close(fig)
    except ImportError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
