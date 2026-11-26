import csv
import json
from pathlib import Path

import pytest

from biorefinery_platform import ProjectAdapter, ProjectDescriptor, ProjectRegistry
from biorefinery_platform.data_catalog import build_catalog_bundle, build_dataset_reuse_catalog
from Greenhub.application.project_adapter import GREENHUB_PROJECT_ADAPTER
from Greenhub.application.scenario_service import ScenarioService


ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_project_registry_keeps_greenhub_as_a_project_plugin():
    descriptor = GREENHUB_PROJECT_ADAPTER.descriptor
    assert descriptor.project_id == "greenhub"
    assert descriptor.status == "runnable_project_adapter"
    assert descriptor.technology_family_ids == (
        "pretreatment_fractionation",
        "protein_recovery",
        "anaerobic_digestion",
        "biogas_upgrading",
        "npk_recovery",
    )
    registry = ProjectRegistry((GREENHUB_PROJECT_ADAPTER,))
    assert registry.get("greenhub").build_model is GREENHUB_PROJECT_ADAPTER.build_model
    with pytest.raises(KeyError, match="not registered"):
        registry.get("unimplemented-project")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(GREENHUB_PROJECT_ADAPTER)


def test_phase_family_labels_preserve_legacy_ids_and_route_groups():
    areas = {row["process_area_id"]: row["display_name"] for row in ScenarioService().list_process_areas()}
    assert areas["feed_preparation_and_primary_separation"] == "Pretreatment and fractionation"
    assert areas["digestate_treatment_and_nutrient_recovery"] == "NPK recovery"
    assert "anaerobic_digestion" in areas
    assert {"feed_preparation", "protein_recovery", "anaerobic_digestion", "biogas_upgrading", "nutrient_recovery"} == set(ScenarioService._groups)
    family_catalog = json.loads((ROOT / "Greenhub/data/platform/technology_families.json").read_text(encoding="utf-8"))
    families = {item["family_id"]: item for item in family_catalog["families"]}
    assert families["biogas_upgrading"]["parent_family_id"] == "anaerobic_digestion"
    assert families["pretreatment_fractionation"]["legacy_process_area_ids"] == ["feed_preparation_and_primary_separation"]
    assert families["npk_recovery"]["scenario_id_prefixes"] == ["NR"]


def test_cross_context_route_template_is_declarative_and_reference_only():
    schema = json.loads(
        (ROOT / "biorefinery_platform/schemas/process_route_template.schema.json").read_text(encoding="utf-8")
    )
    route = json.loads(
        (ROOT / "Greenhub/data/platform/routes/greenhub-grass-protein-biogas-npk-reference-v1.json").read_text(encoding="utf-8")
    )
    descriptor = json.loads(
        (ROOT / "Greenhub/data/platform/projects/greenhub.json").read_text(encoding="utf-8")
    )
    assert {"route_id", "technology_instances", "material_streams", "input_resolution"}.issubset(schema["required"])
    assert "route_template_ids" in json.loads(
        (ROOT / "biorefinery_platform/schemas/project_descriptor.schema.json").read_text(encoding="utf-8")
    )["properties"]
    assert route["route_id"] in descriptor["route_template_ids"]
    assert route["route_status"] == "reference_only"
    assert route["compatibility"]["api_contract_change_required"] is False
    assert route["compatibility"]["executable_model"] is False
    assert route["input_resolution"]["precedence"] == [
        "request_override", "selected_project_material_profile", "project_parameter_registry",
        "declared_structural_state", "explicit_missing",
    ]
    families = {item["family_id"] for item in json.loads(
        (ROOT / "Greenhub/data/platform/technology_families.json").read_text(encoding="utf-8")
    )["families"]}
    assert set(route["technology_family_ids"]).issubset(families)
    step_ids = {item["instance_id"] for item in route["technology_instances"]}
    stream_ids = {item["stream_id"] for item in route["material_streams"]}
    assert len(step_ids) == len(route["technology_instances"])
    assert len(stream_ids) == len(route["material_streams"])
    for step in route["technology_instances"]:
        assert step["technology_family_id"] in families
        assert set(step["input_stream_ids"] + step["output_stream_ids"]).issubset(stream_ids)
        assert all("value" not in binding for binding in step["parameter_bindings"])
    for stream in route["material_streams"]:
        assert stream["from"] in step_ids or stream["from"].startswith("external:")
        assert stream["to"] in step_ids or stream["to"].startswith("boundary:")


def test_phase_3_to_7_catalog_is_traceable_and_does_not_promote_data():
    bundle = build_catalog_bundle()
    datasets = bundle["datasets"]
    inputs = bundle["runtime_inputs"]
    manifest_rows = _read_csv(ROOT / "Greenhub/data/global_audit_package/global_dataset_manifest.csv")
    eligible_categories = {"Pre-treatment", "Protein recovery", "Bigas production + upgrade", "Resource recovery", "Centrifuge"}
    expected_dataset_count = sum(row["category"] in eligible_categories for row in manifest_rows)
    master_inputs = _read_csv(ROOT / "Greenhub/data/fair_input_catalog/master_input_records.csv")
    expected_inputs = [row for row in master_inputs if row["record_id"].startswith(("phase3.", "phase4.", "phase5.", "phase6.", "phase7."))]
    expected_phase_counts = {
        str(phase): sum(row["record_id"].startswith(f"phase{phase}.") for row in expected_inputs)
        for phase in range(3, 8)
    }
    assert bundle["counts"]["technology_dataset_assets"] == len(datasets) == expected_dataset_count
    assert bundle["counts"]["canonical_phase_3_to_7_input_records"] == len(inputs) == len(expected_inputs)
    assert bundle["counts"]["phase_3_to_7_inputs_by_phase"] == expected_phase_counts
    assert bundle["counts"]["d4_promotions"] == 0
    assert bundle["counts"]["context_independent_empirical_assets"] == 0
    assert all(row["quality_class"] != "D" for row in inputs)
    assert all(row["data_asset_id"].startswith("urn:greenhub:data-asset:") for row in datasets)
    assert len({row["data_asset_id"] for row in datasets}) == len(datasets)
    assert all(row["portability_review_status"] == "rule_inferred_review_required" for row in datasets)
    assert all(row["context_independent"] is False for row in datasets)
    assert {row["technology_family_id"] for row in datasets} >= {
        "pretreatment_fractionation", "protein_recovery", "anaerobic_digestion",
        "biogas_upgrading", "npk_recovery", "crosscutting_separation",
    }
    assert all(row["source_dataset"] and row["record_id"].startswith("phase") for row in inputs)
    assert all(row["portability_review_required"] for row in inputs)
    source_rows = {row["record_id"]: row for row in master_inputs}
    for row in inputs:
        assert row["value"] == source_rows[row["record_id"]]["value"]
        assert row["quality_class"] == source_rows[row["record_id"]]["quality_class"]


def test_generated_phase_catalogs_match_catalog_manifest_counts():
    manifest = json.loads((ROOT / "Greenhub/data/platform/catalogs/catalog_manifest.json").read_text(encoding="utf-8"))
    datasets = _read_csv(ROOT / "Greenhub/data/platform/catalogs/phase_3_7_dataset_reuse_catalog.csv")
    inputs = _read_csv(ROOT / "Greenhub/data/platform/catalogs/phase_3_7_runtime_input_reuse_catalog.csv")
    assert len(datasets) == manifest["counts"]["technology_dataset_assets"]
    assert len(inputs) == manifest["counts"]["canonical_phase_3_to_7_input_records"]
    assert not [row for row in inputs if row["quality_class"] == "D"]
    assert sum(row["quality_class"] == "E" for row in inputs) == 528
    input_json = json.loads(
        (ROOT / "Greenhub/data/platform/catalogs/phase_3_7_runtime_input_reuse_catalog.json").read_text(encoding="utf-8")
    )
    assert len(input_json) == len(inputs)
    by_csv_id = {row["record_id"]: row for row in inputs}
    for row in input_json:
        assert by_csv_id[row["record_id"]]["quality_class"] == row["quality_class"]
        if row["quality_class"] == "E":
            metadata = json.loads(row["additional_metadata_json"])
            assert "not an evidence upgrade" in metadata["quality_class_mapping"].lower()


def test_new_open_phase_evidence_is_cross_linked_and_stays_reference_only():
    bundle = build_catalog_bundle()
    assets = {row["filename"]: row for row in bundle["datasets"]}
    expected = {
        "alfalfa_hansen_2022_repeated_pressing_quality_reference.csv": {
            "protein_recovery", "pretreatment_fractionation"
        },
        "lin_2020_pasture_grass_extraction_method_comparison_reference.csv": {
            "protein_recovery", "pretreatment_fractionation"
        },
        "brown_2022_grass_htc_ad_bmp_reference.csv": {
            "anaerobic_digestion", "pretreatment_fractionation"
        },
        "hoyos_2026_carbonate_biogas_upgrading_pilot_reference.csv": {
            "biogas_upgrading"
        },
    }
    for filename, family_ids in expected.items():
        row = assets[filename]
        assert set(row["technology_family_ids"]) == family_ids
        assert row["source_ids"]
        assert row["source_dois_or_stable_ids"]
        assert row["source_urls"]
        assert row["source_locations"]
        assert row["source_licenses"]
        assert row["source_retrieval_dates"]
        assert row["source_metadata_gaps"] == []
        assert row["context_independent"] is False
        assert row["data_scope_class"] in {
            "technology_and_material_specific", "technology_specific"
        }
        assert row["data_status_values"] == "reference_only"
    brown = assets["brown_2022_grass_htc_ad_bmp_reference.csv"]
    assert "10.3390/en15103495" in brown["source_dois_or_stable_ids"] or "https://doi.org/10.3390/en15103495" in brown["source_dois_or_stable_ids"]
    assert "10.5518/1154" in brown["source_dois_or_stable_ids"]
    assert bundle["counts"]["d4_promotions"] == 0


def test_phase_dataset_scope_schema_distinguishes_context_independent_data():
    schema = json.loads(
        (ROOT / "biorefinery_platform/schemas/dataset_reuse_record.schema.json").read_text(encoding="utf-8")
    )
    assert "context_independent" in schema["required"]
    assert "data_scope_class" in schema["required"]
    assert "provenance" in schema["required"]
    assert "metadata_gaps" in schema["required"]
    assert "context_independent" in schema["properties"]["data_scope_class"]["enum"]
    descriptor_schema = json.loads(
        (ROOT / "biorefinery_platform/schemas/project_descriptor.schema.json").read_text(encoding="utf-8")
    )
    descriptor = json.loads(
        (ROOT / "Greenhub/data/platform/projects/greenhub.json").read_text(encoding="utf-8")
    )
    assert set(descriptor_schema["required"]).issubset(descriptor)


def test_cross_context_scientific_schemas_separate_material_mass_from_properties_and_equations():
    profile_schema = json.loads(
        (ROOT / "biorefinery_platform/schemas/material_profile_record.schema.json").read_text(encoding="utf-8")
    )
    assert {"mass_composition", "analytical_properties", "closure", "provenance", "metadata_gaps"}.issubset(
        profile_schema["required"]
    )
    assert "properties" in profile_schema["properties"]["analytical_properties"]["description"]
    assert profile_schema["properties"]["analytical_properties"]["items"]["properties"]["unit"]["type"] == "string"
    assert "not_detected" in profile_schema["properties"]["analytical_properties"]["items"]["properties"]["status"]["enum"]
    derived = profile_schema["properties"]["derived_analytical_properties"]
    assert "mass-composition components" in derived["description"]
    assert {"equation", "input_property_ids"}.issubset(derived["items"]["properties"]["calculation"]["required"])
    assert derived["items"]["properties"]["status"]["const"] == "calculated_from_analytical_properties"
    assert profile_schema["properties"]["mass_composition"]["items"]["properties"]["quality_class"]["enum"] == ["A", "B", "C", "D", "E", None]
    value_statuses = set(profile_schema["properties"]["mass_composition"]["items"]["properties"]["value_status"]["enum"])
    assert {"measured", "literature_derived_assumption", "unmeasured_numeric_fallback", "derived_residual"}.issubset(value_statuses)
    feed_profile = json.loads((ROOT / "Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json").read_text(encoding="utf-8"))
    assert not [row for row in feed_profile["compounds"].values() if row.get("data_class") == "D"]
    assert {row["value_status"] for row in feed_profile["compounds"].values()} <= value_statuses
    assert feed_profile["compounds"]["Peptides"]["value_status"] == "unmeasured_numeric_fallback"
    assert feed_profile["compounds"]["ParticulateBiodegradableOrganics"]["value_status"] == "derived_residual"

    equation_schema = json.loads(
        (ROOT / "biorefinery_platform/schemas/parameter_equation_record.schema.json").read_text(encoding="utf-8")
    )
    assert {"record_kind", "data_scope_class", "applicability", "provenance", "metadata_gaps"}.issubset(
        equation_schema["required"]
    )
    assert {"parameter", "equation", "physical_constant", "method"} == set(
        equation_schema["properties"]["record_kind"]["enum"]
    )
    assert equation_schema["properties"]["equation"]["properties"]["input_record_ids"]["type"] == "array"
    assert equation_schema["properties"]["context_independent"]["type"] == "boolean"
    assert "value_status" not in equation_schema["required"]
    value_statuses = set(equation_schema["properties"]["value_status"]["enum"])
    assert {"measured", "literature_derived_assumption", "unmeasured_numeric_fallback", "structural_placeholder"}.issubset(value_statuses)


def test_generated_dataset_records_follow_common_reuse_metadata_profile():
    bundle = build_catalog_bundle()
    schema = json.loads(
        (ROOT / "biorefinery_platform/schemas/dataset_reuse_record.schema.json").read_text(encoding="utf-8")
    )
    required = set(schema["required"])
    allowed_scope = set(schema["properties"]["data_scope_class"]["enum"])
    for row in bundle["datasets"]:
        assert required.issubset(row)
        assert row["data_scope_class"] in allowed_scope
        assert isinstance(row["metadata_gaps"], list)
        assert isinstance(row["provenance"], list)
        assert isinstance(row["context_independent"], bool)
        assert bool(row["provenance"]) is bool(row["linked_source_count"])
        for source in row["provenance"]:
            assert set(schema["properties"]["provenance"]["items"]["required"]).issubset(source)


def test_multi_source_sidecar_preserves_per_paper_provenance_and_links():
    records = build_dataset_reuse_catalog()
    dataset = next(
        row for row in records
        if row["dataset_path"].endswith("drying_energy_literature_benchmarks.csv")
    )

    expected_sources = {
        "SRC-DRY-BM2005",
        "SRC-DRY-GAWALEK2022",
        "SRC-DRY-MARTYNENKO2023",
        "SRC-DRY-ELSHANI2026",
        "SRC-DRY-WU2024",
    }
    assert set(dataset["source_ids"]) == expected_sources
    assert dataset["linked_source_count"] == len(expected_sources)
    assert len(dataset["source_dois_or_stable_ids"]) == len(expected_sources)
    assert dataset["activation_state"] == "reference_only"
    # This catalog field tracks activation state; evidence classes are separate.
    assert dataset["data_status_values"] == "reference_only"
    assert len(dataset["evidence_class"]) == len(expected_sources)
    assert {source["evidence_class"] for source in dataset["provenance"]} == set(dataset["evidence_class"])
    assert dataset["metadata_gaps"] == []
    assert {source["source_id"] for source in dataset["provenance"]} == expected_sources
    assert all(source["source_location"] for source in dataset["provenance"])
    assert all(source["license"] for source in dataset["provenance"])
    assert all(source["retrieval_date"] == "2026-11-11" for source in dataset["provenance"])
    assert len({source["measurement_basis"] for source in dataset["provenance"]}) == len(expected_sources)


def test_phase_3_to_7_measurement_register_is_a_request_list_not_fabricated_data():
    rows = _read_csv(ROOT / "Greenhub/data/platform/catalogs/phase_3_7_measurement_acquisition_register.csv")
    assert len(rows) == 34
    assert len({row["measurement_id"] for row in rows}) == len(rows)
    assert {row["technology_family_id"] for row in rows if row["technology_family_id"]} == {
        "pretreatment_fractionation", "protein_recovery", "anaerobic_digestion",
        "biogas_upgrading", "npk_recovery",
    }
    assert all(row["project_id"] == "greenhub" for row in rows)
    assert all(row["units"] and row["sampling_location"] and row["how_to_obtain"] for row in rows)
    assert all(row["status"].startswith("Open") for row in rows)
    assert all("measured_value" not in row and "observed_value" not in row for row in rows)


def test_feed_composition_measurement_requests_cover_unresolved_ui_inputs():
    rows = _read_csv(ROOT / "Greenhub/data/platform/catalogs/phase_3_7_measurement_acquisition_register.csv")
    feed_measurements = {
        row["measurement_id"]: row
        for row in rows
        if row["measurement_id"].startswith(("REQ-GH-P3-0", "REQ-GH-P3-10"))
    }

    assert {"REQ-GH-P3-06", "REQ-GH-P3-07", "REQ-GH-P3-08", "REQ-GH-P3-09", "REQ-GH-P3-10"}.issubset(feed_measurements)
    assert "NDF/ADF/ADL" in feed_measurements["REQ-GH-P3-06"]["method_or_instrument"]
    assert "free amino acids" in feed_measurements["REQ-GH-P3-07"]["method_or_instrument"]
    assert "total N P K" in feed_measurements["REQ-GH-P3-08"]["how_to_obtain"]
    assert "detection limits" in feed_measurements["REQ-GH-P3-09"]["method_or_instrument"]
    contaminant_units = feed_measurements["REQ-GH-P3-09"]["units"]
    assert "particles/kg DM" in contaminant_units
    assert "CFU/g" in contaminant_units
    assert "micrograms/kg DM" in contaminant_units
    assert "particle counts" in feed_measurements["REQ-GH-P3-09"]["how_to_obtain"]
    assert all(feed_measurements[item]["status"].startswith("Open") for item in ("REQ-GH-P3-06", "REQ-GH-P3-07", "REQ-GH-P3-08", "REQ-GH-P3-09", "REQ-GH-P3-10"))
    acids_and_sugars = feed_measurements["REQ-GH-P3-10"]
    assert "organic acids" in acids_and_sugars["measurement"].lower()
    assert "individual" in acids_and_sugars["method_or_instrument"]
    assert "do not infer individual compounds" in acids_and_sugars["how_to_obtain"]
