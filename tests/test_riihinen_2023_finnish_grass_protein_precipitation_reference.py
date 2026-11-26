import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILENAME = "riihinen_2023_finnish_grass_protein_precipitation_reference.csv"
SOURCE_ID = "SRC-RIIHINEN-EFFOST-GRASS-PROTEIN-2023"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_riihinen_abstract_observations_keep_conditions_and_denominators_separate():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    assert len(rows) == metadata["row_count"] == 10
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["RIIHINEN23-SULPHITE-ADDITION"]["reported_value"] == "25"
    assert "denominator" in by_id["RIIHINEN23-SULPHITE-ADDITION"]["limitations"]
    assert by_id["RIIHINEN23-HEAT-SELECTED-OPTIMUM"]["reported_value"] == "50"
    assert by_id["RIIHINEN23-ACID-PH-TESTED"]["reported_value"] == "5; 4; 3; 2"
    assert by_id["RIIHINEN23-RED-CLOVER-PRECIPITATE-MAX-PROTEIN"]["reported_value"] == "45"
    assert "does not separately restate the pH" in by_id["RIIHINEN23-TIMOTHY-PRECIPITATE-MAX-PROTEIN"]["condition_scope"]
    assert by_id["RIIHINEN23-SELECTED-RED-CLOVER-PRODUCT-PROTEIN"]["reported_value"] == "41"
    assert by_id["RIIHINEN23-SELECTED-TIMOTHY-PRODUCT-PROTEIN"]["reported_value"] == "51"
    recovery = by_id["RIIHINEN23-SELECTED-RED-CLOVER-PROTEIN-RECOVERY"]
    assert recovery["reported_value"] == "approximately 10"
    assert "not feed protein" in recovery["limitations"]

    assert "doi" not in metadata
    assert metadata["persistent_identifier"].startswith("ISBN 978-90-9037865-7")
    assert metadata["calculation_connected"] is False
    assert any(row["source_id"] == SOURCE_ID for row in _read(FOLDER / "source_register.csv"))
    assert any(row["filename"] == FILENAME and row["row_count"] == "10" for row in _read(FOLDER / "dataset_manifest.csv"))

    catalog = _read(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert SOURCE_ID in asset["source_ids"]
    assert asset["readiness"] == "reference_only"

    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    relative_path = f"Protein recovery/Isoelectric/{FILENAME}"
    global_manifest = _read(audit / "global_dataset_manifest.csv")
    manifest_record = next(row for row in global_manifest if row["dataset_path"] == relative_path)
    assert manifest_record["detected_readiness"] == "D3"
    checksum = next(row for row in _read(audit / "source_dataset_checksums.csv") if row["dataset_path"] == relative_path)
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

