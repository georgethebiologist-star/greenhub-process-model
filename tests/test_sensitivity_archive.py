import gzip
import json
from pathlib import Path

from Greenhub.sensitivity_archive import (
    LEGACY_ARCHIVE_NAME,
    ReportShardWriter,
    iter_report_records,
    report_archives,
    write_report_records,
)
from scripts.reprice_sensitivity_report_economics import reprice_record


def test_legacy_archive_is_repacked_into_verified_bounded_shards(tmp_path: Path):
    records = [{"sample": index, "result": {"value": index * 2}} for index in range(7)]
    legacy = tmp_path / LEGACY_ARCHIVE_NAME
    with gzip.open(legacy, "wt", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")

    paths = write_report_records(tmp_path, iter_report_records(tmp_path), records_per_archive=3)

    assert [path.name for path in paths] == [
        "all_endpoint_reports_001.jsonl.gz",
        "all_endpoint_reports_002.jsonl.gz",
        "all_endpoint_reports_003.jsonl.gz",
    ]
    assert not legacy.exists()
    assert all(path.stat().st_size < 95 * 1024 * 1024 for path in paths)
    assert list(iter_report_records(tmp_path)) == records


def test_report_shard_writer_appends_and_rotates_without_losing_rows(tmp_path: Path):
    initial = [{"sample": index} for index in range(3)]
    write_report_records(tmp_path, initial, records_per_archive=2)

    with ReportShardWriter(tmp_path, records_per_archive=2) as writer:
        writer.write(json.dumps({"sample": 3}) + "\n")
        writer.write(json.dumps({"sample": 4}) + "\n")

    assert [row["sample"] for row in iter_report_records(tmp_path)] == [0, 1, 2, 3, 4]
    assert len(report_archives(tmp_path)) == 3


def test_saved_economics_reprice_separates_sales_bonus_and_public_support():
    report = {
        "configuration": {"candidate_economics": {
            "grass_utilization_bonus_eur_per_t_feed": 10,
            "grass_utilization_bonus_years": 2,
            "project_lifetime_years": 2,
            "discount_rate": 0,
            "tax_rate": 0,
        }},
        "annual": {"feed_processed": {"value": 2_000_000}, "utilities": {}, "balance": {}},
        "tea": {
            "totals": {
                "annual_revenue_eur": 100,
                "annual_opex_eur": 25,
                "high_direct_capex_eur": 1_000,
                "partial_direct_capex_eur": 1_000,
                "screening_capital_basis_eur": 1_000,
                "revenue_status": "complete",
            },
            "capex_lines": [], "opex_lines": [], "financial_kpis": {},
        },
        "objectives": {"operating_profit": {}, "npv": {}, "subsidy_granted": {}},
    }
    record = {
        "configuration": report["configuration"], "report": report,
        "summary": {"status": "evaluated"},
    }

    updated = reprice_record(record)

    totals = updated["report"]["tea"]["totals"]
    assert totals["annual_gross_profit_eur"] == 75
    assert totals["grass_utilization_bonus_eur_per_year"] == 20_000
    assert totals["operating_profit_including_grass_bonus_excluding_public_support_eur_per_year"] == 20_075
    assert totals["total_public_support_pv_eur"] == 0
    assert totals["proxy_npv_without_public_support_eur"] == 39_150
    assert totals["proxy_npv_without_public_support_or_grass_bonus_eur"] == -850

    local = {
        "configuration": updated["configuration"],
        "report": updated["report"],
        "input": {"status": "evaluated"},
    }
    local_updated = reprice_record(local)
    assert local_updated["input"]["operating_profit_eur_y"] == 20_075
    assert local_updated["input"]["product_sales_margin_eur_y"] == 75
