import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Greenhub/data/storage/post_protein_grass_pulp_ensiling_larsen_2019_abstract_reference.csv"
SIDECAR = Path(str(DATASET) + ".source.json")
RELATIVE_DATASET = "storage/post_protein_grass_pulp_ensiling_larsen_2019_abstract_reference.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_abstract_extract_preserves_only_reported_values_and_reference_status():
    rows = _rows(DATASET)
    assert len(rows) == 16
    assert len({row["record_id"] for row in rows}) == 16
    assert {row["source_id"] for row in rows} == {"SRC-LARSEN-POSTBIOREFINERY-PULP-2019"}
    assert {row["evidence_class"] for row in rows} == {"B_measured_literature_abstract_aggregate"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {phase for row in rows for phase in row["phase"].split(";")} == {"2", "3", "4", "5"}

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["LAR19-PULP-TS-GC"]["numeric_value"] == "28.8"
    assert by_id["LAR19-PULP-TS-RG"]["numeric_value"] == "33.6"
    assert by_id["LAR19-RECOVERY-VS"]["reported_value"] == "97–98"
    assert by_id["LAR19-RECOVERY-BMP"]["reported_value"] == "98–116"
    assert "not an absolute methane yield" in by_id["LAR19-RECOVERY-BMP"]["basis"]
    assert by_id["LAR19-PILOT-EFFLUENT-RG"]["numeric_value"] == "0.0"
    assert "not evidence of absolute zero" in by_id["LAR19-PILOT-EFFLUENT-RG"]["notes"]
    assert by_id["LAR19-BMP-DURATION-RESPONSE"]["numeric_value"] == ""
    assert "not continuous-reactor HRT" in by_id["LAR19-BMP-DURATION-RESPONSE"]["condition_or_time"]
    assert all(row["source_location"].startswith("Published abstract") for row in rows)


def test_source_metadata_hash_and_local_registration_are_traceable():
    metadata = json.loads(SIDECAR.read_text(encoding="utf-8"))
    assert metadata["doi"] == "10.1016/j.indcrop.2019.111576"
    assert metadata["source_url"] == "https://doi.org/10.1016/j.indcrop.2019.111576"
    assert metadata["record_count"] == 16
    assert metadata["quality_class"] == "B"
    assert metadata["runtime_policy"].startswith("Reference-only")
    assert "license was confirmed" in metadata["license"]
    assert metadata["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()

    local_sources = _rows(ROOT / "Greenhub/data/storage/source_register.csv")
    source = next(row for row in local_sources if row["source_id"] == metadata["source_id"])
    assert source["doi_or_stable_identifier"] == metadata["doi"]
    local_manifest = _rows(ROOT / "Greenhub/data/storage/dataset_manifest.csv")
    manifest = next(row for row in local_manifest if row["filename"] == DATASET.name)
    assert manifest["row_count"] == "16"
    assert manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"


def test_global_manifest_readiness_and_checksum_are_consistent_and_inactive():
    audit = ROOT / "Greenhub/data/global_audit_package"
    manifests = _rows(audit / "global_dataset_manifest.csv")
    readiness = _rows(audit / "global_dataset_readiness.csv")
    summary = json.loads((audit / "global_validation_summary.json").read_text(encoding="utf-8"))
    assert len(manifests) == len(readiness) == summary["dataset_count"]
    manifest = next(row for row in manifests if row["dataset_path"] == RELATIVE_DATASET)
    gate = next(row for row in readiness if row["dataset_path"] == RELATIVE_DATASET)
    assert manifest["detected_readiness"] == gate["readiness"] == "D3"
    assert manifest["row_count_observed"] == "16"
    assert gate["unsourced_numeric_rows"] == "0"
    issues = _rows(audit / "global_validation_issues.csv")
    assert summary["issue_count"] == len(issues)

    activation = next(
        row for row in _rows(audit / "dataset_activation_matrix.csv")
        if row["dataset_path"] == RELATIVE_DATASET
    )
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["active"] == "False"
    assert activation["default_eligibility"] == "False"
    checksum = next(
        row for row in _rows(audit / "source_dataset_checksums.csv")
        if row["dataset_path"] == RELATIVE_DATASET
    )
    assert checksum["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()


def test_fair_catalog_indexes_the_dataset_with_source_doi_but_no_activation():
    catalog = json.loads((ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"] == f"Greenhub/data/{RELATIVE_DATASET}")
    assert "SRC-LARSEN-POSTBIOREFINERY-PULP-2019" in asset["source_ids"].split(";")
    assert "10.1016/j.indcrop.2019.111576" in asset["source_dois"].split(";")
    assert asset["readiness"] == "reference_only"
    assert asset["source_metadata_status"] == "linked_to_source_register"
