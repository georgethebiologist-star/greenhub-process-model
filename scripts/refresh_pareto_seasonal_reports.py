"""Refresh saved Pareto monthly schedules from the current UI simulation service.

Only the annual biomass_schedule report is replaced. Process, TEA, LCA,
objective, configuration, and scenario identifiers are checked and preserved.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Greenhub.application.decision_support_service import DecisionSupportService
from Greenhub.application.simulation_service import SimulationService
from Greenhub.pareto_reporting import load_pareto_group
import scripts.run_rvo_pareto_analysis as runner


SOURCE = ROOT / "Greenhub" / "results" / "pareto_rvo_2026"
MAX_BYTES = 100 * 1024 * 1024
CORE_TOTALS = (
    "annual_revenue_eur", "annual_opex_eur", "high_direct_capex_eur",
    "total_public_support_pv_eur", "proxy_npv_eur", "proxy_irr",
    "proxy_simple_payback_years",
)


def same_number(left, right):
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) <= max(0.01, abs(float(right)) * 1e-10)


def assert_process_parity(saved, replay):
    for key in CORE_TOTALS:
        if not same_number((saved.get("tea_totals") or {}).get(key),
                           (replay.get("tea", {}).get("totals") or {}).get(key)):
            raise AssertionError(f"{saved['sample_id']} changed {key}; refusing to publish")
    for key in ("net_carbon", "npv", "subsidy_granted", "climate"):
        expected = (saved.get("objectives") or {}).get(key, {}).get("value")
        actual = (replay.get("objectives") or {}).get(key, {}).get("value")
        if not same_number(expected, actual):
            raise AssertionError(f"{saved['sample_id']} changed objective {key}; refusing to publish")
    annual = saved.get("annual") or {}
    replay_annual = replay.get("annual") or {}
    for collection, keys in (
        ("products", ("protein_product", "biomethane", "press_cake")),
        ("utilities", ("electricity", "heating", "cooling", "fresh_water", "fresh_water_mass")),
    ):
        for key in keys:
            left = ((annual.get(collection) or {}).get(key) or {}).get("value")
            right = ((replay_annual.get(collection) or {}).get(key) or {}).get("value")
            if not same_number(left, right):
                raise AssertionError(f"{saved['sample_id']} changed {collection}.{key}; refusing to publish")


def main():
    original_projection = json.loads((SOURCE / "latest_ui.json").read_text(encoding="utf-8"))
    original_ids = {
        group: {
            "catalog": [row.get("sample_id") for row in
                        (original_projection.get("groups_payload", {}).get(group, {}).get("scenario_catalog") or [])],
            "selected": {
                key: [row.get("sample_id") for row in rows]
                for key, rows in (original_projection.get("groups_payload", {}).get(group, {}).get("selected_candidates") or {}).items()
            },
        }
        for group in ("protein_enabled", "protein_bypass")
    }
    scratch = ROOT / ".codex_tmp"
    scratch.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="pareto-seasonal-refresh-", dir=scratch) as temp:
        stage = Path(temp)
        counts = {}
        rows_by_group = {}
        for group_name in ("protein_enabled", "protein_bypass"):
            group = load_pareto_group(SOURCE, group_name)
            rows = group.get("samples") or []
            by_design = {}
            for row in rows:
                if row.get("status") != "evaluated" or not row.get("annual"):
                    continue
                design_id = row["design_id"]
                config = row["configuration"]
                comparable = deepcopy(config)
                comparable.pop("candidate_economics", None)
                prior = by_design.get(design_id)
                if prior and prior["comparable"] != comparable:
                    raise AssertionError(f"Support variants differ in process inputs for {design_id}")
                by_design.setdefault(design_id, {"row": row, "comparable": comparable})

            refreshed = {}
            for design_id, item in by_design.items():
                row = item["row"]
                with TemporaryDirectory(prefix="greenhub-seasonal-refresh-") as run_dir:
                    service = DecisionSupportService(SimulationService(run_root=Path(run_dir)))
                    replay = service.evaluate(row["configuration"])
                assert_process_parity(row, replay)
                schedule = replay.get("annual", {}).get("biomass_schedule") or {}
                months = schedule.get("monthly") or []
                if not months or not schedule.get("annual_operating_hours"):
                    raise AssertionError(f"No operational monthly schedule for {design_id}")
                for month in months:
                    residual = month.get("storage_mass_residual_tonnes")
                    if residual is not None and abs(float(residual)) > 1e-7:
                        raise AssertionError(f"Storage inventory does not close for {design_id}/{month.get('time_label')}")
                refreshed[design_id] = schedule

            for row in rows:
                schedule = refreshed.get(row.get("design_id"))
                if schedule is not None:
                    row.setdefault("annual", {})["biomass_schedule"] = schedule

            group["samples"] = rows
            runner._write_group_batch_shards(group, stage / f"{group_name}_batch.json")
            counts[group_name] = {"samples": len(rows), "physical_designs": len(refreshed)}
            rows_by_group[group_name] = {row["sample_id"]: row for row in rows}

        # Refresh just seasonal detail in the already-selected UI records.
        # Do not rerank fronts or alter sample membership/order.
        projection = deepcopy(original_projection)
        for group_name in counts:
            ui_group = projection["groups_payload"][group_name]
            row_map = rows_by_group[group_name]
            candidate_sets = [ui_group.get("scenario_catalog") or []]
            candidate_sets.extend((ui_group.get("selected_candidates") or {}).values())
            for candidate_set in candidate_sets:
                for candidate in candidate_set:
                    sample = row_map.get(candidate.get("sample_id"))
                    if sample is None:
                        raise AssertionError(f"UI candidate has no saved sample: {candidate.get('sample_id')}")
                    current = runner._candidate_payload(
                        sample, candidate.get("rank"), candidate.get("selection_basis")
                    )
                    for key in ("seasonal_feed_profile", "ending_inventory_tonnes", "annual_processing_operating_hours"):
                        candidate[key] = current.get(key)
        projection_path = stage / "latest_ui.json"
        projection_path.write_text(json.dumps(projection, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        if projection_path.stat().st_size > MAX_BYTES:
            raise AssertionError("Updated UI projection exceeds 100 MiB")
        for group_name in counts:
            published_group = projection["groups_payload"][group_name]
            catalog_ids = [row.get("sample_id") for row in published_group.get("scenario_catalog") or []]
            selected_ids = {
                key: [row.get("sample_id") for row in rows]
                for key, rows in (published_group.get("selected_candidates") or {}).items()
            }
            if catalog_ids != original_ids[group_name]["catalog"] or selected_ids != original_ids[group_name]["selected"]:
                raise AssertionError(f"Pareto scenario selections changed for {group_name}")
        for group_name in counts:
            manifest_path = stage / f"{group_name}_batch.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files = [manifest_path, *(stage / name for name in manifest.get("sample_shards", []))]
            for artifact in files:
                if artifact.stat().st_size > MAX_BYTES:
                    raise AssertionError(f"Artifact exceeds 100 MiB: {artifact.name}")

        # Publish only after all staged data passed parity and size checks.
        destinations = []
        for group_name in counts:
            manifest = json.loads((stage / f"{group_name}_batch.json").read_text(encoding="utf-8"))
            destinations.append((stage / f"{group_name}_batch.json", SOURCE / f"{group_name}_batch.json"))
            destinations.extend((stage / name, SOURCE / name) for name in manifest.get("sample_shards", []))
        destinations.extend((projection_path, SOURCE / name) for name in
                            ("latest.json", "latest_ui.json", "rvo_pareto_manifest.json"))
        destinations.append((projection_path, ROOT / "frontend" / "public" / "data" / "greenhub-pareto-latest.json"))
        for source, target in destinations:
            if source.stat().st_size > MAX_BYTES:
                raise AssertionError(f"Refusing to publish oversized artifact: {source.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        print(json.dumps({"refreshed": counts, "projection_bytes": projection_path.stat().st_size,
                          "scenario_ids_preserved": True, "process_and_economic_results_preserved": True}, indent=2))


if __name__ == "__main__":
    main()
