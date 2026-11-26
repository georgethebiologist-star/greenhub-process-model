import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Mechanical"
FILENAME = "damborg_2019_thesis_press_protein_partition_ranges_reference.csv"
SOURCE_ID = "SRC-DAMBORG-GREEN-BIOREFINERY-THESIS-2019"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_damborg_thesis_ranges_preserve_denominators_and_reference_only_status():
    path = DATA / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    source_register = _rows(DATA / "source_register.csv")
    local_manifest = _rows(DATA / "dataset_manifest.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")
    global_manifest = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_manifest.csv")
    readiness_rows = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "global_dataset_readiness.csv")
    checksums = _rows(ROOT / "Greenhub" / "data" / "global_audit_package" / "source_dataset_checksums.csv")

    assert len(rows) == metadata["row_count"] == 4
    assert len({row["record_id"] for row in rows}) == 4
    assert {row["source_id"] for row in rows} == {SOURCE_ID}
    assert {row["quality_class"] for row in rows} == {"B"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}

    by_metric = {row["metric"]: row for row in rows}
    pulp = by_metric["crude_protein_mass_recovered_in_pulp"]
    concentrate = by_metric["crude_protein_mass_recovered_in_protein_concentrate"]
    assert (pulp["lower_bound"], pulp["upper_bound"], pulp["unit"]) == ("528", "669", "g/kg input crude protein")
    assert (concentrate["lower_bound"], concentrate["upper_bound"], concentrate["unit"]) == ("170", "261", "g/kg input crude protein")
    assert pulp["range_scope"] == concentrate["range_scope"]
    assert "not paired" in pulp["range_scope"]
    assert all("Range only; no SD" in row["uncertainty"] for row in rows)
    assert all("not_Dutch_roadside_or_VARTA" in row["transferability"] for row in rows)

    assert metadata["doi"] is None
    assert "related_peer_reviewed_article_doi" not in metadata
    assert metadata["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert any(row["source_id"] == SOURCE_ID for row in source_register)
    assert any(row["filename"] == FILENAME and row["row_count"] == "4" for row in local_manifest)

    asset = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert SOURCE_ID in asset["source_ids"]
    assert asset["readiness"] == "reference_only"
    global_path = f"Pre-treatment/Mechanical/{FILENAME}"
    assert next(row for row in global_manifest if row["dataset_path"] == global_path)["detected_readiness"] == "D3"
    assert next(row for row in readiness_rows if row["dataset_path"] == global_path)["numeric_rows"] == "4"
    assert next(row for row in checksums if row["dataset_path"] == global_path)["sha256"] == metadata["sha256_csv"]
