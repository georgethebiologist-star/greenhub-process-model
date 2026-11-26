import csv
import json
from pathlib import Path

import pytest

from Greenhub.application.contracts.requests import _default_feed_composition


ROOT = Path(__file__).resolve().parents[1]
FEED_DIR = ROOT / "Greenhub/data/Pre-treatment/Feedstock"


def test_dashboard_planning_composition_references_are_derived_from_the_active_profile():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    measurements = {item["id"]: item for item in profile["analytical_reference"]["measurements"]}
    dry_matter_fraction = float(measurements["dry_matter_percent"]["value"]) / 100.0
    protein_wet_fraction = sum(
        profile["compounds"][component]["wet_mass_fraction"]
        for component in ("SolubleProtein", "SuspendedProtein")
    )

    expected = {
        "moisturePct": 100.0 - float(measurements["dry_matter_percent"]["value"]),
        "proteinPct": protein_wet_fraction / dry_matter_fraction * 100.0,
        "phosphorusPct": float(measurements["phosphorus_g_kg_dm"]["value"]) * dry_matter_fraction / 10.0,
    }
    assert expected["moisturePct"] == pytest.approx(85.7)
    assert expected["proteinPct"] == pytest.approx(10.7)
    assert expected["phosphorusPct"] == pytest.approx(0.04004)

    app = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "moisturePct: feedPlanningReferences.moisturePct" in app
    assert "proteinPct: feedPlanningReferences.proteinPct" in app
    assert "phosphorusPct: feedPlanningReferences.phosphorusPct" in app
    assert "const feedCompositionData = feedCompositionProfile.compounds" in app


def test_ui_analytical_reference_matches_the_varta_whole_grass_source_row():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    reference = profile["analytical_reference"]
    source_path = FEED_DIR / reference["source"]["source_csv"]
    with source_path.open(encoding="utf-8-sig", newline="") as source_file:
        rows = list(csv.DictReader(source_file))
    sample = next(row for row in rows if row["sample_name_english"] == reference["sample_name"])

    assert sample["sample_date"] == reference["sample_date"]
    assert sample["source_sheet"] == reference["source"]["source_sheet"]
    assert int(sample["source_row"]) == reference["source"]["source_row"]
    assert reference["data_class"] == "A"
    assert reference["source"]["source_workbook_sha256"] == json.loads(
        (FEED_DIR / "varta_2026_grass_fiber_measurements.csv.source.json").read_text(encoding="utf-8")
    )["source_workbook_sha256"]

    field_map = {
        "dry_matter_percent": "dry_matter_percent",
        "nitrogen_g_kg_dm": "nitrogen_g_kg_dm",
        "sulfur_g_kg_dm": "sulfur_g_kg_dm",
        "phosphorus_g_kg_dm": "phosphorus_g_kg_dm",
        "potassium_g_kg_dm": "potassium_g_kg_dm",
        "calcium_g_kg_dm": "calcium_g_kg_dm",
        "magnesium_g_kg_dm": "magnesium_g_kg_dm",
        "sodium_g_kg_dm": "sodium_g_kg_dm",
        "chloride_g_kg_dm": "chloride_g_kg_dm",
        "iron_mg_kg_dm": "iron_mg_kg_dm",
        "zinc_mg_kg_dm": "zinc_mg_kg_dm",
        "manganese_mg_kg_dm": "manganese_mg_kg_dm",
        "copper_mg_kg_dm": "copper_mg_kg_dm",
        "boron_mg_kg_dm": "boron_mg_kg_dm",
        "molybdenum_mg_kg_dm": "molybdenum_mg_kg_dm",
    }
    measurements = {item["id"]: item for item in reference["measurements"]}
    for measurement_id, source_field in field_map.items():
        assert measurements[measurement_id]["data_class"] == "A"
        assert measurements[measurement_id]["status"] == "measured"
        assert measurements[measurement_id]["value"] == pytest.approx(float(sample[source_field]))

    crude_protein = measurements["crude_protein_g_kg_dm"]
    assert sample["crude_protein_g_kg_dm"] == ""
    assert crude_protein["value"] is None
    assert crude_protein["status"] == "not_reported"
    assert crude_protein["data_class"] is None

    chloride = profile["compounds"]["ChlorideIon"]
    assert measurements["chloride_g_kg_dm"]["value"] == pytest.approx(11.7)
    assert chloride["data_class"] == "A"
    assert chloride["wet_mass_fraction"] == pytest.approx(11.7 * 0.143 / 1000.0)
    assert chloride["source"]["source_id"] == "SRC-VARTA-2026-10-27"
    assert _default_feed_composition()["ChlorideIon"] == pytest.approx(chloride["wet_mass_fraction"])

    fractions = [item["wet_mass_fraction"] for item in profile["compounds"].values()]
    assert sum(fractions) == pytest.approx(1.0)
    assert profile["compounds"]["Water"]["wet_mass_fraction"] == pytest.approx(
        1.0 - float(sample["dry_matter_percent"]) / 100.0
    )


def test_varta_total_n_crude_protein_equivalent_is_c_labeled_and_not_a_process_input():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    reference = profile["analytical_reference"]
    measurements = {item["id"]: item for item in reference["measurements"]}
    estimate = next(item for item in reference["derived_estimates"] if item["id"] == "crude_protein_equivalent_g_kg_dm")
    total_n = float(measurements[estimate["calculation"]["input_measurement_id"]]["value"])
    factor = float(estimate["calculation"]["nitrogen_to_protein_factor"])

    assert measurements["crude_protein_g_kg_dm"]["value"] is None
    assert measurements["crude_protein_g_kg_dm"]["status"] == "not_reported"
    assert estimate["value"] == pytest.approx(total_n * factor)
    assert estimate["value"] == pytest.approx(131.25)
    assert estimate["data_class"] == "C"
    assert estimate["status"] == "derived_estimate"
    assert estimate["calculation"]["method_source_doi"] == "10.3390/proteomes13010008"
    assert "not a measured protein assay" in estimate["limitation"]
    assert "not connected" in estimate["limitation"]
    assert not any("crude_protein_equivalent" in key for key in profile["compounds"])
    assert _default_feed_composition() == {
        name: row["wet_mass_fraction"] for name, row in profile["compounds"].items()
    }

    component = (ROOT / "frontend/src/components/FeedAnalyticalReference.tsx").read_text(encoding="utf-8")
    assert "C derived estimate" in component
    assert "reference.derived_estimates" in component


def test_reset_profile_element_inventory_discrepancies_are_not_silently_reconciled():
    from Greenhub.component_metadata import COMPONENT_METADATA

    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    measurements = {item["id"]: item for item in profile["analytical_reference"]["measurements"]}
    dm_fraction = float(measurements["dry_matter_percent"]["value"]) / 100.0
    element_fields = {
        "N": ("nitrogen_mass_fraction", "nitrogen_g_kg_dm"),
        "P": ("phosphorus_mass_fraction", "phosphorus_g_kg_dm"),
        "K": ("potassium_mass_fraction", "potassium_g_kg_dm"),
        "S": ("sulfur_mass_fraction", "sulfur_g_kg_dm"),
        "Ca": ("calcium_mass_fraction", "calcium_g_kg_dm"),
        "Mg": ("magnesium_mass_fraction", "magnesium_g_kg_dm"),
        "Na": ("sodium_mass_fraction", "sodium_g_kg_dm"),
        "Cl": ("chloride_mass_fraction", "chloride_g_kg_dm"),
    }
    expected_g_per_kg_wet = {
        "N": (3.3856, 3.0030),
        "P": (0.2107, 0.4004),
        "K": (0.5056, 4.1613),
        "S": (0.1699, 0.7150),
        "Ca": (0.0, 1.9877),
        "Mg": (0.0, 0.3146),
        "Na": (0.0, 0.1859),
        "Cl": (1.6731, 1.6731),
    }

    for element, (metadata_field, measurement_id) in element_fields.items():
        model_total = sum(
            float(row["wet_mass_fraction"])
            * getattr(COMPONENT_METADATA[component], metadata_field, 0.0)
            for component, row in profile["compounds"].items()
            if component in COMPONENT_METADATA
        ) * 1000.0
        lab_total = float(measurements[measurement_id]["value"]) * dm_fraction
        expected_model, expected_lab = expected_g_per_kg_wet[element]
        assert model_total == pytest.approx(expected_model, abs=0.0001)
        assert lab_total == pytest.approx(expected_lab, abs=0.0001)

    limitation = profile["analytical_reference"]["limitation"].lower()
    assert "reset-default component vector" in limitation
    assert "no elemental rescaling or automatic closure" in limitation
    assert "not live user overrides" in limitation


def test_protein_products_are_initial_state_zeros_not_feed_assays():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    for component in ("PrecipitatedProtein", "HeatCoagulatedProtein"):
        row = profile["compounds"][component]
        assert row["wet_mass_fraction"] == 0.0
        assert row["model_baseline_percent"] == 0.0
        assert row["record_role"] == "structural_initial_state"
        assert row["data_class"] is None
        assert row["source"]["data_class"] is None
        assert row["source"]["evidence_class"] == "structural_model_initialization"
        assert "not an analytical result" in row["source"]["basis"]
        assert "untreated raw-grass inlet only" in row["source"]["applicability"].lower()


def test_unmeasured_zero_fallbacks_are_distinct_from_evidence_and_numeric_defaults_are_unchanged():
    profile_text = (FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8")
    profile = json.loads(profile_text)
    compounds = profile["compounds"]
    assert profile_text.count('"derived_estimates"') == 1
    zero_fallbacks = {
        name: row for name, row in compounds.items()
        if row.get("record_role") == "unmeasured_model_fallback" and row["wet_mass_fraction"] == 0.0
    }
    assert len(zero_fallbacks) == 33
    for name, row in zero_fallbacks.items():
        assert row["wet_mass_fraction"] == 0.0, name
        assert row["model_baseline_percent"] == 0.0, name
        assert row["data_class"] is None, name
        assert row["input_status"] == "not_measured_zero_fallback", name
        assert row["source"]["data_class"] is None, name
        assert row["source"]["evidence_class"] == "unmeasured_numeric_fallback", name
        assert "not be interpreted as absence" in row["source"]["basis"], name

    nonzero_fallbacks = {
        name: row for name, row in compounds.items()
        if row.get("record_role") == "unmeasured_model_fallback" and row["wet_mass_fraction"] > 0.0
    }
    assert len(nonzero_fallbacks) == 16
    for name, row in nonzero_fallbacks.items():
        assert row["data_class"] is None, name
        assert row["input_status"] == "not_measured_numeric_fallback", name
        assert row["source"]["data_class"] is None, name
        assert row["source"]["evidence_class"] == "unmeasured_numeric_fallback", name
        assert "not an analytical result" in row["source"]["basis"], name

    structural_states = {
        name: row for name, row in compounds.items()
        if row.get("record_role") == "structural_initial_state"
    }
    assert set(structural_states) == {
        "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein", "MicrobialBiomass"
    }
    assert all(row["data_class"] is None for row in structural_states.values())
    assert all(row["input_status"] == "structural_model_state" for row in structural_states.values())

    residual = compounds["ParticulateBiodegradableOrganics"]
    other_fraction = sum(row["wet_mass_fraction"] for key, row in compounds.items() if key != "ParticulateBiodegradableOrganics")
    assert residual["data_class"] is None
    assert residual["record_role"] == "derived_profile_residual"
    assert residual["input_status"] == "calculated_baseline_mass_balance_residual"
    assert residual["wet_mass_fraction"] == pytest.approx(1.0 - other_fraction)
    assert residual["source"]["evidence_class"] == "derived_model_residual"

    positive_d = {name: row for name, row in compounds.items() if row.get("data_class") == "D"}
    assert positive_d == {}
    assert sum(row["wet_mass_fraction"] for row in compounds.values()) == pytest.approx(1.0)
    assert _default_feed_composition() == {
        name: row["wet_mass_fraction"] for name, row in compounds.items()
    }


def test_ui_acetic_acid_default_is_a_traceable_cross_context_proxy_not_a_varta_measurement():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    with (ROOT / "Greenhub/data/Pre-treatment/Mechanical/landscape_management_grass_heller_2023_composition_reference.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source_file:
        source = next(row for row in csv.DictReader(source_file) if row["record_id"] == "HLR23-COMP-UT")

    acid = profile["compounds"]["AceticAcid"]
    expected = float(source["acetic_acid_g_kg_fm"]) / 1000.0
    assert source["treatment_variant"] == "UT"
    assert float(source["acetic_acid_g_kg_fm"]) == pytest.approx(0.09)
    assert acid["data_class"] == "C"
    assert acid["source"]["source_quality_class"] == "B"
    assert acid["source"]["source_id"] == "S13_HELLER_2023_LANDSCAPE_GRASS"
    assert acid["source"]["source_row_id"] == source["record_id"]
    assert acid["wet_mass_fraction"] == pytest.approx(expected)
    assert acid["model_baseline_percent"] == pytest.approx(expected * 100.0)
    assert _default_feed_composition()["AceticAcid"] == pytest.approx(expected)
    assert "not the project-supplied Dutch roadside-grass sample" in acid["source"]["applicability"]
    assert acid["source"]["uncertainty"]
    assert sum(item["wet_mass_fraction"] for item in profile["compounds"].values()) == pytest.approx(1.0)

    with (FEED_DIR / "source_register.csv").open(encoding="utf-8-sig", newline="") as source_file:
        registered_ids = [row["source_id"] for row in csv.DictReader(source_file)]
    assert registered_ids.count("S13_HELLER_2023_LANDSCAPE_GRASS") == 1
    assert len(registered_ids) == len(set(registered_ids))


def test_literature_linked_pectin_fat_and_nitrate_proxies_preserve_profile_closure():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    reference_path = FEED_DIR / "fresh_ryegrass_composition_della_rosa_2022_reference.csv"
    with reference_path.open(encoding="utf-8-sig", newline="") as source_file:
        reference = {row["parameter"]: row for row in csv.DictReader(source_file)}

    expected = {
        "Pectin": ("Pectin (homogalacturonan)", 10.0, 0.6),
        "Lipids": ("Crude fat", 41.0, 3.0),
    }
    for component, (source_parameter, source_value, source_sd) in expected.items():
        row = profile["compounds"][component]
        source = row["source"]
        literature = reference[source_parameter]
        assert row["data_class"] == source["data_class"] == "C"
        assert source["source_id"] == literature["source_id"] == "SRC-DELLAROSA-2022-RYEGRASS-COMPOSITION"
        assert source["doi"] == "10.1093/jas/skac223"
        assert source["source_location"].startswith("Table 1, FR0")
        assert float(literature["value"]) == source_value
        assert float(literature["standard_deviation"]) == source_sd
        assert row["wet_mass_fraction"] == pytest.approx(
            source_value / 1000 * profile["dry_matter_fraction"]
        )
        assert "transfer" in source["uncertainty"].lower()
        assert "roadside" in source["applicability"].lower()

    compounds = profile["compounds"]
    nitrate = compounds["NitrateIon"]
    nitrate_source = reference["Nitrate nitrogen"]
    assert nitrate["data_class"] == nitrate["source"]["data_class"] == "C"
    assert nitrate["source"]["source_id"] == nitrate_source["source_id"]
    assert nitrate["source"]["source_row_id"] == nitrate_source["observation_id"]
    assert nitrate["source"]["doi"] == "10.1093/jas/skac223"
    nitrate_fraction = (
        float(nitrate_source["value"])
        * 1e-6
        * profile["dry_matter_fraction"]
        * (62.0049 / 14.0067)
    )
    assert nitrate["wet_mass_fraction"] == pytest.approx(nitrate_fraction)
    assert "not a measurement of the VARTA sample" in nitrate["source"]["basis"]
    assert _default_feed_composition()["NitrateIon"] == pytest.approx(nitrate_fraction)

    assert sum(row["wet_mass_fraction"] for row in compounds.values()) == pytest.approx(1.0)
    assert compounds["ParticulateBiodegradableOrganics"]["record_role"] == "derived_profile_residual"


def test_measured_chloride_and_summer_trace_metals_are_partitioned_from_ash_without_mass_drift():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    reference_path = FEED_DIR / "czubaszek_2023_fresh_grass_ultimate_and_metals_reference.csv"
    with reference_path.open(encoding="utf-8-sig", newline="") as source_file:
        rows = {row["record_id"]: row for row in csv.DictReader(source_file)}

    selected_ids = (
        "CZ2023-T4-SU-CHROMIUM",
        "CZ2023-T4-SU-NICKEL",
        "CZ2023-T4-SU-CADMIUM",
        "CZ2023-T4-SU-MERCURY",
        "CZ2023-T4-SU-LEAD",
    )
    source_sum_mg_per_kg_dm = sum(float(rows[row_id]["reported_mean"]) for row_id in selected_ids)
    expected_metals = source_sum_mg_per_kg_dm * profile["dry_matter_fraction"] * 1e-6
    metals = profile["compounds"]["HeavyMetals"]
    assert source_sum_mg_per_kg_dm == pytest.approx(12.97)
    assert metals["data_class"] == metals["source"]["data_class"] == "C"
    assert metals["source"]["source_quality_class"] == "B"
    assert tuple(metals["source"]["source_row_ids"]) == selected_ids
    assert metals["wet_mass_fraction"] == pytest.approx(expected_metals)
    assert _default_feed_composition()["HeavyMetals"] == pytest.approx(expected_metals)

    ash = profile["compounds"]["Ash"]
    chloride_fraction = profile["compounds"]["ChlorideIon"]["wet_mass_fraction"]
    expected_ash = 0.179 * profile["dry_matter_fraction"] - expected_metals - chloride_fraction
    assert ash["data_class"] == "C"
    assert ash["wet_mass_fraction"] == pytest.approx(expected_ash)
    assert "VARTA measured chloride" in profile["mass_balance_method"]
    assert "avoid counting these species twice" in profile["mass_balance_method"]

    compounds = profile["compounds"]
    assert sum(row["wet_mass_fraction"] for row in compounds.values()) == pytest.approx(1.0)
    residual = compounds["ParticulateBiodegradableOrganics"]
    assert residual["data_class"] is None
    assert residual["record_role"] == "derived_profile_residual"
    assert "1 minus the sum of all other wet-mass fractions" in residual["source"]["basis"]


def test_reference_pah_unit_conversion_is_correct_and_pfas_pool_uses_traceable_grass_proxy():
    from Greenhub.component_metadata import COMPONENT_METADATA

    source_path = FEED_DIR / "roadside_grass_composition_scientific.csv"
    with source_path.open(encoding="utf-8-sig", newline="") as source_file:
        rows = {
            row["parameter_id"]: row
            for row in csv.DictReader(source_file)
            if row["parameter_id"] in {"S10_H1_1_bap", "S10_H1_1_sum16pah"}
        }

    expected_mg_per_kg = {"S10_H1_1_bap": 0.37, "S10_H1_1_sum16pah": 3.4}
    for record_id, expected in expected_mg_per_kg.items():
        row = rows[record_id]
        assert row["unit_original"] == "µg/kg"
        assert row["unit_si"] == "mg/kg"
        assert float(row["value_si"]) == pytest.approx(float(row["value_original"]) / 1000.0)
        assert float(row["value_si"]) == pytest.approx(expected)
        assert "Maximum, not mean" in row["limitation_note"]

    # The legacy PersistentOrganics model component represents PFAS, not PAHs.
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    assert COMPONENT_METADATA["PersistentOrganics"].subcategory == "pfas_pool"
    pfas = profile["compounds"]["PersistentOrganics"]
    assert pfas["data_class"] == "C"
    assert pfas["source"]["source_id"] == "SRC-KOSIARSKI-2025"

    reference_path = FEED_DIR / "kosiarski_2025_orchard_grass_control_pfas_replicate_sums.csv"
    with reference_path.open(encoding="utf-8-sig", newline="") as source_file:
        replicate_rows = list(csv.DictReader(source_file))
    replicate_sums = [float(row["sum_targeted_pfas_ug_per_kg_dry"]) for row in replicate_rows]
    mean_ug_per_kg_dry = sum(replicate_sums) / len(replicate_sums)
    expected_wet_fraction = mean_ug_per_kg_dry * profile["dry_matter_fraction"] * 1e-9
    assert replicate_sums == pytest.approx([4.595, 1.824, 1.054])
    assert mean_ug_per_kg_dry == pytest.approx(2.491)
    assert pfas["wet_mass_fraction"] == pytest.approx(expected_wet_fraction)
    assert pfas["source"]["source_quality_class"] == "B"
    assert "three composite subsamples" in pfas["source"]["uncertainty"]
    assert "Not Dutch roadside grass" in pfas["source"]["applicability"]
    assert profile["compounds"]["ParticulateBiodegradableOrganics"]["record_role"] == "derived_profile_residual"
    assert sum(row["wet_mass_fraction"] for row in profile["compounds"].values()) == pytest.approx(1.0)

    with (FEED_DIR / "source_register.csv").open(encoding="utf-8-sig", newline="") as source_file:
        registered_ids = {row["source_id"] for row in csv.DictReader(source_file)}
    assert "SRC-KOSIARSKI-2025" in registered_ids


def test_grass_pesticide_proxy_is_reproducible_and_keeps_transferability_visible():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    source = profile["compounds"]["Pesticides"]
    evidence = source["source"]
    expected = (
        evidence["reported_mean_detected_residue_mg_per_kg_fresh"]
        * evidence["reported_detection_count"]
        / evidence["reported_sample_count"]
        * 1e-6
    )

    assert source["data_class"] == evidence["data_class"] == "C"
    assert evidence["source_quality_class"] == "B"
    assert evidence["source_id"] == "SRC-PRECHSL-2022"
    assert evidence["doi"] == "10.3389/fenvs.2022.1062333"
    assert evidence["reported_sample_count"] == 399
    assert evidence["reported_detection_count"] == 334
    assert evidence["reported_loq_mg_per_kg"] == pytest.approx(0.01)
    assert source["wet_mass_fraction"] == pytest.approx(expected)
    assert _default_feed_composition()["Pesticides"] == pytest.approx(expected)
    assert "lower-bound" in evidence["basis"].lower()
    assert "not Dutch roadside biomass" in evidence["applicability"]

    with (FEED_DIR / "source_register.csv").open(encoding="utf-8-sig", newline="") as source_file:
        registered = {row["source_id"] for row in csv.DictReader(source_file)}
    assert evidence["source_id"] in registered
    assert sum(row["wet_mass_fraction"] for row in profile["compounds"].values()) == pytest.approx(1.0)


def test_masaki_sugar_ranges_create_a_traceable_mass_conserving_ui_proxy():
    profile = json.loads((FEED_DIR / "greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    reference_path = FEED_DIR / "italian_ryegrass_nonstructural_carbohydrates_masaki_ohyama_1976_reference.csv"
    with reference_path.open(encoding="utf-8-sig", newline="") as source_file:
        rows = {row["parameter"]: row for row in csv.DictReader(source_file)}

    expected_ranges = {
        "Glucose": ("Glucose", 1.0, 4.4, "MAS76-NSC-GLUCOSE"),
        "Fructose": ("Fructose", 0.7, 5.0, "MAS76-NSC-FRUCTOSE"),
        "Sucrose": ("Sucrose", 0.3, 4.5, "MAS76-NSC-SUCROSE"),
        "EntrappedSugars": ("Fructosan", 1.2, 12.6, "MAS76-NSC-FRUCTOSAN"),
    }
    midpoint_weights = {}
    for component, (parameter, low, high, source_row_id) in expected_ranges.items():
        row = rows[parameter]
        assert row["observation_id"] == source_row_id
        assert float(row["reported_min"]) == pytest.approx(low)
        assert float(row["reported_max"]) == pytest.approx(high)
        assert row["unit"] == "% of DM"
        midpoint_weights[component] = (low + high) / 2.0

    roadside_rows = FEED_DIR / "roadside_grass_composition_scientific.csv"
    with roadside_rows.open(encoding="utf-8-sig", newline="") as source_file:
        aggregate = next(row for row in csv.DictReader(source_file) if row["parameter_id"] == "extractive_sugars")
    assert float(aggregate["value_si"]) == pytest.approx(0.072)
    assert aggregate["unit_si"] == "kg/kg dry matter"

    profile_sugar_mass = float(aggregate["value_si"]) * profile["dry_matter_fraction"]
    weight_total = sum(midpoint_weights.values())
    for component, weight in midpoint_weights.items():
        record = profile["compounds"][component]
        source = record["source"]
        expected_wet_fraction = profile_sugar_mass * weight / weight_total
        assert record["data_class"] == "C"
        assert record["wet_mass_fraction"] == pytest.approx(expected_wet_fraction)
        assert record["model_baseline_percent"] == pytest.approx(expected_wet_fraction * 100.0)
        assert source["source_quality_class"] == "B"
        if component == "EntrappedSugars":
            assert source["allocation_source_row_id"] == rows["Fructosan"]["observation_id"]
            assert source["aggregate_source_row_id"] == "RG_COMP_V1:extractive_sugars"
        else:
            assert source["source_row_id"] == rows[expected_ranges[component][0]]["observation_id"]

    assert sum(profile["compounds"][name]["wet_mass_fraction"] for name in midpoint_weights) == pytest.approx(profile_sugar_mass)
    assert _default_feed_composition()["Glucose"] == pytest.approx(profile["compounds"]["Glucose"]["wet_mass_fraction"])
    assert _default_feed_composition()["Fructose"] == pytest.approx(profile["compounds"]["Fructose"]["wet_mass_fraction"])
    assert _default_feed_composition()["Sucrose"] == pytest.approx(profile["compounds"]["Sucrose"]["wet_mass_fraction"])
    assert sum(row["wet_mass_fraction"] for row in profile["compounds"].values()) == pytest.approx(1.0)

    sidecar_path = reference_path.with_suffix(reference_path.suffix + ".source.json")
    metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert metadata["source_id"] == "SRC-MASAKI-1976"
    assert metadata["doi"] == "10.2508/chikusan.47.205"
    assert metadata["readiness_state"] == "D4_partial_calculation_connected"
    assert "not the GreenHub Dutch roadside-grass sample" in metadata["limitations"][0]
