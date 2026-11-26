from __future__ import annotations

import csv
from pathlib import Path

from Greenhub.feedstock_proxy import feedstock_proxy_resolution_candidates, load_feedstock_proxies


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data" / "Pre-treatment" / "Feedstock"
FILENAME = "roadside_grass_composition_scientific.csv"
TITLE = "Biomass Pre-Extraction as a Versatile Strategy to Improve Biorefinery Feedstock Flexibility, Sugar Yields, and Lignin Purity"


def _smit_rows() -> list[dict[str, str]]:
    with (DATA / FILENAME).open(encoding="utf-8-sig", newline="") as stream:
        return [row for row in csv.DictReader(stream) if row["source_title"] == TITLE]


def test_smit_table_1_roadside_grass_values_are_traceable_and_non_default() -> None:
    rows = _smit_rows()
    values = {row["parameter_id"]: row for row in rows}

    expected = {
        "water_soluble_extractives": "1.5",
        "solvent_soluble_extractives": "1.8",
        "solid_cellulose": "34.4",
        "solid_hemicellulose": "24.0",
        "xylan": "19.4",
        "arabinan": "3.3",
        "galactan": "1.2",
        "mannan": "0.0",
        "rhamnan": "0.1",
        "solid_lignin": "16.9",
        "fresh_ash": "4.2",
        "liquor_absorbing_capacity": "4.0",
        "acid_neutralizing_capacity": "0.31",
    }
    # Three Smit records (bulk density, protein and extractive sugars) predate this extract.
    assert len(rows) == len(expected) + 3
    assert {key: values[key]["value_original"] for key in expected} == expected
    assert all(row["doi"] == "10.1021/acssuschemeng.2c00838" for row in rows)
    assert all(row["evidence_quality"] == "high" for row in rows)
    table_rows = [values[key] for key in expected]
    assert all("Table 1" in row["page_table_figure"] for row in table_rows)
    assert all("not a seasonal or site-representative mean" in row["applicability_note"] for row in table_rows)
    assert values["solid_hemicellulose"]["equation"] == "xylan + arabinan + galactan + mannan + rhamnan"
    assert values["solid_hemicellulose"]["evidence_status"] == "derived_from_reported_values"
    assert "does not restate it row-by-row" in values["solid_cellulose"]["limitation_note"]

    proxies = load_feedstock_proxies()
    assert "cellulose_dry_basis" not in proxies
    assert "hemicellulose_dry_basis" not in proxies
    assert "lignin_dry_basis" not in proxies
    # The existing GreenHub default-eligible feed profile is preserved.
    assert proxies["ash_dry_basis"].parameter_id == "fresh_ash"
    assert proxies["ash_dry_basis"].value == 0.179

    candidates = feedstock_proxy_resolution_candidates()
    for parameter_id in ("solid_cellulose", "solid_hemicellulose", "solid_lignin"):
        candidate = next(item for item in candidates if item.parameter_id == parameter_id and item.source_title == TITLE)
        assert candidate.can_activate_by_default is False


def test_smit_table_1_rows_are_registered_as_reference_only() -> None:
    with (DATA / "source_register.csv").open(encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))
    source = next(row for row in sources if row["source_id"] == "SRC-SMIT-2022")
    assert "Table 1" in source["quality_notes"]
    assert "no GreenHub default" in source["quality_notes"]

    with (DATA / "dataset_manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    dataset = next(row for row in manifest if row["file_name"] == FILENAME)
    assert dataset["row_count"] == "200"
    assert "reference_only" in dataset["integration_readiness"]
