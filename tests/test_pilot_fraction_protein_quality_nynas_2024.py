import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILENAME = "pilot_fraction_protein_quality_nynas_2024_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_nynas_pilot_fraction_quality_is_traceable_and_reference_only():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA / "dataset_manifest.csv")
    sources = _rows(DATA / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == metadata["rows"] == 7
    assert len({row["record_id"] for row in rows}) == 7
    assert {row["source_id"] for row in rows} == {"SRC-NYNAS-2024"}
    assert {row["fraction_code"] for row in rows} == {"BM", "P", "GJ", "GP", "WJ", "WP", "BJ"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert all(float(row["total_protein_mg_per_g_DM_mean"]) > 0 for row in rows)
    green_juice = next(row for row in rows if row["fraction_code"] == "GJ")
    assert green_juice["soluble_peak_ABD_mg_per_g_DM_mean"] == "166"
    assert green_juice["total_protein_mg_per_g_DM_mean"] == "186"
    white_protein = next(row for row in rows if row["fraction_code"] == "WP")
    assert white_protein["insoluble_peak_ABD_mg_per_g_DM_mean"] == "24.9"
    assert metadata["source_doi"] == "10.1021/acsfoodscitech.3c00426"
    assert metadata["license"] == "CC BY 4.0"
    assert metadata["calculation_connected"] is False
    assert any("not Dutch roadside grass" in limitation for limitation in metadata["limitations"])
    assert any(row["filename"] == FILENAME and row["row_count"] == "7" for row in manifest)
    assert any(row["source_id"] == "SRC-NYNAS-2024" for row in sources)
    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_metadata_linkage"] == "direct_dataset_path"
    assert indexed["source_ids"] == "SRC-NYNAS-2024"
    assert indexed["source_dois"] == "10.1021/acsfoodscitech.3c00426"
