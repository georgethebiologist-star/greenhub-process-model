"""Combine the verified 30+70 weather-aware trials into a diverse UI catalog.

The source batches remain immutable evidence. The extension batch's new UI
sample IDs are namespaced to avoid collisions with the original design IDs.
No process chemistry, measurements, route IDs, or annual result values change.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Greenhub" / "results" / "pareto_weather_100_designs_2026"
INITIAL = ROOT / "Greenhub" / "results" / "pareto_weather_gas_gate_2026"
EXTENSION = ROOT / "Greenhub" / "results" / "pareto_weather_expansion_2026"
PREVIEW = ROOT / "frontend" / "public" / "data" / "greenhub-pareto-weather-100-designs-2026.json"
os.environ["GREENHUB_PARETO_OUTPUT_DIR"] = str(OUT)
os.environ["GREENHUB_PARETO_DESIGNS"] = "50"
os.environ["GREENHUB_PARETO_SEED"] = "20261109"
sys.path.insert(0, str(ROOT))

from Greenhub.pareto_reporting import load_pareto_group, publish_pareto_ui_artifacts
from scripts.run_rvo_pareto_analysis import (
    SUPPORT_CASE_IDS,
    _grass_bonus_sensitivity,
    _manifest_for_groups,
    _pareto,
    _scenario_catalog,
    _select_3d_ranked,
    _select_ranked,
    _write_group_batch_shards,
)


def _read_manifest(path: Path) -> dict:
    return json.loads((path / "rvo_pareto_manifest.json").read_text(encoding="utf-8"))


def _namespace_extension_row(row: dict, suffix: str) -> dict:
    result = deepcopy(row)
    old_design = str(result["design_id"])
    new_design = f"{old_design}-S{suffix}"
    old_sample = str(result["sample_id"])
    result["design_id"] = new_design
    result["sample_id"] = old_sample.replace(old_design, new_design, 1)
    paired = result.get("paired_process_source_sample_id")
    if paired:
        result["paired_process_source_sample_id"] = str(paired).replace(old_design, new_design, 1)
    simulation = (result.get("configuration") or {}).get("simulation") or {}
    if simulation.get("request_id"):
        simulation["request_id"] = f"{simulation['request_id']}_seed{suffix}"
    return result


def main() -> None:
    first_manifest = _read_manifest(INITIAL)
    extension_manifest = _read_manifest(EXTENSION)
    for field in ("financial_basis", "carbon_basis", "support_scenarios", "biomethane_support_conversion", "grass_utilization_bonus", "product_eligibility"):
        if first_manifest.get(field) != extension_manifest.get(field):
            raise ValueError(f"Source batches differ in their {field}; a combined UI catalog would mix bases.")

    groups: dict[str, dict] = {}
    total_product_eligible_designs = 0
    catalog_design_counts: dict[str, int] = {}
    for group_name in ("protein_enabled", "protein_bypass"):
        original = load_pareto_group(INITIAL, group_name)
        extension = load_pareto_group(EXTENSION, group_name)
        rows = list(original.get("samples") or [])
        for row in rows:
            row["design_cohort"] = "initial_30"
            row["design_cohort_label"] = "Initial 30-design sample"
        extension_rows = [_namespace_extension_row(row, "20261109") for row in (extension.get("samples") or [])]
        for row in extension_rows:
            row["design_cohort"] = "expanded_70"
            row["design_cohort_label"] = "Expanded 70-design screening cohort"
        rows.extend(extension_rows)
        sample_ids = [str(row.get("sample_id") or "") for row in rows]
        if not all(sample_ids) or len(sample_ids) != len(set(sample_ids)):
            raise ValueError(f"Combined {group_name} sample IDs are absent or duplicated.")
        eligible_designs = {row["design_id"] for row in rows if row.get("status") == "evaluated" and row.get("product_gate", {}).get("eligible")}
        total_product_eligible_designs += len(eligible_designs)
        rows.sort(key=lambda row: str(row.get("sample_id") or ""))
        group = {
            "group": group_name,
            "requested_designs": 50,
            "support_cases": list(SUPPORT_CASE_IDS),
            "sample_count": len(rows),
            "evaluated_count": sum(row.get("status") == "evaluated" for row in rows),
            "rejected_count": sum(row.get("status") != "evaluated" for row in rows),
            "samples": rows,
            "fronts": {},
            "selected_candidates": {},
        }
        group["scenario_catalog"] = _scenario_catalog(rows, max_points=100)
        group["fronts"] = {
            "net_carbon_vs_npv": _pareto(rows, ("net_carbon", "npv")),
            "subsidy_vs_npv": _pareto(rows, ("subsidy_granted", "npv")),
            "net_carbon_npv_subsidy": _pareto(rows, ("net_carbon", "npv", "subsidy_granted")),
            "by_support_case": {
                case: _pareto([row for row in rows if row.get("support_case") == case], ("net_carbon", "npv"))
                for case in SUPPORT_CASE_IDS
            },
        }
        three = group["fronts"]["net_carbon_npv_subsidy"]
        subsidy = group["fronts"]["subsidy_vs_npv"]
        group["selected_candidates"] = {
            "net_carbon_vs_npv": _select_3d_ranked(three, rows),
            "net_carbon_npv_subsidy": _select_3d_ranked(three, rows),
            "subsidy_vs_npv": _select_ranked(subsidy, rows, economic_first=True),
            "grass_bonus_sensitivity": _grass_bonus_sensitivity(rows),
            **{
                f"net_carbon_vs_npv_{case}": _select_ranked(
                    front, [row for row in rows if row.get("support_case") == case], economic_first=True
                )
                for case, front in group["fronts"]["by_support_case"].items()
            },
        }
        catalog_design_counts[group_name] = len({row["design_id"] for row in group["scenario_catalog"]})
        groups[group_name] = group

    manifest = _manifest_for_groups(groups, workers=2, elapsed_seconds=0.0)
    manifest.update({
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": 20261109,
        "designs_per_protein_group": 50,
        "trial_composition": {
            "process_designs_screened": 100,
            "initial_designs_screened": 30,
            "expanded_designs_screened": 70,
            "expanded_design_cohort_label": "Expanded 70-design screening cohort; not experimental or field-validated results.",
            "protein_enabled_designs_screened": 50,
            "protein_bypass_designs_screened": 50,
            "product_eligible_distinct_designs": total_product_eligible_designs,
            "unique_designs_in_ui_catalog_by_group": catalog_design_counts,
            "positive_npv_candidates": sum(
                1 for group in groups.values() for row in group["samples"]
                if row.get("status") == "evaluated" and float(row["objectives"]["npv"]["value"]) > 0
            ),
            "source_batches": [
                {"path": INITIAL.relative_to(ROOT).as_posix(), "designs_per_group": 15, "seed": first_manifest.get("seed"),
                 "manifest_sha256": hashlib.sha256((INITIAL / "rvo_pareto_manifest.json").read_bytes()).hexdigest()},
                {"path": EXTENSION.relative_to(ROOT).as_posix(), "designs_per_group": 35, "seed": extension_manifest.get("seed"),
                 "manifest_sha256": hashlib.sha256((EXTENSION / "rvo_pareto_manifest.json").read_bytes()).hexdigest()},
            ],
            "catalog_selection": "One existing finance row per distinct product-eligible process design is selected first; remaining capacity adds finance overlays balanced across support cases.",
            "extension_sample_id_suffix": "-S20261109; original sample and process-route IDs are preserved.",
        },
    })
    manifest["limitations"] = list(manifest.get("limitations") or []) + [
        "This preview combines two independently replayed weather-aware batches (30 initial plus 70 extension process designs). Productless designs remain rejected; UI catalog sample IDs are namespaced only for the extension batch.",
        "The 100 designs use conditional Zeeland regional technical potential, not contracted or site-verified biomass supply; all policy support remains hypothetical.",
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    for group_name, group in groups.items():
        _write_group_batch_shards(group, OUT / f"{group_name}_batch.json")
    publish_pareto_ui_artifacts(manifest, OUT / "latest_ui.json", PREVIEW)
    projection = json.loads((OUT / "latest_ui.json").read_text(encoding="utf-8"))
    for name in ("latest.json", "rvo_pareto_manifest.json"):
        target = OUT / name
        target.write_text(json.dumps(projection, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "process_designs_screened": manifest["trial_composition"]["process_designs_screened"],
        "product_eligible_distinct_designs": total_product_eligible_designs,
        "unique_designs_in_ui_catalog_by_group": catalog_design_counts,
        "positive_npv_candidates": manifest["trial_composition"]["positive_npv_candidates"],
        "projection_bytes": (OUT / "latest_ui.json").stat().st_size,
        "preview_bytes": PREVIEW.stat().st_size,
    }, indent=2))


if __name__ == "__main__":
    main()
