"""Process-order construction and interaction tests for Phase 7."""

from __future__ import annotations

import pytest

from Greenhub.systems import create_phase7_scenario


@pytest.mark.parametrize("order", ["A", "B", "C"])
def test_integrated_process_orders(order):
    model = create_phase7_scenario("NR4", process_order=order).simulate()
    assert model.input_bundle.process_order == order
    assert "R711" in model.units
    assert "A721" in model.units


def test_order_d_rejected_for_targeted_scenario():
    with pytest.raises(ValueError, match="cannot use Order D"):
        create_phase7_scenario("NR4", process_order="D")


def test_order_c_requires_phosphorus_route():
    with pytest.raises(ValueError, match="requires an active phosphorus"):
        create_phase7_scenario("NR3", process_order="C")
