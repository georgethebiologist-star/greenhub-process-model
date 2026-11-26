import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "Greenhub/data/lca/source_data/green_biorefinery_energy_benchmarks.csv"


def test_grass_clover_pilot_energy_benchmark_is_traceable_report_only_evidence():
    with BENCHMARK.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert {row["source_id"] for row in rows} == {"SRC-ELSHANI-2026-GBR-ENERGY"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"report_only"}
    assert all(row["doi"] == "10.1038/s44264-026-00189-y" for row in rows)
    assert all(row["basis"] == "dry matter input" for row in rows)
    assert all("not" in row["limitations"].lower() for row in rows)

    by_metric = {row["metric"]: row for row in rows}
    assert float(by_metric["electricity_use"]["normalized_value"]) == 375.0
    assert by_metric["electricity_use"]["normalized_unit"] == "kWh/t DM feed"
    assert float(by_metric["propane_heat"]["normalized_value"]) == 138.0
    assert by_metric["propane_heat"]["normalized_unit"] == "MJ/t DM feed"
    component_sum_mj_per_t_dm = 3.6 * float(by_metric["electricity_use"]["normalized_value"])
    component_sum_mj_per_t_dm += float(by_metric["propane_heat"]["normalized_value"])
    published_total = float(by_metric["total_reported_energy"]["normalized_value"])
    assert published_total == 1489.0
    assert abs(published_total - component_sum_mj_per_t_dm) <= 1.0
    assert "do not sum this total" in by_metric["total_reported_energy"]["limitations"].lower()


def test_grass_clover_pilot_energy_benchmark_is_findable_in_fair_catalog():
    catalog_path = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"] == "Greenhub/data/lca/source_data/green_biorefinery_energy_benchmarks.csv"
    )
    assert asset["source_metadata_status"] == "linked_to_source_register"
    assert "green_biorefinery_energy_benchmarks.source.json" in asset["source_register_paths"]
    assert "10.1038/s44264-026-00189-y" in asset["source_dois"]
    assert len(asset["sha256"]) == 64
