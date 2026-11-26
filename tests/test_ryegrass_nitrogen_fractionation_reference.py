import csv
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
FEED_DIR = ROOT / "Greenhub/data/Pre-treatment/Feedstock"


def _rows(filename):
    with (FEED_DIR / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_lefevre_free_amino_acid_values_are_traceable_reference_only_observations():
    filename = "perennial_ryegrass_free_amino_acids_lefevre_1991_reference.csv"
    rows = _rows(filename)
    assert {row["plant_part"]: float(row["reported_value"]) for row in rows} == {
        "Stubble": 23.0,
        "Leaves": 15.0,
        "Roots": 14.0,
    }
    assert all(row["reported_unit"] == "mg/g" for row in rows)
    assert all(row["normalized_unit"] == "g/kg" for row in rows)
    assert all(float(row["normalized_value"]) == float(row["reported_value"]) for row in rows)

    sidecar = json.loads((FEED_DIR / f"{filename}.source.json").read_text(encoding="utf-8"))
    assert sidecar["doi"] == "10.1093/jxb/42.1.89"
    assert sidecar["record_count"] == len(rows)
    assert sidecar["readiness_state"] == "reference_only_not_D4"
    assert "not connected" in sidecar["activation_state"].lower()


def test_goswami_willcox_nitrogen_fractions_keep_the_reported_n_basis_and_residual_visible():
    filename = "perennial_ryegrass_nitrogen_fractions_goswami_willcox_1969_reference.csv"
    rows = _rows(filename)
    assert [float(row["n_application_kg_ha"]) for row in rows] == [60, 120, 250, 500]
    fraction_columns = (
        "protein_n_percent_total_n",
        "peptide_n_percent_total_n",
        "free_amino_acid_n_percent_total_n",
        "nitrate_nitrite_n_percent_total_n",
        "other_organic_n_percent_total_n",
    )
    for row in rows:
        reported_sum = sum(float(row[column]) for column in fraction_columns)
        assert reported_sum == pytest.approx(float(row["reported_fraction_sum_percent"]))
        assert 100.0 - reported_sum == pytest.approx(float(row["unassigned_residual_percent_not_a_measured_pool"]))
        assert row["reported_basis"].startswith("Mean across cuts/stages")
        assert row["primary_source_doi"] == "10.1002/jsfa.2740201005"
        assert row["transcription_source_location"].startswith("Table 3 p.110")

    sidecar = json.loads((FEED_DIR / f"{filename}.source.json").read_text(encoding="utf-8"))
    assert sidecar["record_count"] == len(rows)
    assert sidecar["transcription_source_url"].endswith("/4131")
    assert "secondary table" in sidecar["limitations"][-1].lower()
    assert sidecar["readiness_state"] == "reference_only_not_D4"


def test_ryegrass_fractionation_benchmarks_do_not_silently_replace_active_greenhub_composition():
    profile = json.loads(
        (FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8")
    )
    for component in ("Peptides", "AminoAcids"):
        row = profile["compounds"][component]
        assert row["data_class"] is None
        assert row["record_role"] == "unmeasured_model_fallback"
        assert row["input_status"] == "not_measured_numeric_fallback"
        assert "compatibility fallback" in row["source"]["basis"]
        assert row["wet_mass_fraction"] > 0.0
    assert profile["compounds"]["Peptides"]["wet_mass_fraction"] == pytest.approx(0.0008426)
    assert profile["compounds"]["AminoAcids"]["wet_mass_fraction"] == pytest.approx(0.0008426)
