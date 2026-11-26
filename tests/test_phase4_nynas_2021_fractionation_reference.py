import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Greenhub" / "data" / "Protein recovery" / "Isoelectric"
FILENAME = "green_leaf_fractionation_yields_and_nitrogen_content_nynas_2021_reference.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def test_nynas_2021_fractionation_observations_preserve_provenance_and_denominators():
    path = DATA_DIR / FILENAME
    rows = _rows(path)
    metadata = json.loads(path.with_suffix(".csv.source.json").read_text(encoding="utf-8"))
    manifest = _rows(DATA_DIR / "dataset_manifest.csv")
    sources = _rows(DATA_DIR / "source_register.csv")
    catalog = _rows(ROOT / "Greenhub" / "data" / "fair_input_catalog" / "master_input_catalog.csv")

    assert len(rows) == 189
    assert len({row["record_id"] for row in rows}) == len(rows)
    assert Counter(row["table_panel"] for row in rows) == {"2a": 54, "2b": 36, "2c": 99}
    assert {row["source_id"] for row in rows} == {"SRC002"}

    panel_a = [row for row in rows if row["table_panel"] == "2a"]
    panel_b = [row for row in rows if row["table_panel"] == "2b"]
    panel_c = [row for row in rows if row["table_panel"] == "2c"]
    assert {row["basis"] for row in panel_a} == {"relative to initial biomass nitrogen"}
    assert {row["basis"] for row in panel_b} == {"relative to incoming fraction nitrogen"}
    assert {row["basis"] for row in panel_c} <= {
        "dry matter basis",
        "dry matter basis; biomass replicate N SD is in Table 1",
    }

    lucerne_full_process = next(
        row for row in panel_a
        if row["biomass"] == "Lucerne" and row["to_fraction"] == "S4"
    )
    assert float(lucerne_full_process["reported_mean"]) == 1.5
    assert float(lucerne_full_process["reported_sd"]) == 1.0
    assert lucerne_full_process["replicate_count"] == "1"
    lucerne_acid_step = next(
        row for row in panel_b
        if row["biomass"] == "Lucerne" and row["from_fraction"] == "S2"
    )
    assert float(lucerne_acid_step["reported_mean"]) == 16.1
    assert float(lucerne_acid_step["reported_sd"]) == 1.0
    assert lucerne_acid_step["basis"] != lucerne_full_process["basis"]
    lucerne_s4_n = next(
        row for row in panel_c
        if row["biomass"] == "Lucerne" and row["to_fraction"] == "S4"
    )
    assert float(lucerne_s4_n["reported_mean"]) == 4.0
    assert lucerne_s4_n["unit"] == "percent"
    assert lucerne_s4_n["basis"] == "dry matter basis"

    missing_carrot_p4 = next(
        row for row in panel_c
        if row["biomass"] == "Carrot" and row["to_fraction"] == "P4"
    )
    assert missing_carrot_p4["reported_mean"] == ""
    assert missing_carrot_p4["reporting_status"] == "not_reported"

    assert metadata["doi"] == metadata["source_doi"] == "10.3390/foods10112533"
    assert metadata["license"] == "CC BY 4.0"
    assert metadata["activation_state"] == "reference_only"
    assert metadata["calculation_connected"] is False
    assert "not roadside grass" in " ".join(metadata["limitations"])
    assert metadata["variable_definitions"]["table_2c"].endswith("not crude-protein content.")
    assert any(row["filename"] == FILENAME and row["row_count"] == "189" for row in manifest)
    source = next(row for row in sources if row["source_id"] == "SRC002")
    assert "Nynäs" in source["authors"]
    assert source["doi_or_stable_id"] == "10.3390/foods10112533"

    indexed = next(row for row in catalog if row["relative_path"].endswith(FILENAME))
    assert indexed["source_ids"] == "SRC002"
    assert indexed["source_dois"] == "10.3390/foods10112533"
    assert indexed["readiness"] == "reference_only"
    assert indexed["source_metadata_linkage"] == "direct_dataset_path"

