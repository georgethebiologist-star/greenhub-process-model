from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "lca" / "source_data"
DATA_FILE = DATA_DIR / "commercial_biogas_upgrader_gas_quality_kvist_aryal_2019_reference.csv"
SOURCE_ID = "SRC-KVIST-ARYAL-2019"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_kvist_aryal_upgrader_composition_and_methane_loss_are_traceable_and_reference_only():
    rows = _read_csv(DATA_FILE)
    metadata = json.loads(DATA_FILE.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    source_rows = _read_csv(ROOT / "Greenhub" / "data" / "lca" / "source_register.csv")
    manifest_rows = _read_csv(DATA_DIR / "dataset_manifest.csv")

    assert len(rows) == metadata["record_count"] == 10
    assert len({row["record_id"] for row in rows}) == 10
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["primary_article_doi"] for row in rows} == {"10.1016/j.wasman.2019.02.023"}

    plant_rows = [row for row in rows if row["record_type"] == "upgrader_sample"]
    assert len(plant_rows) == 9
    assert {row["upgrading_technology"] for row in plant_rows} == {"amine", "water_scrubber", "membrane"}
    assert sum(row["upgrading_technology"] == "amine" for row in plant_rows) == 3
    assert sum(row["upgrading_technology"] == "water_scrubber" for row in plant_rows) == 4
    assert sum(row["upgrading_technology"] == "membrane" for row in plant_rows) == 2

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["KVA19-PLANT-05"]["methane_loss_pct"] == "1.97"
    assert by_id["KVA19-PLANT-05"]["methane_loss_basis"] == "percent of methane supplied to upgrading unit"
    assert by_id["KVA19-PLANT-05"]["offgas_n2_pct"] == "68.33"
    assert by_id["KVA19-PLANT-03"]["offgas_o2_pct"] == ""
    assert by_id["KVA19-PLANT-05"]["feed_gas_n2_pct"] == "0"
    losses = [float(row["methane_loss_pct"]) for row in plant_rows]
    assert round(sum(losses) / len(losses), 2) == 0.81

    rto = by_id["KVA19-RTO-01"]
    assert rto["record_type"] == "rto_followup"
    assert rto["rto_ch4_removal_pct"] == "99.5"
    assert rto["plant_index"] == ""
    assert rto["methane_loss_pct"] == ""

    assert metadata["source_id"] == SOURCE_ID
    assert metadata["activation_state"] == "reference_only"
    assert metadata["runtime_parameter_mapping"] is None
    assert "iea bioenergy task 37 (2025)" in metadata["transcription_source"].lower()
    assert "attributes the nine-plant table" in metadata["transcription_source"].lower()
    assert "does not explicitly define" in metadata["limitations"][2]
    assert "not identified" in metadata["license"].lower()

    source = [row for row in source_rows if row["source_id"] == SOURCE_ID]
    assert len(source) == 1
    assert source[0]["doi_or_stable_identifier"] == "10.1016/j.wasman.2019.02.023"
    manifest = [row for row in manifest_rows if row["filename"] == DATA_FILE.name]
    assert len(manifest) == 1
    assert manifest[0]["row_count"] == "10"
    assert manifest[0]["integration_readiness"] == "reference_only; no runtime mapping"

    catalog = _read_csv(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    asset = next(row for row in catalog if row["relative_path"].endswith(DATA_FILE.name))
    assert asset["source_ids"] == SOURCE_ID
    assert asset["source_dois"] == "10.1016/j.wasman.2019.02.023"
    assert asset["readiness"] == "reference_only"
