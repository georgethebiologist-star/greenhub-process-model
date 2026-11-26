import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_chiumenti_digestate_dataset_is_traceable_reference_only_and_basis_specific():
    data_dir = ROOT / "Greenhub/data/Resource recovery/Digestate_and_Separation"
    data_path = data_dir / "grass_conservation_digestate_nutrients_chiumenti_2019_reference.csv"
    rows = _rows(data_path)
    assert len(rows) == 47
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["grass_preservation"] for row in rows} == {"fresh", "dried", "ensiled"}
    assert {row["evidence_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["CHIUMENTI19-FRESH-TKN-WET"]["value"] == "3.99"
    assert by_id["CHIUMENTI19-FRESH-TKN-WET"]["basis"] == "wet_digestate"
    assert by_id["CHIUMENTI19-FRESH-TKN-TS"]["unit"] == "percent_TS"
    assert by_id["CHIUMENTI19-ENSILED-VS-REMOVAL"]["value"] == "39.7"
    assert by_id["CHIUMENTI19-DRIED-NH4-REMOVAL"]["value"] == "23.0"
    assert "flow-corrected" in by_id["CHIUMENTI19-FRESH-TKN-REMOVAL"]["limitations"]

    metadata = json.loads(data_path.with_suffix(data_path.suffix + ".source.json").read_text(encoding="utf-8"))
    assert metadata["persistent_identifier"] == "10.3390/en12173244"
    assert metadata["license"] == "CC BY 4.0, as stated in the article"
    assert "differing" in " ".join(metadata["limitations"])
    assert "excluded" in metadata["limitations"][-1]

    sources = _rows(data_dir / "source_register.csv")
    source = next(row for row in sources if row["source_id"] == "SRC-CHIUMENTI-GRASS-AD-2019")
    assert source["doi_or_stable_id"] == "10.3390/en12173244"
    manifest = _rows(data_dir / "dataset_manifest.csv")
    entry = next(row for row in manifest if row["filename"] == data_path.name)
    assert entry["row_count"] == "47"
