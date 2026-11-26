"""Refresh saved sensitivity economics without rerunning process simulations."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_greenhub_sensitivity as runner
from Greenhub.application.decision_support_service import _apply_candidate_economics
from Greenhub.sensitivity_archive import (
    iter_report_records,
    write_report_manifest,
    write_report_records,
)


def _saved_capex_unit(tea: dict):
    """Preserve evaluated route CAPEX when unit objects were not archived."""
    totals = tea.get("totals") or {}
    target = totals.get("high_direct_capex_eur")
    if not isinstance(target, (int, float)):
        return ()
    direct = sum(
        float(line["direct_cost_eur"])
        for line in tea.get("capex_lines") or []
        if isinstance(line.get("direct_cost_eur"), (int, float))
    )
    missing_basis = float(target) - direct
    if missing_basis <= 1e-6:
        return ()
    working_volume_m3 = missing_basis / 300.0
    return (SimpleNamespace(
        unit_id="R501",
        design_results={"Working volume": SimpleNamespace(value=working_volume_m3)},
    ),)


def reprice_record(record: dict) -> dict:
    report = record.get("report")
    if not isinstance(report, dict) or not isinstance(report.get("tea"), dict):
        return record
    configuration = deepcopy(record.get("configuration") or report.get("configuration") or {})
    assumptions = configuration.get("candidate_economics") or {}
    annual = report.get("annual") or {}
    source_tea = deepcopy(report["tea"])
    finance = _apply_candidate_economics(
        source_tea, assumptions, annual, _saved_capex_unit(source_tea)
    )
    tea = finance
    totals = tea.get("totals") or {}
    candidate = tea.get("candidate_economics") or {}
    assumptions = deepcopy(candidate.get("assumptions") or assumptions)
    configuration["candidate_economics"] = assumptions
    report["configuration"] = deepcopy(configuration)
    report["tea"] = tea

    objectives = report.setdefault("objectives", {})
    operating_profit = totals.get("operating_profit_including_grass_bonus_excluding_public_support_eur_per_year")
    if "operating_profit" in objectives:
        objectives["operating_profit"].update({
            "value": operating_profit,
            "definition": "Product sales plus the separate user-defined grass logistics bonus, less partial OPEX; excludes public grants/biomethane support, tax and capital recovery.",
        })
    if "npv" in objectives:
        objectives["npv"].update({
            "value": totals.get("proxy_npv_eur"),
            "definition": totals.get("proxy_npv_basis"),
        })
    if "subsidy_granted" in objectives:
        objectives["subsidy_granted"].update({
            "value": totals.get("total_public_support_pv_eur"),
            "definition": "Hypothetical CAPEX grants and biomethane/other public operating support; grass logistics bonus is separate operating income and excluded.",
        })

    record["configuration"] = configuration
    record["report"] = report
    summary_key = "summary" if "summary" in record else "input"
    summary = dict(record.get(summary_key) or {})
    summary.update(runner.objective_extract(report))
    summary.update({
        "product_sales_margin_eur_y": totals.get("annual_gross_profit_eur"),
        "grass_logistics_operating_income_eur_y": totals.get("grass_utilization_bonus_eur_per_year"),
        "operating_profit_including_grass_bonus_eur_y": operating_profit,
        "npv_without_public_support_or_grass_bonus_eur": totals.get("proxy_npv_without_public_support_or_grass_bonus_eur"),
    })
    record[summary_key] = summary
    record["numeric_endpoints"] = runner.flatten_numeric(report)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_folder", type=Path)
    args = parser.parse_args()
    run_dir = args.run_folder.resolve()
    status_path = run_dir / "run_status.json"
    metadata = json.loads(status_path.read_text(encoding="utf-8"))
    count = 0
    rows = []
    endpoints: dict[str, dict] = {}
    units: dict[str, str] = {}
    rng = random.Random(int(metadata.get("seed", 20261106)))

    def refreshed_records():
        nonlocal count
        for record in iter_report_records(run_dir):
            record = reprice_record(record)
            count += 1
            if isinstance(record.get("summary"), dict):
                rows.append(record["summary"])
            for path, value in (record.get("numeric_endpoints") or {}).items():
                runner.update_endpoint_stats(endpoints, path, float(value), rng)
            if isinstance(record.get("report"), dict):
                units.update(runner.find_endpoint_units(record["report"]))
            yield record

    archives = write_report_records(run_dir, refreshed_records())
    metadata["completed_count"] = count
    metadata["failed_count"] = sum(row.get("status") != "evaluated" for row in rows)
    metadata["finance_accounting_basis"] = (
        "Product-sales margin is sales minus partial OPEX; operating profit adds the separate grass logistics bonus; "
        "public grants and biomethane support are excluded from operating profit. NPV without public support retains the grass bonus."
    )
    runner.write_progress(run_dir, rows, endpoints, run_dir, metadata)
    (run_dir / "endpoint_units.json").write_text(
        json.dumps(units, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    runner.make_figures(run_dir, rows)
    manifest = write_report_manifest(run_dir, count)
    print(json.dumps({
        "repriced_records": count,
        "archive_shards": [{"file": path.name, "size_bytes": path.stat().st_size} for path in archives],
        "archive_manifest": manifest,
        "no_process_simulations_repeated": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
