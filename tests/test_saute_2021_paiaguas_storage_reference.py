import csv
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Greenhub" / "data" / "storage" / (
    "paiaguas_grass_silage_storage_loss_effluent_saute_2021_reference.csv"
)
SOURCE_ID = "SRC-SAUTE-PAIAGUAS-GRASS-SILAGE-2021"


def _rows():
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_extract_preserves_reported_factor_marginals_without_inventing_cells():
    rows = _rows()
    assert len(rows) == 114
    assert len({row["record_id"] for row in rows}) == 114
    assert Counter(row["source_table"] for row in rows) == {
        "Table 2": 18,
        "Table 3": 30,
        "Table 4": 60,
        "Methods/Results text": 5,
        "Figure 2 / Results text": 1,
    }
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    storage_rows = [row for row in rows if row["source_table"].startswith("Table")]
    assert Counter(row["factor"] for row in storage_rows) == {
        "theoretical_particle_size": 54,
        "compaction_density": 54,
    }
    assert all("marginal means" in row["replication_design"] for row in storage_rows)
    assert not any("interaction_cell" in row["record_id"] for row in rows)


def test_extract_keeps_source_ambiguities_and_matches_reproducible_builder():
    rows = _rows()
    by_metric = {row["metric"]: row for row in rows}
    assert by_metric["effluent_COD"]["unit"] == "mg/L (as printed)"
    assert by_metric["effluent_BOD"]["unit"] == "mg/L (as printed)"
    assert "denominator not further defined" in by_metric["effluent_dry_matter_loss"]["basis"]

    sidecar_path = DATASET.with_suffix(".source.json")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert sidecar["doi"] == "10.1590/1678-4162-12197"
    assert sidecar["license"] == "Creative Commons Attribution 4.0 International (CC BY 4.0), stated by the journal's official policy."
    assert sidecar["row_count"] == len(rows)
    assert sidecar["calculation_connected"] is False
    assert hashlib.sha256(DATASET.read_bytes()).hexdigest() == sidecar["sha256_csv"]

    script = ROOT / "scripts" / "build_saute_2021_paiaguas_silage_storage_reference.py"
    spec = importlib.util.spec_from_file_location("saute_2021_reference_builder", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert rows == module.build_rows()

    source_register = (DATASET.parent / "source_register.csv").read_text(encoding="utf-8")
    manifest = (DATASET.parent / "dataset_manifest.csv").read_text(encoding="utf-8")
    assert source_register.count(SOURCE_ID) == 1
    assert manifest.count(DATASET.name) == 1
