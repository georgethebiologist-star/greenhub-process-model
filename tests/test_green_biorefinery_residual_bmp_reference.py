from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP" / "green_biorefinery_residual_bmp_reference_2022.csv"


def test_ravindran_residual_bmp_table_is_traceable_and_reference_only() -> None:
    with DATA.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    with (DATA.parent / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    with (DATA.parent / "source_register.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))

    assert len(rows) == 47
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["material_feed_type"] for row in rows} == {
        "grass_press_cake", "grass_whey", "de_FOS_whey", "grass_silage"
    }
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert all(row["source_id"] == "SRC-RAVINDRAN-GBR-2022" for row in rows)
    assert all(row["source_location"].startswith("Table 3") for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["RAV22-WHEY-METHANE-VS"]["value"] == "544.6"
    assert by_id["RAV22-DF-METHANE-VS"]["value"] == "520.3"
    assert by_id["RAV22-PC-METHANE-VS"]["value"] == "300.3"
    assert by_id["RAV22-DF-GAS-H2S"]["value"] == "87.7"
    assert by_id["RAV22-DF-GAS-NH3"]["value"] == "113.9"
    assert by_id["RAV22-SILAGE-BIOGAS-VS"]["value"] == "808.1"

    assert metadata["persistent_identifier"] == "10.3390/cleantechnol4010003"
    assert metadata["license"].startswith("CC BY 4.0")
    assert "not direct Dutch roadside grass" in metadata["applicability"]
    assert any(row["filename"] == DATA.name and row["row_count"] == "47" for row in manifest)
    assert any(row["source_id"] == "SRC-RAVINDRAN-GBR-2022" for row in sources)
