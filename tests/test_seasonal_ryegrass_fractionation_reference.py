import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_stodkilde_ryegrass_seasonal_fractionation_is_traceable_and_reference_only():
    path = DATA_DIR / "seasonal_ryegrass_fractionation_stodkilde_2020_reference.csv"
    rows = _rows(path)
    sidecar = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    source_register = _rows(DATA_DIR / "source_register.csv")
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 20
    assert len({row["observation_id"] for row in rows}) == 20
    assert {row["source_id"] for row in rows} == {"SRC-STODKILDE-2020"}
    assert {row["evidence_class"] for row in rows} == {"B_measured"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["harvest_date"] for row in rows} == {"May 17", "May 24", "May 31", "June 6"}

    ryegrass_isolate_recovery = {
        row["harvest_date"]: row["reported_value"]
        for row in rows if row["parameter"] == "nitrogen_recovery_to_protein_isolate"
    }
    assert ryegrass_isolate_recovery == {
        "May 17": "35.81", "May 24": "41.19", "May 31": "29.31", "June 6": "24.00"
    }
    assert all(row["basis"] == "fraction of plant N" for row in rows if "recovery" in row["parameter"])

    assert sidecar["doi"] is None
    assert sidecar["license"].startswith("No explicit reuse license")
    assert "acid volume" in " ".join(sidecar["limitations"])
    assert any(row["source_id"] == "SRC-STODKILDE-2020" for row in source_register)
    assert any(row["filename"] == path.name and row["row_count"] == "20" for row in manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(path.name))
    assert asset["source_ids"] == "SRC-STODKILDE-2020"
    assert asset["readiness"] == "reference_only"
