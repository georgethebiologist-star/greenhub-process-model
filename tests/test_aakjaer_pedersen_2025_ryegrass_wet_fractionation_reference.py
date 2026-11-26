import csv
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "Greenhub/data/Pre-treatment/Mechanical"
FILENAME = "perennial_ryegrass_wet_fractionation_aakjaer_pedersen_2025_reference.csv"
DOI = "10.3390/proteomes13010008"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_ryegrass_fractionation_table_is_faithfully_transcribed_and_nonactivated():
    path = PACKAGE / FILENAME
    rows = _rows(path)
    metadata = json.loads(Path(str(path) + ".source.json").read_text(encoding="utf-8"))
    assert len(rows) == metadata["rows"] == 15
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"S14_AAKJAER_PEDERSEN_2025"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert metadata["persistent_identifier"] == DOI
    assert metadata["license"] == "CC BY 4.0"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata["source_data_sha256"]
    assert "not roadside/VARTA grass" in " ".join(metadata["limitations"])

    by_key = {(row["stream"], row["metric"]): row for row in rows}
    assert float(by_key[("raw grass", "fraction fresh mass")]["reported_value"]) == 75.2
    assert float(by_key[("pulp", "fraction fresh mass")]["reported_value"]) == 32.9
    assert float(by_key[("green juice", "fraction fresh mass")]["reported_value"]) == 34.4
    assert float(by_key[("raw grass", "dry matter concentration")]["normalized_value"]) == pytest.approx(0.192)
    assert float(by_key[("pulp", "dry matter concentration")]["normalized_sd"]) == pytest.approx(0.031)
    assert float(by_key[("green juice", "crude protein concentration")]["normalized_value"]) == pytest.approx(0.125)
    assert by_key[("green juice", "crude protein concentration")]["basis"] == "dry matter"
    assert by_key[("green juice", "crude protein concentration")]["uncertainty_statistic"] == "SD"


def test_reported_component_distributions_close_with_source_rounding_and_not_as_exact_mass_balance():
    rows = _rows(PACKAGE / FILENAME)
    by_key = {(row["stream"], row["metric"]): row for row in rows}
    dm_distribution = sum(float(by_key[(stream, "dry matter distribution")]["normalized_value"]) for stream in ("pulp", "green juice"))
    cp_distribution = sum(float(by_key[(stream, "crude protein distribution")]["normalized_value"]) for stream in ("pulp", "green juice"))
    wet_fraction_mass = sum(float(by_key[(stream, "fraction fresh mass")]["reported_value"]) for stream in ("pulp", "green juice"))
    input_wet_mass = float(by_key[("raw grass", "fraction fresh mass")]["reported_value"])

    assert dm_distribution == pytest.approx(0.999)
    assert cp_distribution == pytest.approx(0.997)
    assert wet_fraction_mass == pytest.approx(67.3)
    assert input_wet_mass - wet_fraction_mass == pytest.approx(7.9)
    assert input_wet_mass - wet_fraction_mass > 0  # unreported wet-mass loss is not assigned to a modeled outlet


def test_dataset_is_registered_in_local_global_and_fair_catalogs():
    manifest = _rows(PACKAGE / "dataset_manifest.csv")
    source_register = _rows(PACKAGE / "source_register.csv")
    global_root = ROOT / "Greenhub/data/global_audit_package"
    rel = f"Pre-treatment/Mechanical/{FILENAME}"
    global_manifest = _rows(global_root / "global_dataset_manifest.csv")
    global_sources = _rows(global_root / "global_source_register.csv")
    checksum = _rows(global_root / "source_dataset_checksums.csv")
    assert sum(row["filename"] == FILENAME for row in manifest) == 1
    assert sum(row["source_id"] == "S14_AAKJAER_PEDERSEN_2025" for row in source_register) == 1
    assert sum(row["dataset_path"] == rel for row in global_manifest) == 1
    assert sum(row["dataset_path"] == rel for row in global_sources) == 1
    assert sum(row["dataset_path"] == rel for row in checksum) == 1
    assert next(row for row in global_manifest if row["dataset_path"] == rel)["row_count_observed"] == "15"

    catalog = json.loads((ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"] == f"Greenhub/data/{rel}")
    assert DOI in asset["source_dois"]
    assert asset["source_metadata_status"] == "linked_to_source_register"

