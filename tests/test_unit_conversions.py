import pytest

from Greenhub.conversions import (
    K_TO_K2O,
    N_TO_NH4,
    P_TO_P2O5,
    concentration_to_kg_hr,
    convert_element_reporting,
    flow_to_kg_hr,
)


def test_flow_conversions():
    assert flow_to_kg_hr(2.4, "t/d") == pytest.approx(100.0)
    assert flow_to_kg_hr(24.0, "m3/d", density_kg_m3=1000.0) == pytest.approx(1000.0)
    assert flow_to_kg_hr(1000.0, "L/h", density_kg_m3=1000.0) == pytest.approx(1000.0)


def test_concentration_to_flow_conversion():
    assert concentration_to_kg_hr(1000.0, "mg/L", volumetric_flow_m3_hr=2.0) == pytest.approx(2.0)
    assert concentration_to_kg_hr(10.0, "% wet mass", wet_mass_flow_kg_hr=100.0) == pytest.approx(10.0)
    assert concentration_to_kg_hr(100.0, "g/kg TS", dry_solids_flow_kg_hr=20.0) == pytest.approx(2.0)


def test_element_reporting_conversions():
    assert convert_element_reporting(1.0, "N", "NH4+") == pytest.approx(N_TO_NH4)
    assert convert_element_reporting(1.0, "P", "P2O5") == pytest.approx(P_TO_P2O5)
    assert convert_element_reporting(1.0, "K", "K2O") == pytest.approx(K_TO_K2O)


def test_incompatible_volumetric_conversion_requires_density():
    with pytest.raises(ValueError, match="Density"):
        flow_to_kg_hr(1.0, "m3/h")
