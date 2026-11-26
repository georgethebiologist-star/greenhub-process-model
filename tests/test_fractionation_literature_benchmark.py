import csv
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Greenhub/data/Pre-treatment/Mechanical/greenhub_mechanical_pretreatment_pressing_data.csv"
DOI = "10.1038/s44264-026-00189-y"


def test_tuv_grass_clover_fractionation_table_closes_without_double_counting_juice():
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["record_id"]: row for row in csv.DictReader(stream)}
    selected = {f"M{number:03d}": rows[f"M{number:03d}"] for number in range(95, 107)}

    assert all(row["source_id"] == "S11_ELSHANI_2026" for row in selected.values())
    assert all(row["confidence_class"] == "B" for row in selected.values())
    assert all(row["source_url_or_doi"].endswith(DOI) for row in selected.values())
    assert all("Report-only" in row["activation_recommendation"] for row in selected.values())

    values = {
        row["response_parameter"]: float(row["normalized_value"])
        for row in selected.values()
    }
    wet_final = (
        values["Press pulp fresh mass"]
        + values["Protein concentrate fresh mass"]
        + values["Brown juice fresh mass"]
        + values["Unrecovered mass fresh basis"]
    )
    dry_final = (
        values["Press pulp dry matter"]
        + values["Protein concentrate dry matter"]
        + values["Brown juice dry matter"]
        + values["Unrecovered mass dry matter"]
    )
    feed_wet = values["Forage biomass input fresh mass"]
    feed_dm = values["Forage biomass input dry matter"]
    green_juice_intermediate = values["Green juice fresh mass"]

    assert wet_final == 5264.0
    assert abs(wet_final - feed_wet) <= 1.0
    assert dry_final == feed_dm == 1000.0
    assert green_juice_intermediate == 2311.0
    assert green_juice_intermediate + wet_final > feed_wet  # proves intermediate is not an extra final output


def test_tuv_fractionation_benchmark_is_doi_findable_in_fair_catalog():
    catalog = json.loads(
        (ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8")
    )
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"] == "Greenhub/data/Pre-treatment/Mechanical/greenhub_mechanical_pretreatment_pressing_data.csv"
    )
    assert "S11_ELSHANI_2026" in asset["source_ids"]
    assert DOI in asset["source_dois"]
    assert asset["source_metadata_status"] in {"linked_to_source_register", "linked_to_local_source_record"}


def test_ayanfe_fresh_grass_press_benchmarks_retain_original_feed_basis():
    doi = "10.1016/j.biteb.2023.101356"
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["record_id"]: row for row in csv.DictReader(stream)}
    selected = {f"M{number:03d}": rows[f"M{number:03d}"] for number in range(107, 123)}

    assert all(row["source_id"] == "S12_AYANFE_2023" for row in selected.values())
    assert all(row["confidence_class"] == "B" for row in selected.values())
    assert all(row["source_url_or_doi"].endswith(doi) for row in selected.values())
    assert all("Report-only" in row["activation_recommendation"] for row in selected.values())

    catalog = json.loads(
        (ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8")
    )
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"] == "Greenhub/data/Pre-treatment/Mechanical/greenhub_mechanical_pretreatment_pressing_data.csv"
    )
    assert "S12_AYANFE_2023" in asset["source_ids"]
    assert doi in asset["source_dois"]
    assert asset["source_metadata_status"] in {"linked_to_source_register", "linked_to_local_source_record"}

    by_response = {row["response_parameter"]: row for row in selected.values()}
    assert len(selected) == 16
    assert by_response["Liquid yield"]["normalized_unit"] == "kg liquid/kg fresh feed"
    assert by_response["CP retained in liquid"]["normalized_unit"] == "g CP/g original fresh material"

    # Methods §2.3 computes CP retained per original fresh feed mass. It is
    # not a fraction of the feed's initial CP inventory.
    feed_dm_g_per_kg = 218.0
    feed_cp_g_per_kg_dm = 123.0
    expected = {
        ("Lab-scale pneumatic press", "fresh untreated control"): 0.008,
        ("Lab-scale pneumatic press", "formic-propionic acid additive"): 0.052,
        ("Lab-scale twin-screw press", "fresh untreated control"): 0.403,
        ("Lab-scale twin-screw press", "formic-propionic acid additive"): 0.249,
    }
    for (press, treatment), expected_retained in expected.items():
        matches = [
            row for row in selected.values()
            if row["equipment_type"] == press
            and treatment in row["equipment_settings"]
        ]
        metric = {row["response_parameter"]: float(row["normalized_value"]) for row in matches}
        reconstructed_retained = (
            metric["Liquid yield"]
            * metric["Liquid dry matter concentration"]
            * metric["Liquid CP concentration"]
            / (feed_dm_g_per_kg * feed_cp_g_per_kg_dm)
        )
        assert metric["CP retained in liquid"] == pytest.approx(expected_retained)
        # Table values and Table 1 feed composition are rounded; retain a
        # 0.003 absolute tolerance rather than treating rounded inputs as exact.
        assert reconstructed_retained == pytest.approx(expected_retained, abs=0.003)


def test_ayanfe_full_preservation_press_matrix_is_complete_and_traceable():
    matrix_path = ROOT / "Greenhub/data/Pre-treatment/Mechanical/ayanfe_2023_full_preservation_press_matrix_reference.csv"
    source_path = matrix_path.with_suffix(".source.json")
    with matrix_path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    source = json.loads(source_path.read_text(encoding="utf-8"))

    assert len(rows) == 14
    assert {row["press_type"] for row in rows} == {"LPP", "LTS"}
    assert all(sum(row["press_type"] == press for row in rows) == 7 for press in {"LPP", "LTS"})
    treatment_columns = {
        "FR_control", "FR_FPA", "FZ_control", "FZ_FPA", "DR_control", "EN_control", "EN_FPA"
    }
    assert all(treatment_columns <= row.keys() for row in rows)
    assert all(all(row[column] for column in treatment_columns) for row in rows)
    assert all(row["source_id"] == "S12_AYANFE_2023" for row in rows)
    assert {row["source_doi"] for row in rows} == {"10.1016/j.biteb.2023.101356"}
    assert source["evidence_class"] == "B"
    assert source["dataset_id"] == "urn:greenhub:dataset:ayanfe-biteb-2023-table2:v1"
    assert source["related_publication"] == "https://doi.org/10.1016/j.biteb.2023.101356"
    assert source["license"] == "CC BY 4.0"
    assert "reference-only" in " ".join(source["limitations"]).lower()

    cp_retained = next(
        row for row in rows
        if row["press_type"] == "LPP" and row["response_parameter"] == "CP retained in liquid"
    )
    assert cp_retained["reported_unit"] == "g CP/g original fresh material"
    assert cp_retained["FR_control"] == "0.008"
    assert cp_retained["EN_control"] == "0.356"


def test_pilot_perennial_ryegrass_screw_press_quality_data_are_report_only_and_traceable():
    doi = "10.1038/s41538-026-00831-6"
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        rows = {row["record_id"]: row for row in csv.DictReader(stream)}
    selected = {f"M{number}": rows[f"M{number}"] for number in range(123, 127)}

    assert all(row["source_id"] == "S13_SANDOVAL_2026" for row in selected.values())
    assert all(row["confidence_class"] == "B" for row in selected.values())
    assert all(row["source_url_or_doi"].endswith(doi) for row in selected.values())
    assert all("Report-only" in row["activation_recommendation"] for row in selected.values())

    metrics = {row["response_parameter"]: row for row in selected.values()}
    assert metrics["Raw grass juice volume yield"]["normalized_unit"] == "L raw juice/kg fresh PRG"
    assert float(metrics["Raw grass juice volume yield"]["normalized_value"]) == pytest.approx(610 / 1500)
    assert float(metrics["Raw grass juice dry matter concentration"]["normalized_value"]) == pytest.approx(0.0513)
    assert float(metrics["Raw grass juice crude protein concentration"]["normalized_value"]) == pytest.approx(0.160)
    assert "density" in metrics["Raw grass juice volume yield"]["notes"]

    source = json.loads(
        (ROOT / "Greenhub/data/Pre-treatment/Mechanical/prg_screw_press_pilot_benchmark.source.json").read_text(encoding="utf-8")
    )
    assert source["dataset_id"] == f"https://doi.org/{doi}"
    assert source["evidence_class"] == "B"

    catalog = json.loads(
        (ROOT / "Greenhub/data/fair_input_catalog/master_input_catalog.json").read_text(encoding="utf-8")
    )
    asset = next(
        row for row in catalog["assets"]
        if row["relative_path"] == "Greenhub/data/Pre-treatment/Mechanical/greenhub_mechanical_pretreatment_pressing_data.csv"
    )
    assert "S13_SANDOVAL_2026" in asset["source_ids"]
    assert doi in asset["source_dois"]
    assert asset["source_metadata_status"] in {"linked_to_source_register", "linked_to_local_source_record"}


def test_combined_pressing_dataset_resolves_every_legacy_source_id():
    with DATASET.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    register_path = ROOT / "Greenhub/data/Pre-treatment/Mechanical/source_register.csv"
    with register_path.open(encoding="utf-8-sig", newline="") as stream:
        sources = {row["source_id"]: row for row in csv.DictReader(stream)}

    used_ids = {row["source_id"] for row in rows}
    assert used_ids <= sources.keys()
    assert sources["S04_HANSEN_2022"]["doi_or_stable_identifier"] == "10.3390/foods11203229"
    assert sources["S08_ZOPPI_2023"]["doi_or_stable_identifier"] == "10.1016/j.clcb.2023.100064"
    assert sources["S08_ZOPPI_2023"]["title"] == "Biorefinery integration of a green protein platform for maximum resource utilization"

    zopp = [row for row in rows if row["source_id"] == "S08_ZOPPI_2023"]
    assert len(zopp) == 4
    assert all(row["source_title"] == sources["S08_ZOPPI_2023"]["title"] for row in zopp)
    assert all(row["source_url_or_doi"] == "https://doi.org/10.1016/j.clcb.2023.100064" for row in zopp)
