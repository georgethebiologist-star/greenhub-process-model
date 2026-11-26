import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"


def _rows(relative_path):
    with (DATA / relative_path).open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_hansen_alfalfa_press_reference_preserves_pass_basis_and_source_only_status():
    rows = _rows(
        "Protein recovery/Mechanical/alfalfa_hansen_2022_repeated_pressing_quality_reference.csv"
    )
    assert len(rows) == 10
    assert all(row["quality_class"] == "B" for row in rows)
    assert all(row["activation_state"] == "reference_only" for row in rows)
    first, second, tenth = rows[0], rows[1], rows[9]
    assert (first["working_pressure_bar"], first["screw_speed_rpm"]) == ("6", "10")
    assert first["cumulative_total_protein_recovery_pct_at_this_pass"] == "16"
    assert second["cumulative_total_protein_recovery_pct_at_this_pass"] == "25"
    assert tenth["cumulative_total_protein_recovery_pct_at_this_pass"] == "48"
    assert tenth["material"] == "whole alfalfa including leaves and stalks"


def test_lin_pasture_grass_extraction_comparison_keeps_metrics_and_denominators_distinct():
    rows = _rows(
        "Protein recovery/Isoelectric/lin_2020_pasture_grass_extraction_method_comparison_reference.csv"
    )
    yields = {
        row["extraction_method"]: row["reported_mean"]
        for row in rows
        if row["measurement_parameter"] == "protein_extraction_yield"
    }
    purities = {
        row["extraction_method"]: row["reported_mean"]
        for row in rows
        if row["measurement_parameter"] == "protein_concentrate_purity"
    }
    assert yields == {
        "alkaline treatment": "1.1",
        "aqueous extraction": "0.1",
        "subcritical water extraction": "6.7",
    }
    assert purities == {
        "alkaline treatment": "9.8",
        "aqueous extraction": "8.9",
        "subcritical water extraction": "15.7",
    }
    assert all(row["basis"] for row in rows)
    assert all("not recovery" in row["limitations"] for row in rows if row["measurement_parameter"] == "protein_concentrate_purity")
    assert all(row["activation_state"] == "reference_only" for row in rows)


def test_brown_grass_htc_bmp_keeps_measured_vs_theoretical_bases_separate():
    rows = _rows("Bigas production + upgrade/AD kinetics/brown_2022_grass_htc_ad_bmp_reference.csv")
    by_id = {row["record_id"]: row for row in rows}
    assert by_id["BROWN22-GRASS-EBMP"]["reported_value"] == "261.2"
    assert by_id["BROWN22-GRASS-EBMP"]["value_type"] == "measured_mean"
    assert by_id["BROWN22-GRASS-TBMP"]["reported_value"] == "521.5"
    assert by_id["BROWN22-GRASS-TBMP"]["value_type"] == "source_calculated"
    assert by_id["BROWN22-GRASS-EBMP"]["unit"] == "mL CH4/g VS"
    assert all(row["activation_state"] == "reference_only" for row in rows)


def test_hoyos_carbonate_pilot_gas_composition_closes_without_becoming_a_recovery_factor():
    rows = _rows(
        "Bigas production + upgrade/Other_Upgrading/hoyos_2026_carbonate_biogas_upgrading_pilot_reference.csv"
    )
    measured = {
        row["parameter"]: float(row["reported_value"])
        for row in rows
        if row["measurement_class"] == "reported_product_gas_mean"
    }
    assert round(sum(measured.values()), 1) == 100.0
    assert measured == {
        "methane_fraction": 94.9,
        "carbon_dioxide_fraction": 1.7,
        "oxygen_fraction": 0.7,
        "nitrogen_fraction": 2.7,
    }
    assert all(row["activation_state"] == "reference_only" for row in rows)
    methane = next(row for row in rows if row["parameter"] == "methane_fraction")
    h2s = next(row for row in rows if row["parameter"] == "hydrogen_sulfide")
    assert "not commercial-scale energy" in methane["limitations"]
    assert "detection limit is not stated" in h2s["limitations"]
