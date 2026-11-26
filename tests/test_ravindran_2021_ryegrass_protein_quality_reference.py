import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Protein recovery" / "Drying"
CSV_PATH = DATA / "perennial_ryegrass_green_protein_concentrate_quality_ravindran_2021_reference.csv"
SOURCE_ID = "SRC-RAVINDRAN-2021-RYEGRASS-PROTEIN"


def _read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), "CSV row has more cells than the declared schema"
        return rows


def test_ravindran_product_quality_reference_keeps_basis_and_activation_limits():
    rows = _read_rows(CSV_PATH)
    assert len(rows) == 15
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["RAV21-FEED-PROTEIN"]["reported_value"] == "33.9"
    assert by_id["RAV21-FEED-PROTEIN"]["unit"] == "g/100 g feed"
    assert by_id["RAV21-RESULTS-OIL"]["reported_min"] == "10.5"
    assert by_id["RAV21-RESULTS-OIL"]["reported_max"] == "13.2"
    assert by_id["RAV21-RESULTS-OIL"]["reported_value"] == ""
    assert by_id["RAV21-RESULTS-STARCH"]["reported_qualitative_result"] == "not found"
    assert by_id["RAV21-RESULTS-STARCH"]["reported_value"] == ""
    assert by_id["RAV21-DRIED-PRODUCT-DM"]["reported_value"] == "90"
    assert by_id["RAV21-PRESS-CAKE-PROTEIN-PARTITION"]["reported_min"] == "50"
    assert by_id["RAV21-GREEN-JUICE-PROTEIN-PARTITION"]["reported_max"] == "50"
    assert all(row["reported_basis"] for row in rows)

    sidecar = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.3390/cleantechnol3030039"
    assert "CC BY 4.0" in sidecar["license"]
    assert sidecar["activation_state"] == "reference_only"
    assert sidecar["runtime_parameter_mapping"] == []
    assert "basis" in " ".join(sidecar["limitations"]).lower()
    assert "proprietary" in " ".join(sidecar["limitations"]).lower()

    manifest_rows = _read_rows(DATA / "dataset_manifest.csv")
    manifest = {row["filename"]: row for row in manifest_rows}
    assert len(manifest_rows) == len(manifest), "dataset manifest contains duplicate file rows"
    assert manifest[CSV_PATH.name]["row_count"] == "15"
    assert manifest[CSV_PATH.name]["integration_readiness"] == "reference_only"
    source_rows = _read_rows(DATA / "source_register.csv")
    sources = {row["source_id"]: row for row in source_rows}
    assert len(source_rows) == len(sources), "source register contains duplicate source IDs"
    assert sources[SOURCE_ID]["doi_or_stable_id"] == "10.3390/cleantechnol3030039"
