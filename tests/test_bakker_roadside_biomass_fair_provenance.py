from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"


def _rows(name: str, delimiter: str = ",") -> list[dict[str, str]]:
    with (DATA_DIR / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def test_bakker_roadside_biomass_data_and_derived_files_have_fair_metadata() -> None:
    raw = _rows("Biomass.csv", delimiter=";")
    summary = _rows("mowing_regime_biomass_summary.csv")
    site_productivity = _rows("roadside_grass_site_productivity_2023.csv")
    manifest = _rows("dataset_manifest.csv")

    assert len(raw) == 120
    assert len({row["Roadverge"] for row in raw}) == 10
    assert sum(not row["Biomass"].strip() for row in raw) == 1
    assert len(summary) == 12
    assert len(site_productivity) == 10

    manifest_by_file = {}
    for row in manifest:
        assert row["file_name"] not in manifest_by_file
        manifest_by_file[row["file_name"]] = row
    expected = {
        "Biomass.csv": "120",
        "mowing_regime_biomass_summary.csv": "12",
        "roadside_grass_site_productivity_2023.csv": "10",
    }
    for filename, count in expected.items():
        assert manifest_by_file[filename]["row_count"] == count

    raw_metadata = json.loads((DATA_DIR / "Biomass.csv.source.json").read_text(encoding="utf-8"))
    summary_metadata = json.loads(
        (DATA_DIR / "mowing_regime_biomass_summary.csv.source.json").read_text(encoding="utf-8")
    )
    site_metadata = json.loads(
        (DATA_DIR / "roadside_grass_site_productivity_2023.csv.source.json").read_text(encoding="utf-8")
    )

    assert raw_metadata["rows"] == len(raw)
    assert raw_metadata["doi_resolution_status"].startswith("resolved_by_zenodo_record_metadata")
    assert raw_metadata["dataset_doi"] == "10.5281/zenodo.15349657"
    assert raw_metadata["concept_doi"] == "10.5281/zenodo.15349656"
    assert "CC BY 4.0" in raw_metadata["license"]
    assert raw_metadata["runtime_parameter_mapping"] is None
    assert summary_metadata["rows"] == len(summary)
    assert site_metadata["rows"] == len(site_productivity)
    assert summary_metadata["activation_state"] == site_metadata["activation_state"] == "staged_evidence"
