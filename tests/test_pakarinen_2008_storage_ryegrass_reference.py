from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Greenhub/data/storage/ryegrass_ensiling_storage_methane_yield_pakarinen_2008_reference.csv"
RELATIVE_DATASET = "storage/ryegrass_ensiling_storage_methane_yield_pakarinen_2008_reference.csv"
SOURCE_ID = "SRC-PAKARINEN-ENERGY-CROP-STORAGE-2008"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_selected_table2_observations_keep_storage_and_methane_bases_distinct():
    rows = _rows(DATASET)
    assert len(rows) == 6
    assert len({row["record_id"] for row in rows}) == 6
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["phase"] for row in rows} == {"2;5"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["storage_duration_months"] for row in rows} == {"0", "2", "6"}
    assert {row["initial_solids_class"] for row in rows} == {"low solids", "high solids"}
    assert all("Table 2" in row["source_location"] for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["PAK08-RG-LOW-0M"]["total_solids_pct"] == "13.3"
    assert by_id["PAK08-RG-LOW-2M"]["vs_loss_pct"] == "29.6"
    assert by_id["PAK08-RG-LOW-6M"]["methane_yield_m3_per_t_original_wet"] == "25.6"
    assert by_id["PAK08-RG-HIGH-0M"]["total_solids_pct"] == "30.4"
    assert by_id["PAK08-RG-HIGH-2M"]["methane_yield_m3_per_t_current_wet"] == "108.3"
    assert by_id["PAK08-RG-HIGH-6M"]["methane_yield_m3_per_t_original_wet"] == "43.5"
    assert by_id["PAK08-RG-HIGH-0M"]["methane_potential_m3_per_kg_vs"] == ""
    assert "only on the low-solids sample" in by_id["PAK08-RG-HIGH-0M"]["notes"]
    assert by_id["PAK08-RG-LOW-2M"]["methane_potential_sd_m3_per_kg_vs"] == "0.04"


def test_metadata_and_all_registries_link_the_source_without_activating_it():
    metadata = json.loads(Path(str(DATASET) + ".source.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert metadata["doi"] == "10.1016/j.biortech.2008.01.007"
    assert metadata["record_count"] == 6
    assert metadata["sha256"] == digest
    assert metadata["quality_class"] == "B"
    assert metadata["applicable_phases"] == [2, 5]
    assert "No open-data reuse license" in metadata["license"]
    assert "not roadside/VARTA grass" in " ".join(metadata["limitations"])
    assert "not mapped to the parameter registry" in metadata["runtime_policy"]

    storage = ROOT / "Greenhub/data/storage"
    local_source = next(row for row in _rows(storage / "source_register.csv") if row["source_id"] == SOURCE_ID)
    assert local_source["doi_or_stable_identifier"] == metadata["doi"]
    local_manifest = next(row for row in _rows(storage / "dataset_manifest.csv") if row["filename"] == DATASET.name)
    assert local_manifest["row_count"] == "6"
    assert local_manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    audit = ROOT / "Greenhub/data/global_audit_package"
    manifest = next(row for row in _rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == RELATIVE_DATASET)
    readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == RELATIVE_DATASET)
    activation = next(row for row in _rows(audit / "dataset_activation_matrix.csv") if row["dataset_path"] == RELATIVE_DATASET)
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == RELATIVE_DATASET)
    assert manifest["detected_readiness"] == readiness["readiness"] == "D3"
    assert manifest["row_count_observed"] == "6"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["active"] == activation["default_eligibility"] == "False"
    assert checksum["sha256"] == digest

    catalog = json.loads((ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"] == f"Greenhub/data/{RELATIVE_DATASET}")
    assert SOURCE_ID in asset["source_ids"].split(";")
    assert metadata["doi"] in asset["source_dois"].split(";")
    assert asset["readiness"] == "reference_only"
