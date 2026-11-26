import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = (
    ROOT
    / "Greenhub"
    / "data"
    / "Protein recovery"
    / "Drying"
    / "legume_grass_concentrate_spray_drying_echeverria_jaramillo_2026_reference.csv"
)


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_grass_concentrate_dryer_conditions_and_product_protein_are_traceable():
    rows = _rows(DATASET)
    assert len(rows) == 2
    pilot, lab = rows
    assert (pilot["dryer_scale"], pilot["inlet_air_temperature_min_degC"], pilot["outlet_air_temperature_max_degC"]) == (
        "pilot",
        "220",
        "70",
    )
    assert (lab["dryer_scale"], lab["inlet_air_temperature_min_degC"], lab["outlet_air_temperature_min_degC"]) == (
        "lab",
        "246",
        "83",
    )
    assert pilot["crude_protein_mean_g_per_100g_dm"] == "66.19"
    assert lab["crude_protein_mean_g_per_100g_dm"] == "66.61"
    assert all(row["uncertainty_type"] == "source-reported; statistic type not specified" for row in rows)
    assert all(row["dryer_energy"] == "" and row["final_moisture"] == "" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)


def test_grass_concentrate_dryer_source_metadata_and_registration():
    sidecar = json.loads(DATASET.with_suffix(".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.1007/s11947-026-04220-5"
    assert sidecar["license"].startswith("CC BY")
    assert "particle size" in " ".join(sidecar["limitations"]).lower()

    source_rows = _rows(DATASET.with_name("source_register.csv"))
    assert sum(row["source_id"] == "SRC-ECHEVERRIA-2026-LGC-DRYING" for row in source_rows) == 1
    manifest_rows = _rows(DATASET.with_name("dataset_manifest.csv"))
    assert sum(row["filename"] == DATASET.name for row in manifest_rows) == 1
