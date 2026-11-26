import csv
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_dataset_reuse_catalog


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Protein recovery/Isoelectric/halophyte_green_juice_protein_recovery_aquacombine_2022_reference.csv"
SIDECAR = DATA.with_name(DATA.name + ".source.json")
MANIFEST = DATA.parent / "dataset_manifest.csv"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_aquacombine_reference_values_are_source_linked_and_scope_limited():
    rows = _rows(DATA)
    by_id = {row["record_id"]: row for row in rows}
    assert len(rows) == len(by_id) == 27
    assert {row["material_id"] for row in rows} == {
        "Salicornia_ramosissima_RSR",
        "Tripolium_pannonicum_LUH",
        "Saline_halophyte_juice",
    }
    assert all(row["source_location"] for row in rows)

    # Table 4 outcomes and the table's explicit denominator definitions.
    assert by_id["AQC22-SR-LP-PH35-DM-RECOVERY"]["value"] == "14.07"
    assert by_id["AQC22-SR-LP-PH35-DM-RECOVERY"]["basis"] == "DM_in_PEC_divided_by_incoming_juice_DM"
    assert by_id["AQC22-SR-LP-PH40-CP-RECOVERY"]["value"] == "36.86"
    assert by_id["AQC22-SR-LP-PH40-CP-RECOVERY"]["p_value_table_group"] == "0.496"

    # Acid addition remains an upper bound, not a calculated dose.
    acid = by_id["AQC22-HCL-VOLUME-BOUND"]
    assert acid["value"] == "<1"
    assert acid["unit"] == "mL_7.7M_HCl_per_200mL_juice"
    assert "Strict source bound" in acid["basis"]

    metadata = json.loads(SIDECAR.read_text(encoding="utf-8"))
    assert metadata["quality_class"] == "B"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["data_scope_class"] == "technology_and_material_specific"
    assert metadata["context_independent"] is False
    assert "not mapped to GreenHub" in metadata["runtime_mapping"]
    assert any("HCl" in item for item in metadata["limitations"])

    manifest_row = next(row for row in _rows(MANIFEST) if row["filename"] == DATA.name)
    assert manifest_row["row_count"] == "27"
    assert manifest_row["integration_readiness"] == "reference_only"

    catalog_row = next(row for row in build_dataset_reuse_catalog() if row["filename"] == DATA.name)
    assert catalog_row["data_scope_class"] == "technology_and_material_specific"
    assert catalog_row["context_independent"] is False
    assert catalog_row["source_ids"] == ["SRC-AQUACOMBINE-D5.6-2022"]
    assert catalog_row["source_metadata_gaps"] == []
    assert catalog_row["technology_family_ids"] == ["protein_recovery"]
