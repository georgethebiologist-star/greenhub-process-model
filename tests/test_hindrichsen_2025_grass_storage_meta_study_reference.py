import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
FILENAME = "grass_silage_fresh_matter_loss_stability_hindrichsen_2025_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_hindrichsen_grass_storage_summary_preserves_fm_basis_and_reference_limits():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["row_count"] == 26
    assert len({row["record_id"] for row in rows}) == 26
    assert {row["source_id"] for row in rows} == {"HINDRICHSEN2025_META_GRASS"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    lookup = {(row["metric"], row["storage_stage"], row["treatment"], row["statistic"]): row for row in rows}
    assert lookup[("fresh_matter_loss", "anaerobic_storage", "control", "average")]["reported_value"] == "1.2"
    assert lookup[("fresh_matter_loss", "aerobic_challenge", "control", "average")]["reported_value"] == "6.7"
    assert lookup[("fresh_matter_loss", "aerobic_challenge", "SiloSolve_FC", "average")]["reported_value"] == "3.8"
    assert lookup[("aerobic_stability", "aerobic feed-out challenge", "SiloSolve_FC", "average")]["reported_value"] == "251"
    assert lookup[("fresh_matter_loss", "aerobic challenge after anaerobic storage", "control", "reported value")]["reported_value"] == "18.4"
    assert lookup[("fresh_matter_loss", "aerobic challenge after anaerobic storage", "SiloSolve_FC", "reported value")]["reported_value"] == "4.2"

    assert all("Fresh-matter loss, not dry-matter loss" in row["notes"] for row in rows if row["metric"] == "fresh_matter_loss" and "pooled" in row["condition_group"])
    assert metadata["doi"] is None
    assert metadata["activation_state"] == "reference_only"
    assert any("Table 1 caption" in item and "row labels" in item for item in metadata["limitations"])
    assert "No explicit reuse license identified" in metadata["license_or_rights"]
    assert any(row["source_id"] == "HINDRICHSEN2025_META_GRASS" for row in sources)
    assert any(row["filename"] == FILENAME and row["row_count"] == "26" for row in manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == "HINDRICHSEN2025_META_GRASS"
    assert asset["readiness"] == "reference_only"
