import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
CSV_PATH = FOLDER / "wet_lowland_grass_silage_storage_losses_kristensen_feng_moller_2016_reference.csv"
SOURCE_ID = "SRC-KRISTENSEN-FENG-MOLLER-WET-LOWLAND-GRASS-STORAGE-2016"


def _rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_kristensen_storage_transcription_is_traceable_reference_only():
    rows = _rows(CSV_PATH)
    assert len(rows) == 72
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["evidence_class"] for row in rows} == {"B_measured_literature"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["storage_duration_days"] for row in rows} == {"144", "223", "304"}
    assert {row["measurement"] for row in rows} == {"wet_mass_loss", "dry_matter_loss"}

    species_rows = [row for row in rows if row["record_scope"] == "species_specific"]
    average_rows = [row for row in rows if row["record_scope"] == "source_reported_species_average"]
    assert len(species_rows) == 54
    assert len(average_rows) == 18
    assert {row["replicate_count"] for row in species_rows} == {"3"}
    assert all(row["replicate_count"] == "" for row in average_rows)
    assert all(row["uncertainty"].startswith("Not reported") for row in rows)
    assert all(row["unit"] == "%" for row in rows)

    # The source-reported averages are retained as their own scope, not
    # recomputed from or conflated with the species-specific observations.
    lookup = {
        (row["storage_duration_days"], row["additive_treatment"], row["measurement"]): float(row["value"])
        for row in average_rows
    }
    assert lookup[("144", "No additive", "wet_mass_loss")] == 1.1
    assert lookup[("144", "No additive", "dry_matter_loss")] == 6.5
    assert lookup[("223", "No additive", "wet_mass_loss")] == -0.9
    assert lookup[("223", "Sill-All Fireguard", "dry_matter_loss")] == 2.3
    assert lookup[("304", "Biotal Axcool Gold", "dry_matter_loss")] == 3.6

    values = [float(row["value"]) for row in rows if row["measurement"] == "wet_mass_loss"]
    assert min(values) < 0  # Source anomalies are deliberately not clamped.
    moisture = {
        row["grass_species"]: row["initial_moisture_pct_as_reported"]
        for row in species_rows
        if row["storage_duration_days"] == "144" and row["additive_treatment"] == "No additive" and row["measurement"] == "wet_mass_loss"
    }
    assert moisture == {"Tall fescue": "69.7", "Festulolium": "69.6", "Reed canary grass": "59.9"}

    metadata = json.loads(CSV_PATH.with_suffix(CSV_PATH.suffix + ".source.json").read_text(encoding="utf-8"))
    assert metadata["dataset_id"].startswith("urn:greenhub:dataset:storage:")
    assert "no DOI was identified" in metadata["persistent_identifier_status"]
    assert "No explicit reuse license identified" in metadata["license"]
    assert "negative" in " ".join(metadata["limitations"]).lower()
    assert metadata["experiment_year"] == 2015

    local_source = next(row for row in _rows(FOLDER / "source_register.csv") if row["source_id"] == SOURCE_ID)
    assert "no DOI identified" in local_source["doi_or_stable_identifier"]
    manifest = {row["filename"]: row for row in _rows(FOLDER / "dataset_manifest.csv")}
    assert manifest[CSV_PATH.name]["row_count"] == "72"
    assert manifest[CSV_PATH.name]["integration_status"] == "traceable_reference_only_not_runtime_eligible"

    relative = "storage/" + CSV_PATH.name
    checksum = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    checksum_row = next(row for row in _rows(DATA / "global_audit_package/source_dataset_checksums.csv") if row["dataset_path"] == relative)
    assert checksum_row["sha256"] == checksum
    activation = next(row for row in _rows(DATA / "global_audit_package/dataset_activation_matrix.csv") if row["dataset_path"] == relative)
    assert activation["audit_readiness"] == "D3"
    assert activation["integration_eligibility"] == "reference_only"
    assert activation["default_eligibility"] == "False"
    assert activation["calculation_connected"] == "False"
    assert activation["active"] == "False"

    catalog = json.loads((DATA / "fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8"))
    asset = next(row for row in catalog["assets"] if row["relative_path"].endswith(CSV_PATH.name))
    assert asset["source_metadata_status"] == "linked_to_source_register"
    assert asset["source_dois"] == ""  # no DOI is claimed for this conference paper

