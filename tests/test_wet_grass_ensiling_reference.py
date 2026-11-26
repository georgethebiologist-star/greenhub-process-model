from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage" / "wet_grass_ensiling_dynamics_reference_2025.csv"
METADATA = DATA.with_suffix(".source.json")


def test_wet_grass_ensiling_observations_are_traceable_and_not_activated() -> None:
    with DATA.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    catalog = json.loads(
        (ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.json").read_text(encoding="utf-8")
    )

    assert len(rows) == 9
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["storage_days"] for row in rows} == {"0", "7", "30", "87", "192"}
    assert all(row["source_id"] == "SRC-WET-GRASS-ENSILING-2024" for row in rows)
    assert all(row["evidence_class"] == "B_measured" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["source_location"].startswith("Table 9") for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["RESCH2025-V1-192"]["dry_matter_loss_pct"] == "13.1"
    assert by_id["RESCH2025-V2-192"]["dry_matter_loss_pct"] == "3.7"
    assert by_id["RESCH2025-V1-192"]["protein_loss_pct"] == "24.5"
    assert by_id["RESCH2025-V2-192"]["protein_loss_pct"] == "10.3"
    assert by_id["RESCH2025-V1-87"]["butyric_acid_g_per_kg_dm"] == "47.8"
    assert by_id["RESCH2025-V2-87"]["butyric_acid_g_per_kg_dm"] == "17.9"

    assert metadata["dataset_id"] == "greenhub:storage:wet-grass-ensiling-dynamics:2025:v1"
    assert metadata["persistent_identifier"] is None
    assert "not roadside grass" in metadata["applicability"]
    assert "No explicit" in metadata["license"]
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"].endswith(DATA.name)
    )
    assert asset["source_metadata_status"] in {"linked_to_source_register", "linked_to_local_source_record"}
    assert "SRC-WET-GRASS-ENSILING-2024" in asset["source_ids"].split(";")
