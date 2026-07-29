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


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _context(mode, protein="PR1"):
    return SelectionContext(
        calculation_mode=mode,
        selected_scenarios=("F2", protein, "AD1", "BG2", "NR4"),
        month="July",
    )


def test_registry_ids_are_unique_and_source_is_immutable():
    before = _digest(LITERATURE_RECOVERY_PATH)
    registry = load_default_registry()
    ids = [item.parameter_id for item in registry]
    assert len(ids) == len(set(ids))
    assert _digest(LITERATURE_RECOVERY_PATH) == before
    assert registry.get("phase4.precipitation_efficiency").readiness_state.value == "D4"


def test_resolution_preserves_structural_mode_and_activates_only_pr1_literature():
    registry = load_default_registry()
    resolver = ParameterResolver(registry)
    structural = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.STRUCTURAL))}
    literature = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT))}
    combined = {item.parameter_id: item for item in resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT, "PR3"))}
    parameter_id = "phase4.precipitation_efficiency"
    assert structural[parameter_id].selected_candidate.source_dataset.endswith("greenhub_feed_inputs.xlsx")
    assert literature[parameter_id].active_value == pytest.approx(0.34)
    assert literature[parameter_id].selected_candidate.source_row_id == "REC-001"
    assert combined[parameter_id].selected_candidate.source_dataset.endswith("greenhub_feed_inputs.xlsx")


def test_run_override_precedence_bounds_and_json_safety():
    registry = load_default_registry()
    resolver = ParameterResolver(registry)
    override = ParameterOverride("phase4.precipitation_efficiency", 0.25, unit="fraction")
    resolved = resolver.resolve(_context(CalculationMode.LITERATURE_DEFAULT), run_overrides=(override,))
    by_id = {item.parameter_id: item for item in resolved}
    assert by_id[override.parameter_id].active_value == pytest.approx(0.25)
    assert by_id[override.parameter_id].override_status == "run_specific_user_override"
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
