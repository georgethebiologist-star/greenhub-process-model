from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORAGE = ROOT / "Greenhub" / "data" / "storage"
FILENAME = "silage_feedout_co2_ethanol_emissions_shan_2026_abstract_reference.csv"
DATASET = STORAGE / FILENAME
SOURCE_ID = "SRC-SHAN-SILAGE-FEEDOUT-EMISSIONS-2026"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        result = list(reader)
        assert reader.fieldnames
        assert all(None not in item for item in result)
        return result


def test_shan_abstract_values_keep_printed_uncertainty_and_unknown_statistic():
    records = rows(DATASET)
    assert len(records) == 6
    assert len({record["observation_id"] for record in records}) == 6
    assert {record["source_id"] for record in records} == {SOURCE_ID}
    assert {record["phase"] for record in records} == {"2"}
    assert {record["quality_class"] for record in records} == {"B"}
    assert {record["activation_state"] for record in records} == {"reference_only"}

    observed = {
        (record["material"], record["response"]): (record["reported_value"], record["reported_uncertainty"])
        for record in records if record["reported_uncertainty"] != "not reported"
    }
    assert observed[("maize silage", "initial carbon dioxide emission")] == ("1.104", "1.294")
    assert observed[("maize silage", "initial ethanol emission")] == ("0.570", "0.807")
    assert observed[("ryegrass silage", "initial carbon dioxide emission")] == ("0.805", "0.888")
    assert observed[("ryegrass silage", "initial ethanol emission")] == ("0.060", "0.408")
    assert all(record["unit_as_reported"] == "10^-2 mol m^-2" for record in records[:4])
    assert all("statistic not identified" in record["reported_statistic_type"] for record in records[:4])
    assert all("per area" in record["basis"] for record in records[:4])
    assert {record["reported_value"] for record in records[4:]} == {"approximately 40", "approximately 100"}


def test_shan_extract_is_registered_and_cannot_be_used_as_runtime_emission_factor():
    sidecar = json.loads(Path(str(DATASET) + ".source.json").read_text(encoding="utf-8"))
    assert sidecar["doi"] == "10.1016/j.jece.2026.121987"
    assert sidecar["applicable_phases"] == [2]
    assert sidecar["record_count"] == 6
    assert sidecar["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert "available on request" in sidecar["data_availability"]
    assert "statistic" in sidecar["uncertainty"]
    assert "no feed mass or dry matter denominator" in sidecar["limitations"][1]
    assert "Reference-only" in sidecar["runtime_policy"]

    source = next(item for item in rows(STORAGE / "source_register.csv") if item["source_id"] == SOURCE_ID)
    manifest = next(item for item in rows(STORAGE / "dataset_manifest.csv") if item["filename"] == FILENAME)
    relative_path = f"storage/{FILENAME}"
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_source = next(item for item in rows(audit / "global_source_register.csv") if item["dataset_path"] == relative_path)
    global_manifest = next(item for item in rows(audit / "global_dataset_manifest.csv") if item["dataset_path"] == relative_path)
    readiness = next(item for item in rows(audit / "global_dataset_readiness.csv") if item["dataset_path"] == relative_path)

    assert source["doi_or_stable_identifier"] == "10.1016/j.jece.2026.121987"
    assert manifest["integration_status"] == "traceable_reference_only_not_runtime_eligible"
    assert global_source["source_id"] == SOURCE_ID
    assert global_manifest["detected_readiness"] == readiness["readiness"] == "D3"
    assert readiness["numeric_rows"] == "6"
    assert readiness["unsourced_numeric_rows"] == "0"
    assert readiness["numeric_rows_missing_exact_location"] == "0"
