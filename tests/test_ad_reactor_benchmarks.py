from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AD_REACTOR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD reactor"


def _rows(filename: str) -> list[dict[str, str]]:
    with (AD_REACTOR / filename).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_brown_juice_reactor_benchmarks_are_separate_and_traceable():
    rows = _rows("brown_juice_reactor_benchmarks.csv")
    assert len(rows) == 5
    assert len({row["benchmark_id"] for row in rows}) == len(rows)
    assert all(row["source_id"] == "SRC011" for row in rows)
    assert all(row["doi_or_stable_id"] == "10.1007/s13762-017-1637-z" for row in rows)
    assert all(row["source_location"] == "Abstract" for row in rows)
    assert all(row["data_quality_class"] == "B" for row in rows)


def test_continuous_uasb_results_are_not_misclassified_as_bmp():
    rows = _rows("brown_juice_reactor_benchmarks.csv")
    continuous = [row for row in rows if row["operating_mode"] == "continuous"]
    assert len(continuous) == 4
    assert all(row["reactor_configuration"] == "UASB" for row in continuous)
    assert all(row["hydraulic_retention_time"] == "3" for row in continuous)
    assert all(row["organic_loading_rate"] == "13.9" for row in continuous)
    assert any(
        row["metric_id"] == "continuous_methane_yield"
        and row["value"] == "307"
        and row["unit"] == "L CH4/kg VS"
        for row in continuous
    )
    assert not any(row["metric_id"] == "batch_bmp" for row in continuous)
    batch = next(row for row in rows if row["metric_id"] == "batch_bmp")
    assert batch["value_type"] == "reported_upper_result"
    assert batch["operating_mode"] == "batch"


def test_brown_juice_benchmarks_do_not_change_the_existing_default_bmp():
    existing = {row["parameter_id"]: row for row in _rows("../Feed BMP/ad_bmp_observations.csv")}
    assert existing["BMP_DFOS_VS"]["value"] == "520.28"
    assert "BJR-MTZ-2018" not in existing


def test_reactor_benchmark_is_listed_as_report_only():
    manifest = {row["filename"]: row for row in _rows("dataset_manifest.csv")}
    assert manifest["brown_juice_reactor_benchmarks.csv"]["row_count"] == "5"
    assert manifest["brown_juice_reactor_benchmarks.csv"]["integration_status"] == "report_only_literature_benchmark"
    sources = {row["source_id"]: row for row in _rows("source_register.csv")}
    assert sources["SRC011"]["doi_or_stable_id"] == "10.1007/s13762-017-1637-z"
    assert sources["SRC011"]["year"] == "2018"


def test_reactor_benchmark_is_findable_in_fair_asset_catalog():
    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv"
    with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
        assets = list(csv.DictReader(handle))
    asset = next(
        row for row in assets
        if row["relative_path"] == "Greenhub/data/Bigas production + upgrade/AD reactor/brown_juice_reactor_benchmarks.csv"
    )
    assert asset["readiness"] == "report_only_literature_benchmark"
    assert "10.1007/s13762-017-1637-z" in asset["source_dois"]
    assert asset["source_metadata_status"] == "linked_to_source_register"
