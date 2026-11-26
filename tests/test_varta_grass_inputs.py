from pathlib import Path
import csv
import json
import hashlib
import pytest

from Greenhub.phase3_inputs import VARTA_DEFAULT_GRASS_SAMPLE, load_roadside_grass_specification


def test_varta_default_grass_profile_is_traceable_and_measured():
    feed = load_roadside_grass_specification(scenario_id="F1", selected_month="July", sample_id=VARTA_DEFAULT_GRASS_SAMPLE)
    solids = next(item for item in feed.records if item.python_name == "total_solids" and item.sample_id == VARTA_DEFAULT_GRASS_SAMPLE)
    assert solids.value == pytest.approx(0.143)
    assert solids.measurement_status == "measured"
    assert "VARTA_2026_10_27" in (solids.reference or "")
    assert Path("Greenhub/data/Pre-treatment/Feedstock/varta_2026_dataset_traceability.csv").exists()


def test_varta_project_measurements_have_exact_fair_provenance_and_unpaired_juice():
    root = Path(__file__).resolve().parents[1]
    folder = root / "Greenhub/data/Pre-treatment/Feedstock"
    source = folder / "261027 Nutriënten Grasmonsters VARTA.xlsx"
    source_record = json.loads((folder / f"{source.name}.source.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(source.read_bytes()).hexdigest().upper() == source_record["source_workbook_sha256"]

    with (folder / "source_register.csv").open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    assert sum(row["source_id"] == "SRC-VARTA-2026-10-27" for row in source_rows) == 1

    with (root / "Greenhub/data/fair_input_catalog/master_input_catalog.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        catalog = {row["relative_path"]: row for row in csv.DictReader(handle)}
    fiber = catalog["Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_fiber_measurements.csv"]
    juice = catalog["Greenhub/data/Pre-treatment/Feedstock/varta_2026_grass_juice_measurements.csv"]
    for record in (fiber, juice):
        assert record["source_ids"] == "SRC-VARTA-2026-10-27"
        assert record["source_metadata_status"] == "linked_to_source_register"
        assert "No external reuse license identified" in record["license_or_rights"]
    assert fiber["readiness"] == "partial_calculation_connection_for_greenhub_sample_row_7"
    assert juice["readiness"] == "reference_only"

    with (folder / "varta_2026_grass_juice_measurements.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        juice_rows = list(csv.DictReader(handle))
    greenhub_juice = next(row for row in juice_rows if row["sample_name_english"] == "Greenhub (grass sample)")
    assert greenhub_juice["sample_date"] == ""
    juice_provenance = json.loads((folder / "varta_2026_grass_juice_measurements.csv.source.json").read_text(encoding="utf-8"))
    assert juice_provenance["activation_state"] == "reference_only_for_phase3_component_partition"
