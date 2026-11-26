from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "storage"
SOURCE_ID = "SRC-ASSIS-RYEGRASS-ENSILING-2026"
FILES = {
    "feed": ("wilted_ryegrass_ensiling_feed_properties_assis_2026_reference.csv", 14),
    "fermentation": ("wilted_ryegrass_ensiling_fermentation_assis_2026_reference.csv", 19),
    "losses": ("wilted_ryegrass_ensiling_losses_aerobic_stability_assis_2026_reference.csv", 14),
}


def _read_csv(path: Path, *, require_well_formed: bool = True) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        if require_well_formed:
            assert all(None not in row for row in rows), f"Malformed CSV row in {path.name}"
        return list(reader.fieldnames), rows


def test_assis_tables_preserve_reported_values_and_reference_only_status() -> None:
    loaded: dict[str, list[dict[str, str]]] = {}
    for kind, (filename, expected_rows) in FILES.items():
        path = DATA / filename
        header, rows = _read_csv(path)
        loaded[kind] = rows
        assert len(rows) == expected_rows
        assert len({row["record_id"] for row in rows}) == expected_rows
        assert all(row["source_id"] == SOURCE_ID for row in rows)
        assert all(row["evidence_class"] == "B_measured" for row in rows)
        assert all(row["activation_state"] == "reference_only" for row in rows)

        metadata = json.loads(path.with_suffix(path.suffix + ".source.json").read_text(encoding="utf-8"))
        assert metadata["persistent_identifier"] == "doi:10.37496/rbz5520250112"
        assert metadata["activation_state"] == "reference_only"
        assert metadata["calculation_connected"] is False
        assert metadata["runtime_parameter_mapping"] is None
        assert "Dutch roadside grass" in " ".join(metadata["limitations"])
        assert "CC BY 4.0" in metadata["license"]

        manifest = {row["filename"]: row for row in _read_csv(DATA / "dataset_manifest.csv")[1]}
        assert manifest[filename]["row_count"] == str(expected_rows)
        assert manifest[filename]["integration_status"] == "traceable_reference_only_not_runtime_eligible"
        assert manifest[filename]["primary_key"] == "record_id"

    feed = {row["property"]: row for row in loaded["feed"]}
    assert feed["dry_matter_60C"]["harvest_32dm_value"] == "324"
    assert feed["crude_protein"]["harvest_45dm_value"] == "170"
    assert feed["neutral_detergent_fiber"]["unit"] == "g/kg DM"

    fermentation = {row["property"]: row for row in loaded["fermentation"]}
    assert fermentation["lactic_acid"]["dm32_ino"] == "21.8a"
    assert fermentation["lactic_acid"]["dm45_mean"] == "14.1"
    assert fermentation["yeasts"]["dm32_control"] == "<10^4"
    assert fermentation["yeasts"]["dm32_mean"] == "-"
    assert fermentation["crude_protein"]["p_dm_by_inoculant"] == "0.007"

    losses = {row["property"]: row for row in loaded["losses"]}
    assert losses["dry_matter_loss"]["dm32_ino"] == "-21.6c"
    assert losses["gas_loss"]["dm32_ino"] == "-21.9c"
    assert losses["dry_matter_loss_during_aerobic_exposure"]["dm45_control"] == "263.4a"
    assert losses["aerobic_stability"]["dm45_control"] == "228b"
    assert "10 days" in losses["dry_matter_loss_during_aerobic_exposure"]["basis"]
    assert "technical failure" in losses["pH_day_18"]["notes"]


def test_assis_source_register_and_fair_catalog_linkage() -> None:
    source_rows = _read_csv(DATA / "source_register.csv", require_well_formed=False)[1]
    source = next(row for row in source_rows if row["source_id"] == SOURCE_ID)
    assert source["doi_or_stable_identifier"] == "10.37496/rbz5520250112"
    assert "CC BY 4.0" in source["quality_notes"]

    catalog_path = ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assets = {Path(asset["relative_path"]).name: asset for asset in catalog["assets"]}
    for filename, _ in FILES.values():
        asset = assets[filename]
        assert SOURCE_ID in asset["source_ids"].split(";")
        assert "10.37496/rbz5520250112" in asset["source_urls"]
