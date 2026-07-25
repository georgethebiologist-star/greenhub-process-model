import pytest


def test_dryer_hits_selected_product_moisture(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["DR401"]
    product = unit.outs[0]
    moisture = float(product.imass["Water"]) / product.F_mass
    assert moisture == pytest.approx(unit.parameters.target_product_moisture_fraction)
