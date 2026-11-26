from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
BMP = ROOT / "Greenhub" / "data" / "Bigas production + upgrade" / "Feed BMP"
FILES = {
    "elements": (FEED / "urban_roadside_grass_elemental_composition_piepenschneider_2015_reference.csv", 34),
    "press_cake": (FEED / "urban_roadside_grass_press_cake_quality_piepenschneider_2016_reference.csv", 14),
    "bmp": (BMP / "roadside_verge_bmp_summary_statistics_piepenschneider_2016_reference.csv", 18),
}


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row for row in rows), f"Malformed CSV row in {path.name}"
        return list(reader.fieldnames), rows


def test_composition_and_product_tables_preserve_reported_scope_and_missingness() -> None:
    _, elements = _read(FILES["elements"][0])
    _, cake = _read(FILES["press_cake"][0])
    assert len(elements) == 34
    assert len({row["observation_id"] for row in elements}) == len(elements)
    assert all(row["quality_class"] == "B" and row["activation_state"] == "reference_only" for row in elements)

    element_index = {(row["management_regime"], row["analyte"]): row for row in elements}
    assert element_index[("2-cut", "Ca")]["reported_value"] == "6.86"
    assert element_index[("4-cut", "N")]["reported_value"] == "2.09"
    for analyte, limit in (("Cd", "0.4"), ("Pb", "4")):
        for regime in ("2-cut", "4-cut"):
            row = element_index[(regime, analyte)]
            assert row["reported_value"] == ""
            assert row["qualifier"] == "below_detection_limit"
            assert row["detection_limit_value"] == limit
    for analyte in ("S", "Si"):
        missing = element_index[("4-cut", analyte)]
        assert missing["qualifier"] == "not_reported"
        assert missing["reported_value"] == ""

    cake_index = {(row["harvest_cut"], row["property"]): row for row in cake}
    assert cake_index[("1", "carbon")]["reported_mean"] == "43.49"
    assert cake_index[("2", "nitrogen")]["sample_count"] == "5"
    assert cake_index[("1", "higher_heating_value")]["value_origin"] == "source_calculated"
    assert cake_index[("2", "lower_heating_value")]["reported_sd"] == "0.44"
    assert all(row["activation_state"] == "reference_only" for row in cake)


def test_bmp_table_distinguishes_site_sample_counts_from_assay_replicates() -> None:
    _, rows = _read(FILES["bmp"][0])
    assert len(rows) == 18
    assert len({row["observation_id"] for row in rows}) == len(rows)
    lookup = {row["observation_id"]: row for row in rows}
    press_fluid_first_cut = lookup["PIP16-BMP-2CUT-PRESSFLUID-C1-SMY"]
    assert press_fluid_first_cut["reported_mean"] == "292"
    assert press_fluid_first_cut["reported_sd"] == "33"
    assert press_fluid_first_cut["sample_count"] == "10"
    assert "three digestion replicates" in press_fluid_first_cut["reference_conditions"]
    silage = lookup["PIP16-BMP-4CUT-SILAGE-C2-SMY"]
    assert silage["reported_mean"] == "241"
    assert silage["reported_unit"] == "L_N CH4/kg VS"
    assert "two digestion replicates" in silage["reference_conditions"]
    assert all(row["activation_state"] == "reference_only" for row in rows)


def test_dataset_sidecars_manifests_and_source_registers_link() -> None:
    feed_manifest = {row["file_name"]: row for row in _read(FEED / "dataset_manifest.csv")[1]}
    bmp_manifest = {row["filename"]: row for row in _read(BMP / "dataset_manifest.csv")[1]}
    for key, (path, count) in FILES.items():
        _read(path)
        metadata = json.loads(path.with_suffix(path.suffix + ".source.json").read_text(encoding="utf-8"))
        assert metadata["activation_state"] == "reference_only"
        assert metadata["calculation_connected"] is False
        assert metadata["runtime_parameter_mapping"] is None
        manifest = bmp_manifest[path.name] if key == "bmp" else feed_manifest[path.name]
        assert manifest["row_count"] == str(count)

    feed_sources = _read(FEED / "source_register.csv")[1]
    element_source = next(row for row in feed_sources if row["source_id"] == "SRC-PIEPENSCHNEIDER-ELEMENTS-2015")
    assert element_source["doi_or_stable_identifier"] == "10.1007/s11356-014-3881-9"
    bmp_sources = _read(BMP / "source_register.csv")[1]
    process_source = next(row for row in bmp_sources if row["source_id"] == "SRC-PIEPENSCHNEIDER-2016")
    assert process_source["doi_or_stable_id"] == "10.1016/j.biombioe.2015.12.012"

    catalog = json.loads((ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.json").read_text(encoding="utf-8"))
    assets = {Path(asset["relative_path"]).name: asset for asset in catalog["assets"]}
    for key, (path, _) in FILES.items():
        asset = assets[path.name]
        expected_source = "SRC-PIEPENSCHNEIDER-ELEMENTS-2015" if key == "elements" else "SRC-PIEPENSCHNEIDER-2016"
        assert expected_source in asset["source_ids"].split(";")
        assert "doi.org" in asset["source_urls"]
