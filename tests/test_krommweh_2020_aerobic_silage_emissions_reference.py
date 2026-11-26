from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORAGE = ROOT / "Greenhub" / "data" / "storage"
FILENAME = "post_opening_aerobic_silage_emissions_krommweh_2020_reference.csv"
DATASET = STORAGE / FILENAME
SOURCE_ID = "SRC-KROMMWEH-AEROBIC-SILAGE-EMISSIONS-2020"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows)
        return rows


def test_krommweh_values_are_exact_abstract_totals_and_reference_only():
    rows = _rows(DATASET)
    assert len(rows) == 8
    assert len({row["observation_id"] for row in rows}) == 8
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["phase"] for row in rows} == {"2"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_key = {(row["material"], row["property"]): row for row in rows}
    assert by_key[("grass silage bale", "cumulative_carbon dioxide_emission")]["value"] == "2313"
    assert by_key[("lucerne silage bale", "cumulative_carbon dioxide_emission")]["value"] == "2612"
    assert by_key[("grass silage bale", "cumulative_ethanol_emission")]["value"] == "132.3"
    assert by_key[("lucerne silage bale", "cumulative_ethanol_emission")]["value"] == "675.9"
    assert {row["time_window_hours"] for row in rows} == {"600"}
    assert {row["unit"] for row in rows} == {"g bale^-1"}
    assert all("bale mass not reported" in row["mass_basis"] for row in rows)
    assert all(row["reported_uncertainty"] == "not reported" for row in rows)


def test_dataset_sidecar_and_registers_keep_scope_and_missing_denominator_explicit():
    sidecar = json.loads(Path(str(DATASET) + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["doi"] == "10.1016/j.envpol.2020.115513"
    assert sidecar["quality_class"] == "B"
    assert sidecar["applicable_phases"] == [2]
    assert sidecar["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert "bale-mass normalization" in sidecar["conversion_or_processing"]
    assert "these values are not emission factors" in " ".join(sidecar["limitations"])
    assert "Elsevier copyright" in sidecar["license"]

    source = next(row for row in _rows(STORAGE / "source_register.csv") if row["source_id"] == SOURCE_ID)
    manifest = next(row for row in _rows(STORAGE / "dataset_manifest.csv") if row["filename"] == FILENAME)
    relative_path = f"storage/{FILENAME}"
    global_source = next(row for row in _rows(ROOT / "Greenhub/data/global_audit_package/global_source_register.csv") if row["dataset_path"] == relative_path)
    global_manifest = next(row for row in _rows(ROOT / "Greenhub/data/global_audit_package/global_dataset_manifest.csv") if row["dataset_path"] == relative_path)
    readiness = next(row for row in _rows(ROOT / "Greenhub/data/global_audit_package/global_dataset_readiness.csv") if row["dataset_path"] == relative_path)
    assert source["doi_or_stable_identifier"] == "10.1016/j.envpol.2020.115513"
    assert manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    assert global_source["source_id"] == SOURCE_ID
    assert global_manifest["detected_readiness"] == readiness["readiness"] == "D3"
    assert readiness["numeric_rows"] == "8"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert readiness["numeric_rows_missing_exact_location"] == "0"
