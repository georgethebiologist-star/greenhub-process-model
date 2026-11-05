"""Refresh Pareto provenance/report metadata without changing any model values."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_rvo_pareto_analysis import ECONOMIC_DEFAULTS, LCA_BASIS, FINANCIAL_BASIS

OUT = ROOT / "Greenhub" / "results" / "pareto_rvo_2026"
HEAT = ECONOMIC_DEFAULTS["environment"]["heatKgCo2eKwh"]


def update_heat(record: dict) -> None:
    if record.get("factor_id") != "heat" or record.get("value") is None:
        return
    if abs(float(record["value"]) - float(HEAT["value"])) > 1e-12:
        return
    record.update({
        "quantity_unit": "kWh",
        "source_status": "direct_literature",
        "basis": HEAT["basis"],
        "geography": HEAT["geography"],
        "reference_year": HEAT["reference_year"],
        "source_url": "; ".join(HEAT["source_urls"]),
        "source_table_page": HEAT["source_table_page"],
        "retrieval_date": HEAT["retrieval_date"],
        "evidence_class": "B",
        "applicability": HEAT["applicability"],
        "conversion_method": HEAT["conversion_method"],
        "uncertainty": HEAT["uncertainty"],
        "warning": "Average 2022 Dutch heat-grid factor; not a supplier-specific plant factor.",
    })


def visit(value) -> None:
    if isinstance(value, dict):
        update_heat(value)
        for child in value.values():
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)


def publish(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    manifest_path = OUT / "rvo_pareto_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["grass_utilization_bonus"] = {
        "label": "Grass utilization/logistics bonus",
        "rates_eur_per_wet_tonne": ECONOMIC_DEFAULTS["grass_utilization_bonus"]["test_levels_eur_per_wet_tonne"],
        "duration_years": FINANCIAL_BASIS["project_lifetime_years"],
        "status": "User-defined hypothetical support; not an awarded subsidy",
        "basis": "Rate × annual wet tonnes actually processed; post-route economics only; no process chemistry, balances, or emissions change.",
    }
    manifest["carbon_basis"]["heat_factor_kg_co2e_kwh"] = HEAT["value"]
    manifest["lca_project_basis"]["inventory_completeness"]["heat"]["note"] = (
        "Modeled annual heat activity; CE Delft 2022 Dutch end-user heat-grid average applied (B literature evidence; not site-specific)."
    )
    manifest["limitations"] = [
        "CAPEX grant fractions and €0–50/wet t grass-use bonuses are user-defined what-if values, not awards or verified programme eligibility determinations.",
        "The operating-support overlay uses candidate-specific modeled biomethane volume × the assumed €1.87/Nm³ average; €1.28–€2.46/Nm³ is a sensitivity range, not a verified SDE++ tariff or guaranteed award.",
        "RVO DEI+ eligibility, eligible cost base, grant ceiling and co-funding conditions are not assessed.",
        "RVO SDE++ support is modeled for 15 years without official annual market corrections or an eligibility test.",
        "CAPEX is high direct uninstalled screening cost; installation and unpriced/uncosted components may be missing.",
        "OPEX remains partial; NPV is an after-tax screening proxy under shared Configure assumptions, not an investment-grade forecast.",
        "Climate inventory includes modeled process emissions and life-cycle electricity/heat factors; other upstream/downstream burdens remain excluded.",
        "Net carbon includes assumed furniture and soil carbon retention; manufacturing loss and end-of-life release are not represented.",
        "Pareto fronts describe only the sampled feasible configurations and are not global optima.",
    ]

    for group, batch in manifest["groups_payload"].items():
        visit(batch)
        batch_path = OUT / f"{group}_batch.json"
        publish(batch_path, batch)
        manifest["groups"][group].update({
            "sample_count": batch["sample_count"],
            "evaluated_count": batch["evaluated_count"],
            "rejected_count": batch["rejected_count"],
            "front_counts": {name: len(front.get("points", [])) for name, front in batch["fronts"].items() if name != "by_support_case"},
            "support_front_counts": {case: len(front.get("points", [])) for case, front in batch["fronts"]["by_support_case"].items()},
        })
    visit(manifest)
    publish(manifest_path, manifest)
    publish(OUT / "latest.json", manifest)
    print("Updated provenance and screening limitations; scientific outputs unchanged.")


if __name__ == "__main__":
    main()
