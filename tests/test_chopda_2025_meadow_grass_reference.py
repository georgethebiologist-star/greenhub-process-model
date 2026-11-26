from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP"
FILENAME = "meadow_grass_pretreatment_bmp_digestate_chopda_2025_reference.csv"
CSV_PATH = DATA / FILENAME
RELATIVE_PATH = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
SOURCE_ID = "SRC-CHOPDA-MEADOW-GRASS-2025"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_cross_phase_observations_keep_reported_values_and_limits():
    rows = _rows(CSV_PATH)
    assert len(rows) == 63
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["evidence_class"] for row in rows} == {"B_measured_literature_observation"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_id = {row["observation_id"]: row for row in rows}
    assert by_id["CHOPDA25-FEED-CELLULOSE"]["numeric_value"] == "29.4"
    assert by_id["CHOPDA25-FEED-BOTANICAL-MIX"]["unit"] == "species list"
    assert "not stated" in by_id["CHOPDA25-FEED-CELLULOSE"]["basis"]
    assert by_id["CHOPDA25-E-TS"]["numeric_value"] == "21.9"
    assert by_id["CHOPDA25-EM-BMP-VS"]["numeric_value"] == "343"
    assert by_id["CHOPDA25-EM-BMP-FM"]["numeric_value"] == "75"
    assert by_id["CHOPDA25-E-DIGESTATE-N"]["numeric_value"] == "7"
    assert by_id["CHOPDA25-LA-LDELBRUECKII"]["numeric_value"] == "240"
    assert "not protein recovery" in by_id["CHOPDA25-LA-LDELBRUECKII"]["applicability"]
    assert by_id["CHOPDA25-LA-FERMENTER-TEMPERATURE"]["numeric_value"] == "37"
    assert by_id["CHOPDA25-BMP-METHANE-FRACTION"]["phase"] == "5;6"
    assert "no gas-upgrading" in by_id["CHOPDA25-BMP-METHANE-FRACTION"]["applicability"]
    assert by_id["CHOPDA25-HYDROLYSATE-CENTRIFUGE-SPEED"]["unit"] == "rpm"
    assert by_id["CHOPDA25-HYDROLYSATE-CENTRIFUGE-DURATION"]["unit"] == "min"
    assert all(row["source_location"] for row in rows if row["numeric_value"] or row["lower_bound"] or row["upper_bound"])


def test_dataset_metadata_and_registers_are_traceable_but_not_runtime_active():
    metadata = json.loads(Path(str(CSV_PATH) + ".source.json").read_text(encoding="utf-8"))
    assert metadata["doi"] == "10.1007/s13399-024-05776-y"
    assert metadata["source_id"] == SOURCE_ID
    assert metadata["record_count"] == 63
    assert metadata["quality_class"] == "B"
    assert metadata["sha256"] == hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    assert "not roadside grass" in metadata["limitations"][0]
    assert "prohibits further distribution" in metadata["license"]
    assert "no parameter registry" in metadata["runtime_policy"].lower()
    assert metadata["phase_coverage"]["4"].startswith("Lactic-acid fermentation")
    assert "no upgrading technology" in metadata["phase_coverage"]["6"]

    local_sources = _rows(DATA / "source_register.csv")
    local_ad_sources = _rows(DATA / "ad_source_register.csv")
    local_manifest = _rows(DATA / "dataset_manifest.csv")
    assert any(row["source_id"] == SOURCE_ID for row in local_sources)
    assert any(row["source_id"] == SOURCE_ID for row in local_ad_sources)
    manifest = next(row for row in local_manifest if row["filename"] == FILENAME)
    assert manifest["row_count"] == "63"
    assert manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    audit = ROOT / "Greenhub/data/global_audit_package"
    global_sources = _rows(audit / "global_source_register.csv")
    manifests = _rows(audit / "global_dataset_manifest.csv")
    readiness = _rows(audit / "global_dataset_readiness.csv")
    source = next(row for row in global_sources if row["dataset_path"] == RELATIVE_PATH)
    manifest = next(row for row in manifests if row["dataset_path"] == RELATIVE_PATH)
    gate = next(row for row in readiness if row["dataset_path"] == RELATIVE_PATH)
    assert source["source_id"] == SOURCE_ID
    assert source["doi_or_stable_id"] == metadata["doi"]
    assert manifest["row_count_observed"] == "63"
    assert manifest["detected_readiness"] == gate["readiness"] == "D3"
    assert gate["numeric_rows"] == "61"
    assert gate["unsourced_numeric_rows"] == "0"

    activation = next(row for row in _rows(audit / "dataset_activation_matrix.csv") if row["dataset_path"] == RELATIVE_PATH)
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["active"] == "False"
    assert activation["default_eligibility"] == "False"
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == RELATIVE_PATH)
    assert checksum["sha256"] == metadata["sha256"]


def test_fair_catalog_indexes_the_new_evidence_and_citation():
    catalog = json.loads((ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"] == f"Greenhub/data/{RELATIVE_PATH}")
    assert SOURCE_ID in asset["source_ids"].split(";")
    assert "10.1007/s13399-024-05776-y" in asset["source_dois"].split(";")
    assert str(asset["observed_rows"]) == "63"
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_status"] == "linked_to_source_register"
