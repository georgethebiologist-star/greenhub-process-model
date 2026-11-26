from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "Greenhub"
    / "data"
    / "Bigas production + upgrade"
    / "Feed BMP"
)
CSV_PATH = DATA / "bedoić_residue_grass_field_and_AD_reference_2019.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_residue_grass_field_and_ad_observations_are_traceable_and_reference_only() -> None:
    rows = _rows(CSV_PATH)
    metadata = json.loads(CSV_PATH.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["observation_id"]: row for row in rows}

    assert len(rows) == 46
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC-BEDOIC-2019"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["evidence_class"].startswith("B_") for row in rows)
    assert {row["phase"] for row in rows} == {"1", "5"}

    assert by_id["BEDOIC19-RG1-YIELD"]["reported_value"] == "0.74"
    assert by_id["BEDOIC19-RG1-YIELD"]["reported_sd"] == "0.14"
    assert by_id["BEDOIC19-RG2-YIELD"]["unit"] == "kg fresh matter/m2"
    assert by_id["BEDOIC19-RG3-MOISTURE"]["reported_value"] == "77.5"
    assert by_id["BEDOIC19-RG2-ASH-TS"]["basis"] == "dry matter"

    expected_bmp = {
        "BEDOIC19-MRG1-BMP": "0.2750",
        "BEDOIC19-MRG2-BMP": "0.1921",
        "BEDOIC19-MRG3-BMP": "0.2552",
    }
    for observation_id, expected in expected_bmp.items():
        assert by_id[observation_id]["reported_value"] == expected
        assert by_id[observation_id]["unit"] == "Nm3/kg TS"
        assert "not continuous AD" in by_id[observation_id]["limitations"]

    assert by_id["BEDOIC19-KDIS"]["reported_value"] == "0.17"
    assert by_id["BEDOIC19-KDIS"]["source_location"] == "Table 6; fit to MRG2"
    assert by_id["BEDOIC19-MRG1-BGP-ADM"]["reported_value"] == "0.3578"
    assert "21.9%" in by_id["BEDOIC19-MRG1-BGP-ADM"]["limitations"]
    assert "0.9%" in by_id["BEDOIC19-MRG2-BGP-ADM"]["limitations"]

    assert metadata["dataset_rows"] == len(rows)
    assert metadata["doi"] == "10.1016/j.jclepro.2018.12.224"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["runtime_parameter_mapping"] is None
    assert metadata["retrieval_date"] == "2026-11-07"
    assert any("Table 6" in location for location in metadata["source_locations"])
    assert "empty uncertainty is not zero" in metadata["uncertainty"]


def test_residue_grass_reference_is_registered_in_local_global_and_fair_indexes() -> None:
    filename = CSV_PATH.name
    local_source_register = _rows(DATA / "source_register.csv")
    local_manifest = _rows(DATA / "dataset_manifest.csv")
    global_source_register = _rows(
        ROOT / "Greenhub" / "data" / "global_audit_package" / "global_source_register.csv"
    )
    global_manifest = _rows(
        ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv"
    )
    fair_catalog = _rows(
        ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv"
    )

    assert any(row["source_id"] == "SRC-BEDOIC-2019" for row in local_source_register)
    local = next(row for row in local_manifest if row["filename"] == filename)
    assert local["row_count"] == "46"
    assert local["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    global_source = next(
        row for row in global_source_register if row["source_id"] == "SRC-BEDOIC-2019"
    )
    assert global_source["doi_or_stable_id"] == "10.1016/j.jclepro.2018.12.224"
    global_dataset = next(row for row in global_manifest if row["filename"] == filename)
    assert global_dataset["row_count_observed"] == "46"

    fair = next(row for row in fair_catalog if row["relative_path"].endswith(filename))
    assert fair["observed_rows"] == "46"
    assert fair["source_ids"] == "SRC-BEDOIC-2019"
    assert "10.1016/j.jclepro.2018.12.224" in fair["source_dois"]
