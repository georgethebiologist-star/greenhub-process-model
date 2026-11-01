"""Export a compact, traceable UI snapshot from the saved BioSTEAM batch."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH_DIR = ROOT / "Greenhub" / "results" / "actual_pareto_2000" / "decision_batches"
JOB_ID = (BATCH_DIR / "job.txt").read_text(encoding="utf-8").strip()
job = json.loads((BATCH_DIR / f"{JOB_ID}.json").read_text(encoding="utf-8"))


def objective_point(sample):
    objectives = sample.get("outputs", {}).get("objectives", {})
    profit = objectives.get("operating_profit", {})
    climate = objectives.get("climate", {})
    if sample.get("status") != "evaluated" or not all(
        item.get("eligible") and isinstance(item.get("value"), (int, float))
        for item in (profit, climate)
    ):
        return None
    return {
        "sample_id": sample["sample_id"],
        "source_sample_id": sample.get("source_sample_id"),
        "x": profit["value"],
        "y": climate["value"],
    }


def compact_line(line, amount_key, unit):
    return {
        "area": line.get("process_area"),
        "step": line.get("process_step"),
        "item": line.get("equipment_or_cost_item"),
        "cost_type": line.get("cost_type"),
        "amount": line.get(amount_key),
        "unit": unit,
    }


samples = {row["sample_id"]: row for row in job["samples"]}
eligible = [point for row in job["samples"] if (point := objective_point(row))]
front = [
    point for point in eligible
    if not any(
        other["sample_id"] != point["sample_id"]
        and other["x"] >= point["x"]
        and other["y"] <= point["y"]
        and (other["x"] > point["x"] or other["y"] < point["y"])
        for other in eligible
    )
]

# Keep the same evenly spaced cloud for a light preview, while adding every
# true full-batch frontier point so the displayed Pareto curve is not sampled away.
cloud = [point for point in eligible if int(point["sample_id"].rsplit("-", 1)[-1]) % 8 == 1]
plot_ids = {point["sample_id"] for point in cloud + front}
scenario_details = []
for sample_id in sorted(plot_ids, key=lambda value: int(value.rsplit("-", 1)[-1])):
    row = samples[sample_id]
    outputs = row["outputs"]
    tea = outputs.get("tea", {})
    totals = tea.get("totals", {})
    total_fields = (
        "total_direct_capex_eur", "partial_direct_capex_eur", "partial_installed_capex_eur",
        "total_installed_capex_eur", "annual_opex_eur", "annual_revenue_eur",
        "partial_operating_margin_eur_per_year", "capex_status", "opex_status",
        "revenue_status", "profit_status", "optimization_savings_eur_per_year",
        "optimization_revenue_uplift_eur_per_year", "subsidy_eur",
        "subsidy_adjusted_capex_eur", "tax_eur_per_year",
        "optimized_after_tax_profit_eur_per_year", "optimization_status",
    )
    scenario_details.append({
        "sample_id": sample_id,
        "source_sample_id": row.get("source_sample_id"),
        "configuration": row.get("configuration", {}),
        "objectives": {
            "operating_profit": outputs["objectives"]["operating_profit"]["value"],
            "climate_load": outputs["objectives"]["climate"]["value"],
        },
        "feasibility": {
            "numerical_checks_passed": (outputs.get("feasibility") or {}).get("numerical_checks_passed"),
            "route_compatible": (outputs.get("feasibility") or {}).get("route_compatible"),
            "storage_blocker_count": len((outputs.get("feasibility") or {}).get("storage_blockers", [])),
        },
        "products": [
            {
                "product_id": product.get("product_id"),
                "stream_id": product.get("stream_id"),
                "mass_flow": {
                    "value": (product.get("mass_flow") or {}).get("value"),
                    "unit": (product.get("mass_flow") or {}).get("unit"),
                },
                "classification": product.get("classification"),
            }
            for product in outputs.get("products", [])
        ],
        "tea": {
            "totals": {key: totals.get(key) for key in total_fields},
            "capex_lines": [compact_line(line, "direct_cost_eur", "EUR") for line in tea.get("capex_lines", [])],
            "opex_lines": [compact_line(line, "annual_cost_eur", "EUR/year") for line in tea.get("opex_lines", [])],
            "revenue_lines": [compact_line(line, "annual_revenue_eur", "EUR/year") for line in tea.get("revenue_lines", [])],
            "missing_input_count": len(tea.get("missing_inputs", [])),
        },
    })

payload = {
    "job_id": JOB_ID,
    "status": job.get("status"),
    "requested_count": job.get("requested_count"),
    "completed_count": job.get("completed_count"),
    "failed_count": job.get("failed_count"),
    "scenario_count": len(eligible),
    "seed": job.get("seed"),
    "sampling_method": job.get("sampling_method"),
    "created_at": job.get("created_at"),
    "source_provenance": (job["samples"][0].get("outputs", {}).get("provenance", {}).get("process", {})),
    "cloud": cloud,
    "front": front,
    "scenarios": scenario_details,
    "climate_objective": "Attributional climate load; minimize. Substitution credits are excluded from this objective.",
    "economics": {
        "tax_rate": 0.258,
        "subsidy_rate": 0.2,
        "subsidy_cap_eur": 250000.0,
        "eligible_capex_fraction": 0.35,
    },
}
target = ROOT / "frontend" / "src" / "data" / "actualParetoPreview.json"
temporary = target.with_suffix(".json.tmp")
temporary.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")
temporary.replace(target)
print(json.dumps({"job_id": JOB_ID, "scenarios": len(eligible), "plotted": len(plot_ids), "front": len(front), "fixture_bytes": target.stat().st_size}))
