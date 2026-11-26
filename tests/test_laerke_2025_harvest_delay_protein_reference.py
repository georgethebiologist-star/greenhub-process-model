from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "storage"
FILE_NAME = "grass_clover_harvest_delay_digestible_protein_laerke_2025_abstract_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_laerke_abstract_values_are_traceable_sparse_and_reference_only() -> None:
    rows = _rows(DATA_DIR / FILE_NAME)
    sidecar = json.loads((DATA_DIR / f"{FILE_NAME}.source.json").read_text(encoding="utf-8"))
    assert len(rows) == sidecar["rows"] == 16
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC-LAERKE-2025-HARVEST-DELAY"}
    assert {row["evidence_class"] for row in rows} == {"B_abstract_only_primary_literature"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["persistent_identifier"] == "doi:10.1016/j.anifeedsci.2025.116336"
    assert sidecar["readiness"] == "D3"
    assert sidecar["license"].startswith("CC BY 4.0")
    assert "available on request" in sidecar["source_data_availability"]

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["LAERKE25-SIDCP-MOWED-0H"]["reported_value"] == "71.0"
    assert by_id["LAERKE25-SIDCP-CHOPPED-0H"]["reported_value"] == "69.2"
    assert by_id["LAERKE25-DCPYIELD-MOWED-0H"]["reported_value"] == "56.8"
    assert by_id["LAERKE25-DCPYIELD-MOWED-12H"]["reported_value"] == "43.4"
    assert by_id["LAERKE25-DCPYIELD-CHOPPED-12H"]["reported_value"] == "29.4"
    assert by_id["LAERKE25-SIDCP-DELAY-EFFECT-P"]["reported_value"] == "0.005"
    assert by_id["LAERKE25-SIDCP-HARVEST-METHOD-EFFECT-P"]["reported_value"] == "0.006"

    not_reported = [row for row in rows if row["data_status"] == "tested_value_not_reported_in_abstract"]
    assert len(not_reported) == 7
    assert all(row["reported_value"] == "" for row in not_reported)
    assert {row["delay_after_harvest_h"] for row in not_reported} & {"6", "12"}
    assert all("reference_only" in row["activation_state"] for row in rows)
    assert "no parameter" in sidecar["limitations"][0]


def test_laerke_source_and_manifest_registration() -> None:
    source = next(
        row for row in _rows(DATA_DIR / "source_register.csv")
        if row["source_id"] == "SRC-LAERKE-2025-HARVEST-DELAY"
    )
    assert source["doi_or_stable_identifier"] == "10.1016/j.anifeedsci.2025.116336"
    assert "abstract-level" in source["source_type"]

    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    entry = next(row for row in manifest if row["filename"] == FILE_NAME)
    assert entry["row_count"] == "16"
    assert entry["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    assert entry["primary_key"] == "observation_id"
