import csv
import hashlib
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_dataset_reuse_catalog


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "AD kinetics"
FILENAME = "bmp_interlaboratory_hafner_2026_bottle_calculated_reference.csv"


def test_hafner_interlaboratory_bmp_data_is_traceable_and_not_a_process_default():
    path = DATA / FILENAME
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    sidecar = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))

    assert len(rows) == 619
    assert len(rows[0]) == 8
    assert len({row["bottle_id"] for row in rows}) == len(rows)
    assert len({row["lab_id"] for row in rows}) == 31
    assert set(row["substrate"] for row in rows) == {
        "Bird feed", "Cellulose", "Rabbit feed", "Sunflower seeds", "Wheat straw", "Whey"
    }
    assert min(float(row["bmp_calc"]) for row in rows) == 107.8
    assert max(float(row["bmp_calc"]) for row in rows) == 1208.0
    assert all(row["bmp_calc"] and row["fv_inoc"] for row in rows)

    assert sidecar["source_id"] == "SRC-HAFNER-IL-BMP-2026"
    assert sidecar["publication_doi"] == "10.1016/j.biortech.2026.134136"
    assert "CC BY 4.0" in sidecar["license"]
    assert sidecar["activation_state"] == "reference_only"
    assert sidecar["calculation_connected"] is False
    assert "not a continuous-process" in sidecar["basis"]
    assert "no uncertainty column" in sidecar["uncertainty"]

    catalog = {row["filename"]: row for row in build_dataset_reuse_catalog()}
    asset = catalog[FILENAME]
    assert asset["technology_family_id"] == "anaerobic_digestion"
    assert asset["technology_subgroup"] == "AD assay validation"
    assert asset["technology_family_ids"] == ["anaerobic_digestion"]
    assert asset["data_scope_class"] == "technology_specific"
    assert asset["portability_review_status"] == "rule_inferred_review_required"
    assert asset["data_status_values"] == "reference_only"
    assert asset["activation_state"] == "reference_only"
    assert asset["source_metadata_gaps"] == []
    assert sidecar["source_url"] in asset["source_urls"]
    families = json.loads((ROOT / "Greenhub/data/platform/technology_families.json").read_text(encoding="utf-8"))
    ad_family = next(item for item in families["families"] if item["family_id"] == "anaerobic_digestion")
    assert "interlaboratory BMP assay quality and reproducibility" in ad_family["technology_subfamilies"]

    source_path = "Bigas production + upgrade/AD kinetics/" + FILENAME
    with (ROOT / "Greenhub/data/global_audit_package/global_dataset_manifest.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        manifest = {row["dataset_path"]: row for row in csv.DictReader(handle)}
    assert manifest[source_path]["row_count_observed"] == "619"
    assert manifest[source_path]["subgroup"] == "AD assay validation"

    with (ROOT / "Greenhub/data/global_audit_package/source_dataset_checksums.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        checksums = {row["dataset_path"]: row for row in csv.DictReader(handle)}
    assert checksums[source_path]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    with (ROOT / "Greenhub/data/global_audit_package/dataset_activation_matrix.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        activation = {row["dataset_path"]: row for row in csv.DictReader(handle)}
    assert activation[source_path]["integration_eligibility"] == "reference_only"
    assert activation[source_path]["default_eligibility"] == "False"
    assert activation[source_path]["calculation_connected"] == "False"
    assert activation[source_path]["active"] == "False"
