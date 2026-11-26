from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD reactor"
FILENAME = "feng_2021_brown_juice_anaerobic_filter_abstract_reference.csv"
DATASET = DATA_DIR / FILENAME


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_feng_abstract_observations_are_traceable_reference_data():
    rows = _rows(DATASET)
    sidecar = json.loads(DATASET.with_suffix(".source.json").read_text(encoding="utf-8"))
    assert len(rows) == sidecar["rows"] == 2
    assert len({row["record_id"] for row in rows}) == 2
    assert {row["source_id"] for row in rows} == {"SRC013"}
    assert {row["phase"] for row in rows} == {"5"}
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert sidecar["doi"] == "10.1016/j.psep.2020.12.026"
    assert sidecar["source_file_sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()


def test_cod_removal_is_an_upper_observation_at_reported_hrt_not_a_general_factor():
    rows = _rows(DATASET)
    cod = next(row for row in rows if row["metric"] == "influent_COD_removed")
    assert (cod["reported_value"], cod["numeric_value"], cod["unit"]) == ("up to 80", "80", "%")
    assert "HRT 5.5 days" in cod["operating_condition"]
    assert "maximum" in cod["basis"]
    assert "Do not treat the maximum as a general removal factor" in cod["limitations"]


def test_ambiguous_specific_ch_expression_is_preserved_without_normalization():
    rows = _rows(DATASET)
    metric = next(row for row in rows if row["metric"] == "specific_CH_production_as_reported")
    assert metric["numeric_value"] == "230"
    assert "gCOD^-1 d^-1" in metric["reported_value"]
    assert "unresolved" in metric["unit"]
    assert "Do not interpret" in metric["limitations"]
    assert not any(key in metric for key in ("normalized_value", "normalized_unit"))


def test_feng_source_is_registered_and_dataset_remains_non_calculation_ready():
    source = next(row for row in _rows(DATA_DIR / "source_register.csv") if row["source_id"] == "SRC013")
    manifest = next(row for row in _rows(DATA_DIR / "dataset_manifest.csv") if row["filename"] == FILENAME)
    global_path = "Bigas production + upgrade/AD reactor/" + FILENAME
    global_source = next(row for row in _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_source_register.csv") if row["dataset_path"] == global_path)
    readiness = next(row for row in _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_readiness.csv") if row["dataset_path"] == global_path)
    assert source["doi_or_stable_id"] == "10.1016/j.psep.2020.12.026"
    assert manifest["row_count"] == "2"
    assert manifest["integration_status"] == "reference_only_abstract_measurements_not_runtime_eligible"
    assert global_source["source_id"] == "SRC013"
    assert readiness["readiness"] == "D3"
    assert readiness["unit_conflicts"] == "0"
    assert readiness["cross_reference_issues"] == "0"
    assert "unit interpretation is unresolved" in readiness["notes"]

