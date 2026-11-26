import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage" / "grass_silage_forced_aeration_williams_1997_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_williams_grass_silage_core_data_are_traceable_and_not_mislabeled_as_mass_loss():
    rows = _rows(DATA)
    source = json.loads(DATA.with_suffix(".source.json").read_text(encoding="utf-8"))
    global_manifest = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv")
    global_readiness = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_readiness.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 48
    assert len({row["record_id"] for row in rows}) == 48
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["source_id"] for row in rows} == {"SRC-GRASS-SILAGE-BUNKER-1997"}
    assert {row["parameter"] for row in rows} == {
        "dry_matter_concentration", "water_soluble_carbohydrate", "lactic_acid", "acetic_acid",
        "butyric_acid", "total_nitrogen", "ammonia_nitrogen", "pH", "mould_count",
        "streptococci_count", "bacilli_count", "lactic_acid_bacteria_count",
    }
    assert {row["n_cores"] for row in rows} == {"5"}

    means = {
        (row["bunker"], row["sample_state"], row["parameter"]): row["mean_value"]
        for row in rows
    }
    assert means[("Bunker 1", "before forced aeration", "water_soluble_carbohydrate")] == "92"
    assert means[("Bunker 1", "after forced aeration", "water_soluble_carbohydrate")] == "72"
    assert means[("Bunker 2", "before forced aeration", "mould_count")] == "0.23"
    assert means[("Bunker 2", "after forced aeration", "mould_count")] == "6.5"
    assert all("not" in row["limitations"].lower() for row in rows if row["parameter"] == "dry_matter_concentration")

    assert source["doi"] == "10.1111/j.1365-2494.1997.tb02348.x"
    assert source["activation_state"] == "reference_only"
    assert "not a whole-silo" in " ".join(source["limitations"])
    path = "storage/grass_silage_forced_aeration_williams_1997_reference.csv"
    assert any(row["dataset_path"] == path and row["row_count_observed"] == "48" for row in global_manifest)
    assert any(row["dataset_path"] == path and row["readiness"] == "D3" for row in global_readiness)
    asset = next(row for row in catalog if row["relative_path"].endswith(DATA.name))
    assert asset["source_ids"] == "SRC-GRASS-SILAGE-BUNKER-1997"
    assert asset["readiness"] == "D3"
