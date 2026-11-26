from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP"
FILENAME = "roadside_grass_bmp_seasonal_contamination_christodoulou_2022_reference.csv"
CSV_PATH = DATA / FILENAME
RELATIVE_PATH = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
SOURCE_ID = "SRC-ARAMIS-METHAROAD-SI502089-2022"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_swiss_roadside_observations_keep_bases_censoring_and_conflicts():
    observations = rows(CSV_PATH)
    assert len(observations) == 91
    assert len({row["observation_id"] for row in observations}) == len(observations)
    assert {row["source_id"] for row in observations} == {SOURCE_ID}
    assert {row["activation_state"] for row in observations} == {"reference_only"}
    assert all(row["source_location"] for row in observations if row["numeric_value"] or row["upper_bound"])

    by_id = {row["observation_id"]: row for row in observations}
    assert by_id["METHAROAD-BMP-RC604-1-FM"]["numeric_value"] == "55.2"
    assert by_id["METHAROAD-BMP-RC604-1-OM"]["numeric_value"] == "345.2"
    assert by_id["METHAROAD-BMP-LA_VEYRE_TALUS_PLAT-2-FM"]["numeric_value"] == "120.7"
    assert "statistic type not stated" in by_id["METHAROAD-BMP-RC604-1-FM"]["reported_uncertainty"]

    pah = by_id["METHAROAD-PAH-RC604-1-TOTAL"]
    assert pah["numeric_value"] == ""
    assert pah["upper_bound"] == "1.0"
    assert pah["reported_value"] == "< 1 ppm"
    assert "not zero" in pah["limitations"]

    assert by_id["METHAROAD-MACROPLASTIC-RC601B-1"]["numeric_value"] == "990"
    assert by_id["METHAROAD-MACROPLASTIC-RC604-1"]["numeric_value"] == ""
    assert "not zero" in by_id["METHAROAD-MACROPLASTIC-RC604-1"]["limitations"]
    assert by_id["METHAROAD-ZN-LA-VEYRE-INTENSIVE-JUNE"]["numeric_value"] == "3.454"
    assert "contradicting" in by_id["METHAROAD-ZN-LA-VEYRE-INTENSIVE-JUNE"]["limitations"]

    june_cn = by_id["METHAROAD-CN-JUNE-SUMMARY"]
    conflicting_cn = by_id["METHAROAD-CN-JUNE-CONFLICT"]
    assert (june_cn["lower_bound"], june_cn["upper_bound"]) == ("21", "40")
    assert (conflicting_cn["lower_bound"], conflicting_cn["upper_bound"]) == ("16", "32")
    assert "Conflicts" in conflicting_cn["limitations"]

    estimate = by_id["METHAROAD-ESTIMATED-ROAD-YIELD-RATIO"]
    assert estimate["evidence_class"] == "C_literature_based_author_estimate"
    assert (estimate["lower_bound"], estimate["upper_bound"]) == ("2", "3")
    assert "not a measured" in estimate["limitations"]


def test_sidecar_registers_and_catalog_mark_swiss_study_reference_only():
    sidecar = json.loads(Path(str(CSV_PATH) + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["source_id"] == SOURCE_ID
    assert sidecar["project_identifier"] == "SI/502089-01"
    assert sidecar["record_count"] == 91
    assert sidecar["doi"] == ""
    assert sidecar["sha256"] == hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    assert "Dutch roadside" in sidecar["limitations"][0]
    assert "reference-only" in sidecar["runtime_policy"].lower()

    for register_name in ("source_register.csv", "ad_source_register.csv"):
        assert any(row["source_id"] == SOURCE_ID for row in rows(DATA / register_name))
    manifest = next(row for row in rows(DATA / "dataset_manifest.csv") if row["filename"] == FILENAME)
    assert manifest["row_count"] == "91"
    assert manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    audit = ROOT / "Greenhub/data/global_audit_package"
    source = next(row for row in rows(audit / "global_source_register.csv") if row["dataset_path"] == RELATIVE_PATH)
    manifest = next(row for row in rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == RELATIVE_PATH)
    assert source["source_id"] == SOURCE_ID
    assert source["doi_or_stable_id"] == "SI/502089-01"
    assert manifest["row_count_observed"] == "91"

    activation = next(row for row in rows(audit / "dataset_activation_matrix.csv") if row["dataset_path"] == RELATIVE_PATH)
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["active"] == "False"
    assert activation["default_eligibility"] == "False"
    checksum = next(row for row in rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == RELATIVE_PATH)
    assert checksum["sha256"] == sidecar["sha256"]

    catalog = json.loads((ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"] == f"Greenhub/data/{RELATIVE_PATH}")
    assert SOURCE_ID in asset["source_ids"].split(";")
    assert asset["source_metadata_status"] == "linked_to_source_register"
    assert asset["readiness"] == "reference_only"
