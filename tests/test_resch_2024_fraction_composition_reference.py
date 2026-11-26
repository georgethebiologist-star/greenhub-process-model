import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = (
    ROOT
    / "Greenhub"
    / "data"
    / "Protein recovery"
    / "Isoelectric"
    / "grass_clover_silage_biorefinery_fraction_composition_resch_2024_reference.csv"
)


def _csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_resch_fraction_dataset_has_traceable_basis_and_expected_measurements():
    rows = _csv_rows(DATASET)
    assert len(rows) == 56
    assert len({row["observation_id"] for row in rows}) == len(rows)
    assert all(row["source_table"] in {"Table 1", "Table 3"} for row in rows)
    assert all(row["unit"] and row["measurement_basis"] for row in rows)

    lookup = {
        (row["forage_type"], row["process_fraction"], row["parameter"]): row
        for row in rows
    }
    assert lookup[("GCM", "press_juice", "crude_protein")]["value"] == "204"
    assert lookup[("red_clover", "press_juice", "dry_matter")]["value"] == "123"
    assert lookup[("GCM", "fresh_press_cake", "NDF")]["value"] == "499"
    assert lookup[("red_clover", "reensiled_press_cake", "pH")]["value"] == "4.22"
    assert not any(row["parameter"] == "NDF" and row["process_fraction"] == "press_juice" for row in rows)


def test_resch_fraction_dataset_is_registered_but_not_activated():
    sidecar = json.loads(DATASET.with_suffix(".source.json").read_text(encoding="utf-8"))
    assert sidecar["persistent_identifier"] == "doi:10.1111/gfs.12682"
    assert sidecar["evidence_class"] == "B_measured"
    assert sidecar["activation_state"] == "reference_only"

    source_register = _csv_rows(DATASET.with_name("source_register.csv"))
    assert any(row["source_id"] == "SRC-RESCH-2024-FRACTIONS" for row in source_register)
    manifest = _csv_rows(DATASET.with_name("dataset_manifest.csv"))
    assert any(
        row["filename"] == DATASET.name and row["integration_readiness"] == "reference_only"
        for row in manifest
    )
