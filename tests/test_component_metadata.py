from Greenhub.chemicals import chemicals
from Greenhub.component_metadata import COMPONENT_METADATA


def test_every_component_has_metadata():
    assert set(COMPONENT_METADATA) == set(chemicals.IDs)


def test_pseudo_component_conventions_are_documented():
    protein = COMPONENT_METADATA["SolubleProtein"]
    assert protein.real_or_pseudo == "pseudo"
    assert protein.molecular_weight_convention
    assert protein.property_surrogate
    assert protein.nitrogen_mass_fraction == 0.16


def test_aggregate_indicators_are_not_components():
    for aggregate in ("COD", "TOC", "TKN", "TS", "TotalNitrogen", "TotalPhosphorus"):
        assert aggregate not in chemicals.IDs
