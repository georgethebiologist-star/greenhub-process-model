"""Matched-basis structural route comparisons; no economic or LCA ranking."""
from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

from Greenhub.application.decision_support_service import DecisionSupportService, default_configuration
from Greenhub.application.simulation_service import SimulationService

OUT = Path(__file__).resolve().parent
CASES = (
    ("baseline_F2_PR3_AD1_BG2_NR4_A", {}),
    ("no_targeted_nutrients", {"nutrient_recovery": "NR0", "process_order": "D"}),
    ("struvite_only", {"nutrient_recovery": "NR2", "process_order": "A"}),
    ("ammonium_only", {"nutrient_recovery": "NR3", "process_order": "A"}),
)

def main():
    service = DecisionSupportService(SimulationService(run_root=OUT / "comparison_runs"))
    rows = []
    for case_id, overrides in CASES:
        config = deepcopy(default_configuration())
        config["simulation"]["request_id"] = case_id
        config["simulation"]["scenarios"].update(overrides)
        try:
            report = service.evaluate(config)
            (OUT / (case_id + ".json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
            annual = report["annual"]
            row = {"case_id": case_id, "run_id": report["run_id"], **config["simulation"]["scenarios"],
                   "feed_kg_year": annual["feed_processed"]["value"],
                   "electricity_kwh_year": annual["utilities"]["electricity"]["value"],
                   "heating_kwh_year": annual["utilities"]["heating"]["value"],
                   "mass_residual_kg_year": annual["balance"]["process_mass_residual_kg"],
                   "warning_count": len(report["warnings"]),
                   "installed_capex_eur": report["tea"]["totals"].get("total_installed_capex_eur"),
                   "npv_eur": report["tea"]["financial_kpis"].get("npv_eur"),
                   "climate_kg_co2e_year": report["lca"]["totals"].get("climate_kg_co2e_per_year")}
            row.update({k+"_kg_year": v["value"] for k, v in annual["products"].items()})
            rows.append(row)
            print(case_id, "OK", flush=True)
        except Exception as exc:
            rows.append({"case_id": case_id, "error": str(exc)})
            print(case_id, "FAILED", str(exc), flush=True)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / "route_comparison.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader(); writer.writerows(rows)

if __name__ == "__main__": main()
