import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Protein recovery" / "Isoelectric"
FILENAME = "kaur_2021_trojan_ryegrass_gpc_yield_composition_and_protocol_reference.csv"
SOURCE_ID = "SRC-KAUR-2021-TROJAN-RYEGRASS-GPC"


def _read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_kaur_ryegrass_gpc_data_are_traceable_and_route_bounded():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    by_id = {row["record_id"]: row for row in rows}

    assert len(rows) == metadata["row_count"] == 31
    assert len(by_id) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert by_id["KAUR21-ACID-GPC-YIELD"]["value"] == "2.22"
    assert by_id["KAUR21-ACID-GPC-YIELD"]["unit"] == "% fresh grass mass"
    assert by_id["KAUR21-ENZYME-GPC-YIELD"]["value"] == "11"
    assert by_id["KAUR21-ENZYME-GPC-YIELD"]["unit"] == "% dry grass mass"
    assert by_id["KAUR21-ENZYME-PROTEIN-RECOVERY"]["basis"].startswith("author-reported")
    assert by_id["KAUR21-ACID-GPC-PROTEIN"]["value"] == "54.69"
    assert "5.83" in by_id["KAUR21-ACID-GPC-PROTEIN"]["analytical_method"]
    assert by_id["KAUR21-ACID-GPC-MOISTURE"]["basis"].endswith("not further specified")
    assert by_id["KAUR21-ACID-GPC-CALCIUM"]["unit"] == "mg/100 g"
    assert by_id["KAUR21-ACID-PRECIP-PH"]["value"] == "3.5"
    assert "No acid demand" in by_id["KAUR21-ACID-PRECIP-PH"]["limitations"]
    assert by_id["KAUR21-ENZYME-WATER-1"]["value"] == "9000"
    assert "not normalized per tonne" in " ".join(metadata["limitations"])
    assert metadata["license"].endswith("(CC BY 4.0), identified by Massey Research Online and the article publisher.")
    assert metadata["calculation_connected"] is False
    assert all("not roadside" in row["transferability"] for row in rows)

    sources = _read(FOLDER / "source_register.csv")
    manifests = _read(FOLDER / "dataset_manifest.csv")
    global_sources = _read(DATA / "global_audit_package" / "global_source_register.csv")
    global_manifest = _read(DATA / "global_audit_package" / "global_dataset_manifest.csv")
    readiness = _read(DATA / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _read(DATA / "global_audit_package" / "source_dataset_checksums.csv")
    catalog = _read(DATA / "fair_input_catalog" / "master_input_catalog.csv")

    assert any(row["source_id"] == SOURCE_ID and row["doi_or_stable_id"] == "10.3390/foods10020331" for row in sources)
    assert any(row["filename"] == FILENAME and row["row_count"] == "31" for row in manifests)
    relative = f"Protein recovery/Isoelectric/{FILENAME}"
    assert sum(row["dataset_path"] == relative for row in global_sources) == 1
    global_entry = next(row for row in global_manifest if row["dataset_path"] == relative)
    assert global_entry["row_count_observed"] == "31"
    assert global_entry["detected_readiness"] == "D3"
    readiness_entry = next(row for row in readiness if row["dataset_path"] == relative)
    assert readiness_entry["numeric_rows"] == "30"
    assert readiness_entry["numeric_rows_missing_exact_location"] == "0"
    checksum = next(row for row in checksums if row["dataset_path"] == relative)
    assert checksum["sha256"] == metadata["sha256_csv"]
    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["readiness"] == "reference_only"
