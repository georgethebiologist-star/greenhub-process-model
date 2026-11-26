import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_2026_ryegrass_pilot_measurements_are_fully_traceable_and_reference_only():
    path = DATA_DIR / "cultivated_ryegrass_pilot_extraction_2023_reference.csv"
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    sources = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 13
    assert len({row["measurement_id"] for row in rows}) == 13
    assert {row["source_id"] for row in rows} == {"SRC-SANDOVAL-2026"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert any(row["parameter"] == "fresh_grass_feed_mass" and row["reported_value"] == "1500" and row["unit"] == "kg" for row in rows)
    assert any(row["parameter"] == "raw_grass_juice_dry_matter" and row["reported_value"] == "5.13" and row["basis"] == "wet basis" for row in rows)
    assert any(row["parameter"] == "protein_precipitation_target_pH" and row["reported_value"] == "3.5" for row in rows)
    assert any(row["parameter"] == "final_product_crude_protein" and row["reported_value"] == "40.1" and row["reported_uncertainty"] == "0.5" for row in rows)

    assert metadata["doi"] == "10.1038/s41538-026-00831-6"
    assert metadata["dataset_file"] == path.name
    assert metadata["license"] == "CC BY 4.0"
    assert "cultivated perennial ryegrass" in metadata["material_scope"].lower()
    assert any(row["source_id"] == "SRC-SANDOVAL-2026" for row in sources)
    assert any(row["filename"] == path.name and row["row_count"] == "13" for row in manifest)
    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "SRC-SANDOVAL-2026"
    assert asset["source_dois"] == "10.1038/s41538-026-00831-6"
    assert asset["observed_rows"] == "13"
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_linkage"] == "direct_dataset_path"

    code = "\n".join(file.read_text(encoding="utf-8") for file in (ROOT / "Greenhub").rglob("*.py"))
    assert path.name not in code
