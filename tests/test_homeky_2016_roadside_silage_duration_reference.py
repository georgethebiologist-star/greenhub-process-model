from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
CSV_PATH = DATA / "roadside_grass_silage_duration_codigestion_homeky_2016_abstract_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_homeky_abstract_data_is_traceable_sparse_and_reference_only() -> None:
    rows = _rows(CSV_PATH)
    assert len(rows) == 3
    assert len({row["observation_id"] for row in rows}) == 3
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_abstract_only_primary_literature"}
    assert {row["source_id"] for row in rows} == {"SRC-HOMEKY-ROADSIDE-ENSILING-DURATION-2016"}

    by_duration = {int(row["storage_duration_weeks"]): row for row in rows}
    assert set(by_duration) == {3, 8, 36}
    assert {duration: int(row["storage_duration_days"]) for duration, row in by_duration.items()} == {
        3: 21,
        8: 56,
        36: 252,
    }
    assert {
        duration: int(row["relative_change_percent_vs_slurry_only_control"])
        for duration, row in by_duration.items()
    } == {3: -14, 8: -5, 36: 15}
    assert all(row["reported_yield_unit"] == "L CH4/kg VS added" for row in rows)
    assert all(row["replicate_count"] == "2" for row in rows)
    assert all(row["additional_inoculum"] == "none" for row in rows)
    assert all("absolute methane yield" in row["uncertainty"] for row in rows)
    assert all("do not calibrate" in row["transfer_and_scope_note"].lower() for row in rows)

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.1002/ep.12361"
    assert sidecar["activation_state"] == "reference_only"
    assert sidecar["data_scope"].startswith("Three abstract-reported relative methane-yield changes")
    assert any("do not isolate" in limit for limit in sidecar["limitations"])

    manifest = {row["filename"]: row for row in _rows(DATA / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "3"
    assert manifest[CSV_PATH.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    sources = {row["source_id"]: row for row in _rows(DATA / "source_register.csv")}
    assert sources["SRC-HOMEKY-ROADSIDE-ENSILING-DURATION-2016"]["doi_or_stable_identifier"] == "10.1002/ep.12361"
