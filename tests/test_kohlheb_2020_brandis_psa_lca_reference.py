import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "Greenhub/data/Bigas production + upgrade/PSA"
FILENAME = "kohlheb_2020_brandis_fullscale_psa_lca_reference.csv"


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames
        assert all(None not in row and all(value is not None for value in row.values()) for row in rows)
        return rows


def test_brandis_psa_extract_preserves_data_boundaries_and_lca_basis():
    path = FOLDER / FILENAME
    rows = _read(path)
    metadata = json.loads(path.with_suffix(".source.json").read_text(encoding="utf-8"))
    records = {row["record_id"]: row for row in rows}

    assert len(rows) == metadata["record_count"] == 49
    assert len(records) == len(rows)
    assert metadata["doi"] == "10.1007/s12155-020-10205-9"
    assert "CC BY 4.0" in metadata["license"]
    assert metadata["calculation_connected"] is False
    assert {row["source_id"] for row in rows} == {"SRC-KOHLHEB-2020-BRANDIS-PSA"}
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert all(row["source_location"] and row["unit"] and row["basis"] for row in rows)

    assert records["KOH20-GAS-RAW-CH4"]["lower_bound"] == "51.4"
    assert records["KOH20-GAS-RAW-CH4"]["upper_bound"] == "52.2"
    assert records["KOH20-ELECTRICITY-ANNUAL"]["value_numeric"] == "2568985"
    assert records["KOH20-ELECTRICITY-SPECIFIC"]["value_numeric"] == "0.22"
    assert records["KOH20-CH4-AIR-EMISSION"]["value_numeric"] == "0.2"
    assert records["KOH20-CH4-AIR-EMISSION-ANNUAL"]["value_numeric"] == "12194"
    assert records["KOH20-CH4-FIGURE-LOSS"]["value_numeric"] == ""
    assert records["KOH20-CH4-FIGURE-LOSS"]["validation_status"] == "not_reconciled_with_operator_air_emission_value"
    assert "not reconciled" in records["KOH20-OPS-PRODUCT-DAY"]["basis"]
    assert records["KOH20-FU"]["value_numeric"] == "1"
    assert records["KOH20-LCA-GWP"]["value_numeric"] == "0.113"
    assert "cradle-to-gate" in records["KOH20-LCA-GWP"]["basis"]
    assert records["KOH20-LCA-AP"]["value_numeric"] == ""
    assert records["KOH20-LCA-AP"]["validation_status"] == "quarantined_impact_category_unit_missing"
    assert records["KOH20-TEA-ELECTRICITY-PRICE"]["quality_class"] == "C"
    assert "not stated" in records["KOH20-TEA-ELECTRICITY-PRICE"]["basis"]

    manifest = _read(FOLDER / "dataset_manifest.csv")
    assert FILENAME in {row["filename"] for row in manifest}
    source_register = _read(FOLDER / "source_register.csv")
    assert "SRC-KOHLHEB-2020-BRANDIS-PSA" in {row["source_id"] for row in source_register}

    relative = f"Bigas production + upgrade/PSA/{FILENAME}"
    audit = ROOT / "Greenhub/data/global_audit_package"
    global_manifest = next(row for row in _read(audit / "global_dataset_manifest.csv") if row["dataset_path"] == relative)
    assert global_manifest["detected_readiness"] == "D3"
    checksum = next(row for row in _read(audit / "source_dataset_checksums.csv") if row["dataset_path"] == relative)
    assert checksum["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()

    catalog = ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.csv"
    if catalog.exists():
        asset = next(row for row in _read(catalog) if row["relative_path"].endswith(FILENAME))
        assert "SRC-KOHLHEB-2020-BRANDIS-PSA" in asset["source_ids"]
        assert asset["readiness"] == "reference_only"
