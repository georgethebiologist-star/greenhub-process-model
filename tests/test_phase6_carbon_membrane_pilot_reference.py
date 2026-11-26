import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Bigas production + upgrade/Membrane"


def test_carbon_membrane_pilot_values_are_traceable_and_not_activated():
    with (DATA / "performance_observations.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = {row["parameter_id"]: row for row in csv.DictReader(f)}
    with (DATA / "source_register.csv").open(encoding="utf-8-sig", newline="") as f:
        sources = {row["source_id"]: row for row in csv.DictReader(f)}
    with (DATA / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        manifest = {row["filename"]: row for row in csv.DictReader(f)}

    assert rows["MEM_PERF_007"]["value"] == "98"
    assert rows["MEM_PERF_008"]["value"] == "96"
    assert rows["MEM_PERF_009"]["value"] == "0.13"
    assert rows["MEM_PERF_007"]["source_id"] == "CARBON2018"
    assert "maximum" in rows["MEM_PERF_007"]["basis"]
    assert "compressor" in rows["MEM_PERF_009"]["basis"]
    assert "not transferable as total" in rows["MEM_PERF_009"]["transferability"]
    assert sources["CARBON2018"]["doi_or_stable_identifier"] == "10.1016/j.gee.2018.03.003"
    assert manifest["performance_observations.csv"]["row_count"] == "9"
    assert all(rows[key]["data_status"] == "literature-reported" for key in ("MEM_PERF_007", "MEM_PERF_008", "MEM_PERF_009"))
