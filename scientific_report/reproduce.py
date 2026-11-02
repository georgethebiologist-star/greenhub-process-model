"""Run the unchanged GreenHub decision-support reference and export its evidence."""
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from Greenhub.application.decision_support_service import DecisionSupportService, default_configuration
from Greenhub.application.simulation_service import SimulationService


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def main() -> None:
    OUT.mkdir(exist_ok=True)
    config = default_configuration()
    # A full-calendar-year *steady-state annualization*: July composition and 1000 kg/h
    # are assumed to hold for 8760 h. This is not a seasonal simulation.
    (OUT / "reference_configuration.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    service = DecisionSupportService(SimulationService(run_root=OUT / "model_runs"))
    report = service.evaluate(config)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        commit = "unavailable"
    report["report_package_metadata"] = {"git_commit": commit, "generated_utc": datetime.now(timezone.utc).isoformat()}
    (OUT / "baseline_report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")

    def rows_to_csv(name: str, rows: list[dict]) -> None:
        if not rows:
            return
        keys = list(dict.fromkeys(k for row in rows for k in row))
        with (OUT / name).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})

    annual = report["annual"]
    kpis = [{"section": "annual", "kpi": "feed_processed", **annual["feed_processed"]}]
    for section in ("products", "named_products", "utilities"):
        kpis += [{"section": section, "kpi": k, **v} for k, v in annual[section].items()]
    for section, obj in (("tea", report["tea"]["totals"]), ("lca", report["lca"]["totals"])):
        kpis += [{"section": section, "kpi": k, "value": v, "unit": "see source report"} for k, v in obj.items() if isinstance(v, (int, float)) or v is None]
    rows_to_csv("baseline_kpis.csv", kpis)
    for name, rows in (("products", report["products"]), ("balances", report["balances"]), ("parameter_evidence", report["process_parameter_evidence"]), ("tea_capex", report["tea"].get("capex_lines", [])), ("tea_opex", report["tea"].get("opex_lines", [])), ("tea_revenue", report["tea"].get("revenue_lines", [])), ("lca_inventory", report["lca"].get("inventory", []))):
        rows_to_csv(name + ".csv", rows)
    warnings = Counter(str(x) for x in report["warnings"])
    rows_to_csv("warnings.csv", [{"warning": k, "count": v, "severity": "not classified by model"} for k, v in warnings.items()])
    print(json.dumps({"run_id": report["run_id"], "feed_kg_year": annual["feed_processed"]["value"], "warnings": len(report["warnings"]), "tea_status": report["maturity_summary"]["tea_status"], "lca_status": report["maturity_summary"]["lca_status"]}, indent=2))


if __name__ == "__main__":
    main()
