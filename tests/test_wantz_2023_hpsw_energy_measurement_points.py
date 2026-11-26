import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Water_Scrubbing"
DATA = FOLDER / "wantz_2023_hpsw_experiment_energy_points_reference.csv"


def test_wantz_farm_scale_energy_points_are_traceable_and_not_active():
    with DATA.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(Path(str(DATA) + ".source.json").read_text(encoding="utf-8"))
    with (FOLDER / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    with (FOLDER / "source_register.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))

    assert len(rows) == 12
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["experiment_id"] for row in rows} == {"EXP31", "EXP35"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["evidence_class"] for row in rows} == {"published_primary_measurement"}
    values = {(row["experiment_id"], row["metric"]): row["reported_value"] for row in rows}
    assert values[("EXP31", "raw_biogas_flow")] == "30"
    assert values[("EXP31", "measured_electrical_power")] == "25"
    assert values[("EXP35", "raw_biogas_flow")] == "20"
    assert values[("EXP35", "measured_electrical_power")] == "16.6"
    assert all(row["qualifier"] == "approximately" for row in rows if row["metric"] in {"measured_electrical_power", "specific_electricity_consumption"})
    assert all("2 h" in row["measurement_window"] for row in rows if row["metric"] == "measured_electrical_power")
    assert metadata["doi"] == "10.1016/j.apenergy.2023.121781"
    assert "No explicit reuse license" in metadata["license_or_rights"]
    assert metadata["sha256_csv"] == hashlib.sha256(DATA.read_bytes()).hexdigest()
    assert sum(row["source_id"] == "SRC008" for row in sources) == 1
    assert any(row["filename"] == DATA.name and row["row_count"] == "12" and row["integration_status"] == "traceable_reference_only_not_runtime_eligible" for row in manifest)

    source_code = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "Greenhub").rglob("*.py"))
    assert DATA.name not in source_code
