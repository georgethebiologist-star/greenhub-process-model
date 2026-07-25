import pytest

from Greenhub.analytical import calculate_analytical_indicators


def test_indicators_from_known_glucose_solution():
    indicators = calculate_analytical_indicators(
        {"Water": 90.0, "Glucose": 10.0},
        volumetric_flow_m3_hr=0.1,
    )
    assert indicators["dry_solids_kg_hr"] == pytest.approx(10.0)
    assert indicators["soluble_sugars_g_L"] == pytest.approx(100.0)
    assert indicators["cod_kg_hr"] > 10.0
    assert indicators["toc_kg_hr"] > 0.0
