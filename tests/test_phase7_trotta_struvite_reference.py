import csv
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_dataset_reuse_catalog


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Resource recovery" / "Digestate_and_Separation"


def test_trotta_cow_digestate_nutrient_recovery_is_traceable_and_reference_only():
    path = DATA / "cow_digestate_struvite_ammonia_recovery_trotta_2023_reference.csv"
    sidecar = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (DATA / "source_register.csv").open(encoding="utf-8-sig", newline="") as handle:
        sources = {row["source_id"]: row for row in csv.DictReader(handle)}
    with (DATA / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        manifest = {row["filename"]: row for row in csv.DictReader(handle)}
    with (ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        global_manifest = {row["dataset_path"].split("/")[-1]: row for row in csv.DictReader(handle)}

    by_id = {row["observation_id"]: row for row in rows}
    assert len(rows) == 10
    assert by_id["TROTTA_FS8"]["total_phosphorus_removed_pct"] == "61.4"
    assert by_id["TROTTA_FS8"]["ammonia_stripped_pct"] == "65.6"
    assert by_id["TROTTA_CLS2"]["total_phosphorus_removed_pct"] == "57.47"
    assert by_id["TROTTA_CLS2"]["airflow_L_min"] == "9"
    assert {row["evidence_class"] for row in rows} == {"B_literature_measurement"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert sidecar["publication_doi"] == "10.1016/j.rineng.2023.101478"
    assert sidecar["calculation_connected"] is False
    assert "CC BY 4.0" in sidecar["license"]
    assert "Tables 4-5" in sidecar["source_location"]
    assert "independent process-run replicates is not stated" in sidecar["measurement_basis"]
    assert sidecar["related_technology_family_ids"] == ["anaerobic_digestion"]
    assert "cattle" in sidecar["experimental_context"]
    assert "scale-up" in " ".join(sidecar["limitations"])
    assert sidecar["source_id"] in sources
    assert "no GreenHub runtime activation" in sources[sidecar["source_id"]]["quality_notes"]
    assert manifest[path.name]["row_count"] == str(len(rows))
    assert manifest[path.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    with (DATA / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        local_manifest_rows = list(csv.DictReader(handle))
    assert sum(row["filename"] == path.name for row in local_manifest_rows) == 1
    assert global_manifest[path.name]["row_count_observed"] == str(len(rows))
    assert global_manifest[path.name]["detected_readiness"] == "D3"

    catalog = {row["filename"]: row for row in build_dataset_reuse_catalog()}
    reuse_record = catalog[path.name]
    assert reuse_record["technology_family_ids"] == ["anaerobic_digestion", "npk_recovery"]
    assert reuse_record["related_technology_family_ids"] == ["anaerobic_digestion"]
    assert reuse_record["source_metadata_gaps"] == []
    assert reuse_record["data_status_values"] == "reference_only"
    assert reuse_record["activation_state"] == "reference_only"
    assert any("CC BY 4.0" in value for value in reuse_record["source_licenses"])
    assert any("Tables 4-5" in value for value in reuse_record["source_locations"])
