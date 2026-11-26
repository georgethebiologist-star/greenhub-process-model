from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT / "Greenhub" / "data" / "Protein recovery" / "Membrane"
FILENAME = "clover_grass_membrane_stream_composition_and_conditions_echers_2026_reference.csv"
DATASET = GROUP / FILENAME
SOURCE_ID = "ECHERS-CLOVER-GRASSPILOT-MEMBRANE-2026"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_echers_data_are_provenanced_reference_only_and_phase_scoped():
    data = rows(DATASET)
    sidecar = json.loads(DATASET.with_suffix(".source.json").read_text(encoding="utf-8"))
    assert len(data) == 45
    assert sidecar["data_scope"].startswith(f"{len(data)} structured records")
    assert len({item["record_id"] for item in data}) == len(data)
    assert {item["source_id"] for item in data} == {SOURCE_ID}
    assert {item["phase"] for item in data} == {"1", "3", "4"}
    assert all(item["quality_class"] == "B" for item in data)
    assert all(item["activation_state"] == "reference_only" for item in data)
    assert sidecar["persistent_identifier"] == "doi:10.1039/D5FB00771B"
    assert sidecar["source_file_sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert "CC BY-NC 3.0" in sidecar["license"]


def test_composition_keeps_basis_missing_streams_and_liquid_product_distinct():
    data = rows(DATASET)
    by_id = {item["record_id"]: item for item in data}
    assert by_id["ECHERS26-BIOMASS-DM"]["numeric_value"] == "14.20"
    assert by_id["ECHERS26-BIOMASS-DM"]["reported_uncertainty"] == "SD 2.15 percentage points"
    assert by_id["ECHERS26-BIOMASS-CP"]["unit"] == "% dry matter"
    assert by_id["ECHERS26-DF-C-DM"]["numeric_value"] == "0.48"
    assert "liquid diafiltered concentrate" in by_id["ECHERS26-DF-C-DM"]["limitations"]
    assert by_id["ECHERS26-S2-PERM-DM"]["record_type"] == "not_reported"
    assert by_id["ECHERS26-DF-PERM-CP"]["numeric_value"] == ""
    assert by_id["ECHERS26-DF-PERM-CP"]["reported_value"] == "not recorded"


def test_operating_settings_preserve_ambiguity_and_do_not_claim_recovery():
    data = rows(DATASET)
    by_id = {item["record_id"]: item for item in data}
    ratio = by_id["ECHERS26-STABILIZER-RATIO"]
    assert ratio["reported_value"] == "1:2 (w/w)"
    assert ratio["numeric_value"] == ""
    assert "which material is numerator" in ratio["basis"]
    assert by_id["ECHERS26-S1-TMP"]["reported_value"] == "0.3–0.4"
    assert by_id["ECHERS26-S2-DF-CROSSFLOW"]["unit"] == "m^3 h^-1"
    pigment = by_id["ECHERS26-OVERALL-PIGMENT-DEPLETION"]
    assert "not a mass-based" in pigment["basis"]
    assert all("closed water/dry-matter/protein balance" in item["limitations"] for item in data)


def test_source_and_global_readiness_registers_keep_dataset_reference_only():
    local_source = next(item for item in rows(GROUP / "source_register.csv") if item["source_id"] == SOURCE_ID)
    local_manifest = next(item for item in rows(GROUP / "dataset_manifest.csv") if item["filename"] == FILENAME)
    relative_path = f"Protein recovery/Membrane/{FILENAME}"
    global_source = next(item for item in rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_source_register.csv") if item["dataset_path"] == relative_path)
    global_manifest = next(item for item in rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv") if item["dataset_path"] == relative_path)
    readiness = next(item for item in rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_readiness.csv") if item["dataset_path"] == relative_path)
    assert local_source["doi_or_stable_id"] == "10.1039/D5FB00771B"
    assert local_manifest["integration_readiness"] == "reference_only"
    assert global_source["source_id"] == SOURCE_ID
    assert global_manifest["detected_readiness"] == readiness["readiness"] == "D3"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert readiness["numeric_rows_missing_exact_location"] == "0"
