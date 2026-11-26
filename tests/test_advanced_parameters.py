from __future__ import annotations

import hashlib
import json

import pytest

from Greenhub.parameters import (
    CalculationMode,
    ParameterOverride,
    ParameterResolver,
    SelectionContext,
    build_editable_registry,
    load_default_registry,
    to_json_compatible,
)
from Greenhub.parameters.__main__ import export_parameter_registries
from Greenhub.parameters.loaders import LITERATURE_RECOVERY_PATH
from Greenhub.phase7_systems import create_phase7_scenario


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _context(mode, protein="PR1", digester="AD1", nutrient="NR4"):
    return SelectionContext(
        calculation_mode=mode,
        selected_scenarios=("F1", protein, digester, "BG2", nutrient),
        month="July",
    )


def test_registry_ids_are_unique_and_source_is_immutable():
    before = _digest(LITERATURE_RECOVERY_PATH)
    registry = load_default_registry()
    ids = [item.parameter_id for item in registry]
    assert len(ids) == len(set(ids))
    assert _digest(LITERATURE_RECOVERY_PATH) == before
    assert registry.get("phase4.precipitation_efficiency").readiness_state.value == "D4"


def test_resolution_preserves_structural_mode_and_activates_route_specific_literature():
    registry = load_default_registry()
    resolver = ParameterResolver(registry)
    structural = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.STRUCTURAL))}
    literature = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT))}
    combined = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT, "PR3"))}
    parameter_id = "phase4.precipitation_efficiency"
    assert structural[parameter_id].selected_candidate.source_dataset.endswith("greenhub_feed_inputs.xlsx")
    assert literature[parameter_id].active_value == pytest.approx(0.38)
    assert literature[parameter_id].selected_candidate.source_row_id == "REC-005"
    assert literature[parameter_id].selected_candidate.quality_class == "C"
    assert literature[parameter_id].selected_candidate.stable_identifier == "10.3389/fsufs.2019.00112"
    assert literature[parameter_id].selected_candidate.transferability_class == "proxy_high"
    assert "total-N denominator" in " ".join(literature[parameter_id].selected_candidate.warnings)
    assert combined[parameter_id].selected_candidate.source_dataset.endswith("greenhub_feed_inputs.xlsx")

    pH_id = "phase4.target_pH"
    assert structural[pH_id].selected_candidate.source_dataset.endswith("greenhub_feed_inputs.xlsx")
    assert literature[pH_id].active_value == pytest.approx(4.5)
    assert literature[pH_id].selected_candidate.source_row_id == "REC-006"
    assert literature[pH_id].selected_candidate.quality_class == "C"
    assert literature[pH_id].selected_candidate.stable_identifier == "10.3389/fsufs.2019.00112"
    assert literature[pH_id].selected_candidate.readiness_state.value == "D4"
    assert "endpoint is an explicit assumption" in " ".join(literature[pH_id].selected_candidate.warnings)
    assert combined[pH_id].active_value == pytest.approx(5.0)
    assert combined[pH_id].selected_candidate.source_row_id == "GUO2022_PRECIPITATION_PH"
    assert combined[pH_id].selected_candidate.stable_identifier == "10.1016/j.fufo.2022.100173"


def test_literature_operating_candidates_are_traceable_opt_in_and_leave_defaults_unchanged():
    registry = load_default_registry()
    resolver = ParameterResolver(registry)
    structural = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.STRUCTURAL))}
    literature = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT))}

    expected = {
        "phase3.juice_yield_kg_per_kg_wet_feed": (0.301, "PRESS-001"),
        "phase5.digester_temperature_c": (35.0, "AD-001"),
        "phase5.digester_hrt_days": (30.0, "AD-002"),
        "phase5.target_vs_olr_kg_m3_day": (2.0, "AD-003"),
    }
    for parameter_id, (value, source_row_id) in expected.items():
        assert structural[parameter_id].selected_candidate.source_kind.value in {
            "structural_placeholder", "existing_workbook"
        }
        selected = literature[parameter_id].selected_candidate
        assert literature[parameter_id].active_value == pytest.approx(value)
        assert selected.source_row_id == source_row_id
        assert selected.quality_class == "B"
        assert selected.stable_identifier and selected.stable_identifier.startswith("10.")
        assert selected.transferability_class == "proxy_high"
        assert selected.warnings


def test_ad1_operating_evidence_is_route_scoped_and_reportable_without_changing_values():
    resolver = ParameterResolver(load_default_registry())
    ad1 = {
        item.parameter_id: item
        for item in resolver.resolve(_context(CalculationMode.STRUCTURAL, digester="AD1"))
    }
    ad2 = {
        item.parameter_id: item
        for item in resolver.resolve(_context(CalculationMode.STRUCTURAL, digester="AD2"))
    }

    expected = {
        "phase5.digester_temperature_c": (
            35.0, "B", "10.1016/j.biortech.2011.07.020", "Phase5Parameters:88"
        ),
        "phase5.digester_pH": (
            7.2, "C", "10.1016/j.rser.2022.112092", "Phase5Parameters:89"
        ),
        "phase5.target_vs_olr_kg_m3_day": (
            1.5, "B", "10.1016/j.rser.2022.112092", "Phase5Parameters:90"
        ),
    }
    for parameter_id, (value, quality, doi, row_id) in expected.items():
        selected = ad1[parameter_id].selected_candidate
        assert ad1[parameter_id].active_value == pytest.approx(value)
        assert selected.quality_class == quality
        assert selected.stable_identifier == doi
        assert selected.source_row_id == row_id
        assert selected.readiness_state.value == "D4"
        assert selected.applicability.scenario_ids == ("AD1",)
        assert selected.source_title
        assert selected.warnings
        # Other digester routes keep their unresolved shared fallback.
        assert ad2[parameter_id].selected_candidate.quality_class == "E"
        assert not ad2[parameter_id].selected_candidate.stable_identifier

    assert "upper endpoint 7.2 is a proxy assumption" in " ".join(
        ad1["phase5.digester_pH"].selected_candidate.warnings
    )
    json.dumps(to_json_compatible(list(ad1.values())), allow_nan=False)


def test_struvite_literature_candidates_are_nr2_scoped_and_change_reported_design():
    resolver = ParameterResolver(load_default_registry())
    structural = {
        item.parameter_id: item
        for item in resolver.resolve(
            _context(CalculationMode.STRUCTURAL, nutrient="NR2")
        )
    }
    literature = {
        item.parameter_id: item
        for item in resolver.resolve(
            _context(CalculationMode.LITERATURE_DEFAULT, nutrient="NR2")
        )
    }

    ratio_id = "phase7.struvite_magnesium_to_p_molar_ratio"
    residence_id = "phase7.struvite_residence_time_min"
    pH_id = "phase7.struvite_target_pH"
    assert structural[ratio_id].active_value == pytest.approx(1.2)
    assert structural[residence_id].active_value == pytest.approx(60.0)
    assert structural[pH_id].active_value == pytest.approx(8.5)
    assert structural[ratio_id].selected_candidate.quality_class == "E"

    expected = {
        ratio_id: (1.0, "TSARIDOU2023-04", "mol Mg/mol P"),
        residence_id: (30.0, "TSARIDOU2023-06", "min"),
    }
    for parameter_id, (value, row_id, unit) in expected.items():
        selected = literature[parameter_id]
        candidate = selected.selected_candidate
        assert selected.active_value == pytest.approx(value)
        assert candidate.source_row_id == row_id
        assert candidate.unit == unit
        assert candidate.quality_class == "C"
        assert candidate.stable_identifier == "10.30955/gnc2023.00314"
        assert candidate.applicability.scenario_ids == ("NR2",)
        assert candidate.readiness_state.value == "D4"
        assert candidate.warnings

    # The source's N:Mg:P order is 1:1.5:1.5, so Mg:P is 1.0, not 1.5.
    assert "1:1.5:1.5" in literature[ratio_id].selected_candidate.basis
    assert literature[pH_id].selected_candidate.quality_class == "E"
    nr4 = {
        item.parameter_id: item
        for item in resolver.resolve(
            _context(CalculationMode.LITERATURE_DEFAULT, nutrient="NR4")
        )
    }
    assert nr4[ratio_id].selected_candidate.quality_class == "E"

    model_overrides = resolver.model_overrides(tuple(literature.values()))
    struvite_overrides = {
        key: value
        for key, value in model_overrides.items()
        if key.startswith("struvite_")
    }
    model = create_phase7_scenario(
        "NR2", parameter_overrides=struvite_overrides
    ).simulate()
    reactor = model.units["R711"]
    assert reactor.parameters.magnesium_to_p_molar_ratio == pytest.approx(1.0)
    assert reactor.parameters.residence_time_min == pytest.approx(30.0)
    # pH is deliberately not activated: the current model reports it but does
    # not use it to determine alkalinity/base demand or struvite recovery.
    assert reactor.parameters.target_pH == pytest.approx(8.5)
    assert reactor.design_results["Working volume"] == pytest.approx(
        reactor.design_results["Liquid throughput"] * 0.5
    )
    serialized = to_json_compatible(literature[ratio_id])
    assert serialized["selected_candidate"]["source_row_id"] == "TSARIDOU2023-04"
    assert serialized["selected_candidate"]["quality_class"] == "C"


def test_guo_precipitation_conditions_are_opt_in_only_for_pr3():
    registry = load_default_registry()
    resolver = ParameterResolver(registry)
    structural = {
        item.parameter_id: item
        for item in resolver.resolve(_context(CalculationMode.STRUCTURAL, "PR3"))
    }
    literature = {
        item.parameter_id: item
        for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT, "PR3"))
    }
    other_route = {
        item.parameter_id: item
        for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT, "PR1"))
    }
    other_route_structural = {
        item.parameter_id: item
        for item in resolver.resolve(_context(CalculationMode.STRUCTURAL, "PR1"))
    }

    expected = {
        "phase4.target_pH": (5.0, "GUO2022_PRECIPITATION_PH"),
        "phase4.precipitation_temperature_C": (60.0, "GUO2022_PRECIPITATION_TEMPERATURE"),
    }
    for parameter_id, (value, row_id) in expected.items():
        assert structural[parameter_id].selected_candidate.source_dataset.endswith(
            "greenhub_feed_inputs.xlsx"
        )
        candidate = literature[parameter_id].selected_candidate
        assert literature[parameter_id].active_value == pytest.approx(value)
        assert candidate.source_row_id == row_id
        assert candidate.source_dataset.endswith(
            "grass_clover_pilot_press_PEF_protein_separation_guo_2022_abstract_reference.csv"
        )
        assert candidate.stable_identifier == "10.1016/j.fufo.2022.100173"
        assert candidate.quality_class == "B"
        assert candidate.readiness_state.value == "D4"
        assert candidate.applicability.scenario_ids == ("PR3",)
        assert candidate.warnings
        assert other_route[parameter_id].selected_candidate.source_row_id != row_id
        assert other_route[parameter_id].selected_candidate.stable_identifier != (
            "10.1016/j.fufo.2022.100173"
        )

    assert other_route_structural["phase4.target_pH"].active_value == pytest.approx(4.5)
    assert (
        other_route_structural["phase4.target_pH"].selected_candidate.quality_class
        == "E"
    )
    assert other_route_structural["phase4.target_pH"].selected_candidate.source_row_id != (
        "Phase4Parameters:91"
    )

    model_values = resolver.model_overrides(tuple(literature.values()))
    assert model_values["target_pH"] == pytest.approx(5.0)
    assert model_values["precipitation_temperature_C"] == pytest.approx(60.0)


def test_run_override_precedence_bounds_and_json_safety():
    registry = load_default_registry()
    resolver = ParameterResolver(registry)
    override = ParameterOverride("phase4.precipitation_efficiency", 0.25, unit="fraction")
    pH_override = ParameterOverride("phase4.target_pH", 4.2, unit="pH")
    resolved = resolver.resolve(
        _context(CalculationMode.LITERATURE_DEFAULT),
        run_overrides=(override, pH_override),
    )
    by_id = {item.parameter_id: item for item in resolved}
    assert by_id[override.parameter_id].active_value == pytest.approx(0.25)
    assert by_id[override.parameter_id].override_status == "run_specific_user_override"
    assert by_id[pH_override.parameter_id].active_value == pytest.approx(4.2)
    assert by_id[pH_override.parameter_id].override_status == "run_specific_user_override"
    json.dumps(to_json_compatible(resolved), allow_nan=False)
    with pytest.raises(ValueError):
        resolver.resolve(
            _context(CalculationMode.EXPERT_OVERRIDE),
            run_overrides=(ParameterOverride(override.parameter_id, 1.1, unit="fraction"),),
        )


def test_editable_and_machine_registries_are_deterministic(tmp_path):
    registry = load_default_registry()
    resolved = ParameterResolver(registry).resolve(_context(CalculationMode.STRUCTURAL))
    editable = build_editable_registry(registry, resolved)
    assert len(editable) == len(registry)
    assert any(item.editable_mode.value == "expert" for item in editable)
    first = export_parameter_registries(tmp_path / "first")
    second = export_parameter_registries(tmp_path / "second")
    for key in first:
        assert first[key].read_bytes() == second[key].read_bytes()
