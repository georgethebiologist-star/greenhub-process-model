from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "fen_grass_biorefinery_fractionation_per_harvest_nielsen_2021_tables_3_4_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_nielsen_per_harvest_reference_preserves_streams_and_censored_values() -> None:
    path = DATA / FILENAME
    rows = _rows(path)
    sidecar = json.loads(Path(f"{path}.source.json").read_text(encoding="utf-8"))
    events = {
        (row["species"], row["treatment_harvest_cuts"], row["harvest_index"], row["harvest_week"])
        for row in rows
    }
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == sidecar["record_count"] == 224
    assert len(events) == 28
    assert {row["source_id"] for row in rows} == {"SRC-NIELSEN-2021"}
    assert {row["source_table"] for row in rows} == {"Table 3", "Table 4"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["runtime_parameter_mapping"] is None
    assert sidecar["source_file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    rcg = by_id["NF21-Table3-REED_CANARY_GRASS-2CUT-C1-W24-PLANT_BIOMASS-DM"]
    assert rcg["reported_mean"] == "8.8"
    assert rcg["reported_sd"] == "3.3"
    assert "per-cut rows" in rcg["source_basis_note"]
    concentrate = by_id["NF21-Table3-REED_CANARY_GRASS-3CUT-C1-W20-PROTEIN_CONCENTRATE-CP"]
    assert concentrate["reported_mean_text"] == "0.1"
    assert concentrate["reported_sd_text"] == ">0.0"
    assert concentrate["record_status"] == "reported_mean_sd_at_table_precision_threshold"

    unavailable = by_id["NF21-Table3-REED_CANARY_GRASS-5CUT-C5-W42-PLANT_BIOMASS-DM"]
    assert unavailable["reported_mean"] == ""
    assert unavailable["reported_mean_text"] == "NA"
    assert unavailable["record_status"] == "not_available_source_NA_insufficient_biomass_note"
    assert any("same-source annual rows" in item for item in sidecar["limitations"])

    tf_single = by_id["NF21-Table4-TALL_FESCUE-4CUT-C4-W42-PLANT_BIOMASS-DM"]
    assert tf_single["reported_mean"] == "1.0"
    assert tf_single["reported_sd_text"] == "NA"
    assert tf_single["record_status"] == "mean_reported_sd_unavailable_source_NA_single_replicate"
    tf_unavailable_pulp = by_id["NF21-Table4-TALL_FESCUE-4CUT-C4-W42-PULP-DM"]
    assert tf_unavailable_pulp["reported_mean_text"] == "NA"

    assert any(
        row["file_name"] == FILENAME and row["row_count"] == "224"
        for row in _rows(DATA / "dataset_manifest.csv")
    )
    assert any(row["source_id"] == "SRC-NIELSEN-2021" for row in _rows(DATA / "source_register.csv"))
