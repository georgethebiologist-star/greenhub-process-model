import csv
import json
from pathlib import Path

from biorefinery_platform.data_catalog import build_dataset_reuse_catalog


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub/data/Pre-treatment/Feedstock/perennial_ryegrass_seasonal_wsc_cp_olszewska_2021_reference.csv"
SIDECAR = DATA.with_suffix(".source.json")
PROFILE = ROOT / "Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json"


def _rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_olszewska_feed_composition_tables_are_transcribed_and_material_scoped():
    rows = _rows(DATA)
    by_id = {row["record_id"]: row for row in rows}
    assert len(rows) == 36
    assert len(by_id) == 36
    assert {row["property"] for row in rows} == {
        "water_soluble_carbohydrates", "crude_protein", "wsc_to_cp_ratio"
    }
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["value_status"] == "measured" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    assert all(row["data_scope_class"] == "material_or_site_specific" for row in rows)
    assert all(row["context_independent"] == "false" for row in rows)

    assert by_id["OLS21-WSC-N-120"]["reported_mean"] == "159.2"
    assert by_id["OLS21-WSC-N-120"]["unit"] == "g/kg DM"
    assert by_id["OLS21-CP-CUT-IV"]["reported_mean"] == "166.0"
    assert by_id["OLS21-RATIO-CULT-BARONKA"]["reported_mean"] == "1.11"
    assert by_id["OLS21-WSC-CULT-BARONKA"]["study_year_2014"] == "189.0"

    metadata = json.loads(SIDECAR.read_text(encoding="utf-8"))
    assert metadata["doi_or_stable_id"] == "10.3390/agronomy11030468"
    assert metadata["source_license"] == "CC BY 4.0"
    assert "marginal means" in metadata["experimental_conditions"]
    assert any("roadside-grass" in gap.lower() for gap in metadata["metadata_gaps"])

    catalog_row = next(
        row for row in build_dataset_reuse_catalog()
        if row["filename"] == DATA.name
    )
    assert catalog_row["data_scope_class"] == "material_or_site_specific"
    assert catalog_row["context_independent"] is False
    assert catalog_row["source_ids"] == ["SRC-OLSZEWSKA-2021-WSC-CP"]
    assert any("10.3390/agronomy11030468" in item for item in catalog_row["source_dois_or_stable_ids"])
    assert catalog_row["source_metadata_gaps"] == []
    assert catalog_row["detected_readiness"] == "D3"

    # The literature comparator must not silently become a GreenHub run default.
    feed_profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert "OLSZEWSKA" not in json.dumps(feed_profile).upper()
