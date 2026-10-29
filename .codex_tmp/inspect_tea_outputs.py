from __future__ import annotations

from collections import Counter
from pathlib import Path

from Greenhub.application.contracts import SCHEMA_VERSION, ScenarioSelection, SimulationRequest
from Greenhub.application.dynamic_complete_reporting_service import build_scenario_summary
from Greenhub.application.simulation_service import SimulationService
from Greenhub.application.tea_service import calculate_dynamic_tea, calculate_empirical_tea
from Greenhub.parameters import CalculationMode, ResolutionMode


def summarize(label: str, report) -> None:
    payload = report.to_dict()
    print(f"\n=== {label} ===")
    print("route", payload["route_summary"].get("scenario_ids") or payload["route_summary"].get("selected_methods"))
    print("totals", payload["totals"])
    print("financial_kpis", payload["financial_kpis"])
    print("warnings")
    for warning in payload["warnings"]:
        print("-", warning)
    print("selected lines", len(payload["selected_cost_lines"]))
    print("capex", len(payload["capex_lines"]), "opex", len(payload["opex_lines"]), "revenue", len(payload["revenue_lines"]))
    print("missing count", len(payload["missing_inputs"]))
    print("missing codes", dict(Counter(item["code"] for item in payload["missing_inputs"])))
    print("missing by cost")
    for item in payload["missing_inputs"][:40]:
        print("-", item.get("cost_id"), item.get("process_area"), item.get("process_step"), item.get("code"), item.get("required_input"))
    print("calculated opex lines")
    for line in payload["opex_lines"]:
        if line.get("annual_cost_eur") is not None:
            print("-", line["cost_id"], line["process_area"], line["process_step"], line["annual_cost_eur"], line.get("quantity"), line.get("quantity_unit"))
    print("calculated capex lines")
    for line in payload["capex_lines"]:
        if line.get("installed_cost_eur") is not None:
            print("-", line["cost_id"], line["process_area"], line["process_step"], line["installed_cost_eur"])
    print("revenue lines")
    for line in payload["revenue_lines"]:
        print("-", line.get("cost_id"), line.get("annual_revenue_eur"), line.get("calculation_status"))


service = SimulationService(run_root=Path(".codex_tmp") / "tea-inspect-run")
request = SimulationRequest(
    SCHEMA_VERSION,
    "tea-inspect-empirical",
    "greenhub-tea-inspect",
    calculation_mode=CalculationMode.STRUCTURAL,
    resolution_mode=ResolutionMode.STEADY_STATE,
    scenarios=ScenarioSelection(
        feed_preparation="F2",
        protein_recovery="PR1",
        anaerobic_digestion="AD1",
        biogas_upgrading="BG2",
        nutrient_recovery="NR2",
        process_order="A",
    ),
)
empirical_result = service.execute_run(service.create_run(request))
summarize("empirical_F2_PR1_AD1_BG2_NR2", calculate_empirical_tea(empirical_result))

dynamic_result = build_scenario_summary({"active_months": [5]})
summarize("dynamic_proxy_May_water_scrubbing", calculate_dynamic_tea(dynamic_result))
