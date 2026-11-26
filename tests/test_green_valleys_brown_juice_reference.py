from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD reactor"
DATASET = DATA_DIR / "green_valleys_brown_juice_characterization_and_pilot_profile_2020_reference.csv"
NF_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Membrane"
NF_DATASET = NF_DIR / "green_valleys_brown_juice_nanofiltration_2020_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_green_valleys_brown_juice_data_are_traceable_and_nonactivated():
    rows = _rows(DATASET)
    sidecar = json.loads(DATASET.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = {row["source_id"]: row for row in _rows(DATA_DIR / "source_register.csv")}
    manifest = {row["filename"]: row for row in _rows(DATA_DIR / "dataset_manifest.csv")}

    assert len(rows) == sidecar["rows"] == 32
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC-GREEN-VALLEYS-BJ-2020"}
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert sources["SRC-GREEN-VALLEYS-BJ-2020"]["doi_or_stable_id"] == "not assigned"
    assert sources["SRC-GREEN-VALLEYS-BJ-2020"]["source_url"] == sidecar["source_url"]
    assert manifest[DATASET.name]["row_count"] == "32"
    assert manifest[DATASET.name]["integration_status"] == "reference_only_project_measurements"


def test_brown_juice_bmp_and_pilot_conditions_keep_distinct_boundaries():
    rows = _rows(DATASET)
    bmp = [row for row in rows if row["parameter"] == "batch_methane_potential"]
    assert {(row["value"], row["unit"], row["basis"]) for row in bmp} == {
        ("409.6", "NmL CH4/g VS", "VS fed"),
        ("264.2", "NmL CH4/g COD", "COD fed"),
    }
    assert all(row["process_context"] == "90-day batch digestion test" for row in bmp)
    periods = [row for row in rows if row["parameter"] == "hydraulic_retention_time"]
    assert [(row["sample_or_period"], row["value"]) for row in periods] == [
        ("1", "11"), ("2", "22"), ("3", "11"), ("4", "11"), ("5", "5.5")
    ]
    assert all("not a design recommendation" in row["limitations"] for row in periods)


def test_brown_juice_raw_and_warmed_sample_values_remain_separate():
    rows = _rows(DATASET)
    measured = {
        (row["sample_or_period"], row["parameter"]): row["value"]
        for row in rows
        if row["record_type"] == "juice_characterization"
    }
    assert measured[("fresh_brown_juice", "COD")] == "20.63"
    assert measured[("warmed_brown_juice", "COD")] == "22.51"
    assert measured[("fresh_brown_juice", "volatile_fatty_acids")] == "976"
    assert measured[("warmed_brown_juice", "volatile_fatty_acids")] == "1925"


def test_green_valleys_nanofiltration_trials_and_streams_remain_separate():
    rows = _rows(NF_DATASET)
    sidecar = json.loads(NF_DATASET.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = {row["source_id"]: row for row in _rows(NF_DIR / "source_register.csv")}
    manifest = {row["filename"]: row for row in _rows(NF_DIR / "dataset_manifest.csv")}

    assert len(rows) == sidecar["rows"] == 30
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert sources["SRC-GREEN-VALLEYS-BJ-2020"]["doi_or_stable_id"] == "not assigned"
    assert manifest[NF_DATASET.name]["row_count"] == "30"
    pilot_brix = {
        row["stream"]: row["value"]
        for row in rows
        if row["record_type"] == "stream_chemistry" and row["analyte"] == "Brix"
    }
    assert pilot_brix == {"feed": "4.0", "permeate": "1.1", "concentrate": "15.7"}
    demo_brix = next(
        row["value"] for row in rows
        if row["experiment_context"] == "demo_nf_98_m2" and row["analyte"] == "Brix"
    )
    assert demo_brix == "2.66"
    assert any(row["value"] == "nd" and row["analyte"] == "lactic_acid" for row in rows)
    assert all(row["unit"] == "mg/L" for row in rows if row["analyte"] == "lactic_acid")
