from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS, get_group, validate_component_groups


def test_groups_reference_valid_components():
    validate_component_groups()
    known = set(chemicals.IDs)
    assert all(group <= known for group in COMPONENT_GROUPS.values())


def test_key_groups_have_expected_members():
    assert "Glucose" in get_group("soluble_sugars")
    assert "SuspendedSolids" in get_group("suspended_solids")
    assert "Orthophosphate" in get_group("phosphorus_components")
