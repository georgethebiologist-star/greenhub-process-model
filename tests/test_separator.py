import pytest

from Greenhub.separator import SeparatorParameters, resolve_separator_splits


def test_separator_precedence_and_convention():
    parameters = SeparatorParameters(
        component_splits_to_clarified={"Glucose": 0.8},
        group_splits_to_clarified={"soluble_sugars": 0.9},
    )
    resolved = resolve_separator_splits(parameters)
    assert resolved.splits_to_clarified["Glucose"] == pytest.approx(0.8)
    assert resolved.splits_to_clarified["Fructose"] == pytest.approx(0.9)
    assert resolved.source_by_component["Glucose"] == "component_override"


def test_separator_split_bounds_are_validated():
    with pytest.raises(ValueError, match="within"):
        resolve_separator_splits(SeparatorParameters(component_splits_to_clarified={"Water": 1.1}))
