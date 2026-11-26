import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
NAME = "stodkilde_2021_species_harvest_press_fractionation_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_stodkilde_2021_full_species_press_dataset_is_traceable_and_not_activated():
    path = DATA / NAME
    rows = _rows(path)
    sidecar = json.loads(path.with_suffix(path.suffix + ".source.json").read_text(encoding="utf-8"))
    source_register = _rows(DATA / "source_register.csv")
    manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    audit = ROOT / "Greenhub" / "data" / "global_audit_package"
    global_path = f"Pre-treatment/Mechanical/{NAME}"

    assert len(rows) == 300
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert {row["source_id"] for row in rows} == {"SRC-STODKILDE-2021-AFST"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["plant_species"] for row in rows} == {
        "Lucerne", "Red clover", "White clover", "Perennial ryegrass", "Tall fescue"
    }
    assert {row["harvest_date"] for row in rows} == {"17 May", "24 May", "31 May", "6 June"}
    assert all(row["value_numeric"] for row in rows)
    assert all(row["pooled_model_sem"] for row in rows)
    assert all("not date-specific" in row["sem_scope"] for row in rows)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["STODKILDE21-PRG-MAY17-SINGLE_PRESS_PULP-NITROGEN_CONTENT"]["value_numeric"] == "31.2"
    assert by_id["STODKILDE21-PRG-JUN06-DOUBLE_PRESS_CONCENTRATE-NITROGEN_CONTENT"]["value_numeric"] == "47.0"
    assert by_id["STODKILDE21-TF-JUN06-SINGLE_PRESS_CONCENTRATE-NITROGEN_RECOVERY_TO_PROTEIN_CONCENTRATE"]["value_numeric"] == "160.2"
    ocr = by_id["STODKILDE21-RC-MAY17-FEED-DRY_MATTER_CONTENT"]
    assert ocr["value_numeric"] == "128.1"
    assert ocr["validation_status"] == "ocr_digit_reconciled_against_published_species_lsmean"
    assert "12.81b" in ocr["reported_value_text"]

    assert sidecar["doi"] == "10.1016/j.anifeedsci.2021.115016"
    assert sidecar["license"].startswith("CC BY")
    assert sidecar["activation_state"] == "reference_only"
    assert "do not pool or average" in " ".join(sidecar["limitations"])
    assert "not forced to equal" in " ".join(sidecar["limitations"])
    assert sum(row["source_id"] == "SRC-STODKILDE-2021-AFST" for row in source_register) == 1
    assert sum(row["filename"] == NAME and row["row_count"] == "300" for row in manifest) == 1

    global_manifest = next(row for row in _rows(audit / "global_dataset_manifest.csv") if row["dataset_path"] == global_path)
    readiness = next(row for row in _rows(audit / "global_dataset_readiness.csv") if row["dataset_path"] == global_path)
    checksum = next(row for row in _rows(audit / "source_dataset_checksums.csv") if row["dataset_path"] == global_path)
    assert global_manifest["row_count_observed"] == "300"
    assert readiness["readiness"] == "D3"
    assert readiness["numeric_rows"] == "300"
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    asset = next(row for row in catalog if row["relative_path"].endswith(NAME))
    assert asset["source_ids"] == "SRC-STODKILDE-2021-AFST"
    assert asset["readiness"] == "reference_only"
