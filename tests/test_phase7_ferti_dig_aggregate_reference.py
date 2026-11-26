import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Resource recovery" / "Digestate_and_Separation"


def test_ferti_dig_published_aggregate_is_traceable_and_not_activated():
    dataset_path = DATA / "ferti_dig_french_digestate_summary_caradec_2025_reference.csv"
    sidecar = json.loads(dataset_path.with_suffix(".source.json").read_text(encoding="utf-8"))
    with dataset_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (DATA / "source_register.csv").open(encoding="utf-8-sig", newline="") as handle:
        sources = {row["source_id"]: row for row in csv.DictReader(handle)}
    with (DATA / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        manifest = {row["filename"]: row for row in csv.DictReader(handle)}
    by_id = {row["source_row_id"]: row for row in rows}

    assert len(rows) == 13
    assert by_id["FDIG_FR_DM_MEDIAN"]["value"] == "8.39"
    assert by_id["FDIG_FR_NTOT_MEDIAN"]["value"] == "62.16"
    assert by_id["FDIG_FR_NH4_MEDIAN"]["value"] == "28.02"
    assert by_id["FDIG_FR_K2O_MEDIAN"]["value"] == "54.59"
    assert by_id["FDIG_FR_P2O5_MEDIAN"]["value"] == "28.33"
    assert {row["collection_size_n"] for row in rows} == {"608"}
    assert {row["evidence_class"] for row in rows} == {"B_literature_measurement_summary"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["publication_doi"] == "10.1016/j.dib.2025.111550"
    assert sidecar["related_dataset_doi"] == "10.57745/M1JSU5"
    assert "CC BY 4.0" in sidecar["license"]
    assert "non-commercial" in sidecar["license"]
    assert sidecar["calculation_connected"] is False
    assert sidecar["source_id"] in sources
    assert "raw data not downloaded" in sources[sidecar["source_id"]]["quality_notes"]
    assert manifest[dataset_path.name]["row_count"] == str(len(rows))
    assert manifest[dataset_path.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"
