import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Bigas production + upgrade/Feed BMP"
FILENAME = "alterra_2015_roadside_grass_dry_ad_reference.csv"


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_alterra_extract_is_traceable_and_reference_only():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    records = {row["record_id"]: row for row in rows}

    assert len(rows) == metadata["record_count"] == 156
    assert len(records) == len(rows)
    assert metadata["doi"] is None
    assert metadata["calculation_connected"] is False
    assert {row["source_id"] for row in rows} == {"SRC-ALTERRA-2661-ZWART-DEBOER-2015"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["source_location"] and row["unit"] and row["basis"] for row in rows)

    # The three feed samples close DM = organic matter + ash in the source table.
    for sample in ("SPRING_VERGE", "AUTUMN_VERGE", "SELLINGEN_NATURE"):
        dm = float(records[f"ALT15-T2-{sample}-DRY_MATTER"]["value_numeric"])
        om = float(records[f"ALT15-T2-{sample}-ORGANIC_MATTER"]["value_numeric"])
        ash = float(records[f"ALT15-T2-{sample}-ASH"]["value_numeric"])
        assert dm == om + ash

    assert records["ALT15-T4-AUTUMN_VERGE-PER-MATERIAL"]["value_numeric"] == "130"
    assert records["ALT15-LUFA-AUTUMN-BIOGAS-TEST"]["value_numeric"] == "123"
    assert records["ALT15-LUFA-AUTUMN-BIOGAS-TEST"]["validation_status"] == "measurement_reported_method_and_basis_incomplete"
    assert records["ALT15-OSTRA-MIX-GAS-NATURE"]["value_numeric"] == ""
    assert records["ALT15-OSTRA-MIX-GAS-NATURE"]["quality_class"] == "C"
    assert records["ALT15-T7-OSTRA-DIGESTATE-NATURE-NITRATE_N"]["value_text"] == "<0.01"
    assert records["ALT15-T7-OSTRA-DIGESTATE-NATURE-NITRATE_N"]["value_numeric"] == ""
    assert records["ALT15-T7-OSTRA-DIGESTATE-NATURE-NITRATE_N"]["validation_status"] == "below_reported_quantification_limit"
    assert records["ALT15-T7-OSTRA-DIGESTATE-MEADOW-DRY_MATTER"]["validation_status"] == "source_table_component_closure_difference_preserved"
    assert records["ALT15-T7-CHROMIUM-ROW-QUARANTINE"]["value_numeric"] == ""
    assert records["ALT15-T7-CHROMIUM-ROW-QUARANTINE"]["validation_status"] == "quarantined_source_alignment_ambiguity"
    assert records["ALT15-LCA-OPEN-DIGESTATE-CH4"]["value_numeric"] == ""
    assert records["ALT15-LCA-OPEN-DIGESTATE-CH4"]["validation_status"] == "not_reported_not_zero"

    manifest = _read(FOLDER / "dataset_manifest.csv")
    assert FILENAME in {row["filename"] for row in manifest}
    source_register = _read(FOLDER / "source_register.csv")
    assert "SRC-ALTERRA-2661-ZWART-DEBOER-2015" in {row["source_id"] for row in source_register}

    relative = f"Bigas production + upgrade/Feed BMP/{FILENAME}"
    audit = ROOT / "Greenhub/data/global_audit_package"
    global_manifest = next(row for row in _read(audit / "global_dataset_manifest.csv") if row["dataset_path"] == relative)
    assert global_manifest["detected_readiness"] == "D3"
    checksum = next(row for row in _read(audit / "source_dataset_checksums.csv") if row["dataset_path"] == relative)
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    catalog = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv"
    if catalog.exists():
        asset = next(row for row in _read(catalog) if row["relative_path"].endswith(FILENAME))
        assert "SRC-ALTERRA-2661-ZWART-DEBOER-2015" in asset["source_ids"]
        assert asset["readiness"] == "reference_only"
