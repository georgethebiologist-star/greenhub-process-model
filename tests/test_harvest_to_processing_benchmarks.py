from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "storage"
DATA = DATA_DIR / "harvest_to_processing_benchmarks.csv"
SOURCE = DATA_DIR / "harvest_to_processing_benchmarks.source.json"
SOURCE_REGISTER = DATA_DIR / "source_register.csv"
FAIR_CATALOG = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv"
CHECKSUMS = ROOT / "Greenhub" / "data" / "global_audit_package" / "source_dataset_checksums.csv"


def test_harvest_delay_observations_are_traceable_and_not_runtime_defaults() -> None:
    with DATA.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(SOURCE.read_text(encoding="utf-8"))

    assert len(rows) == 32
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert all(row["doi"] == "10.3303/CET24109019" for row in rows)
    assert all(row["evidence_class"] == "B_measured" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["source_url"].endswith("/24/109/019.pdf") for row in rows)
    assert metadata["persistent_identifier"] == "10.3303/CET24109019"
    assert "Do not interpolate" in metadata["limitations"]

    explicit_endpoints = {
        row["record_id"]: (row["delay_after_harvest_h"], row["reported_value"])
        for row in rows
        if "CP-RECOVERY" in row["record_id"]
    }
    assert explicit_endpoints == {
        "ANDRADE2024-21-IF-CP-RECOVERY-START": ("0.5", "21.0"),
        "ANDRADE2024-21-IF-CP-RECOVERY-END": ("12", "14.0"),
        "ANDRADE2024-22-IF-CP-RECOVERY-START": ("0.5", "9.2"),
        "ANDRADE2024-22-IF-CP-RECOVERY-END": ("6", "5.5"),
    }

    with SOURCE_REGISTER.open("r", encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    source = next(row for row in source_rows if row["source_id"] == "SRC-GRASS-HARVEST-DELAY-2024")
    assert source["doi_or_stable_identifier"] == "10.3303/CET24109019"

    with FAIR_CATALOG.open("r", encoding="utf-8-sig", newline="") as stream:
        assets = list(csv.DictReader(stream))
    asset = next(row for row in assets if row["relative_path"] == "Greenhub/data/storage/harvest_to_processing_benchmarks.csv")
    assert asset["observed_rows"] == "32"
    assert "10.3303/CET24109019" in asset["source_dois"]

    with CHECKSUMS.open("r", encoding="utf-8-sig", newline="") as stream:
        checksums = list(csv.DictReader(stream))
    checksum = next(row for row in checksums if row["dataset_path"] == "storage/harvest_to_processing_benchmarks.csv")
    assert checksum["sha256"] == asset["sha256"]


def test_harvest_delay_benchmark_does_not_change_runtime_storage_rates() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "Greenhub").rglob("*.py")
    )
    assert "harvest_to_processing_benchmarks.csv" not in source_text
