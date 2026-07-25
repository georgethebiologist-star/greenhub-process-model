"""Fresh-flowsheet isolation and deterministic rebuild tests for Phase 7."""

from __future__ import annotations

import pytest

from Greenhub.systems import create_phase7_scenario


def test_phase7_scenario_isolation():
    phosphorus = create_phase7_scenario("NR2")
    assert "R711" in phosphorus.parameters["phase7_unit_ids"]
    assert "A721" not in phosphorus.parameters["phase7_unit_ids"]
    ammonia = create_phase7_scenario("NR3")
    assert "A721" in ammonia.parameters["phase7_unit_ids"]
    assert "R711" not in ammonia.parameters["phase7_unit_ids"]


def test_phase7_deterministic_rebuild():
    first = create_phase7_scenario("NR4").simulate()
    first_values = (
        first.metrics["phosphorus_product_kg_hr"],
        first.metrics["ammonium_product_kg_hr"],
        first.metrics["gross_electricity_kw"],
    )
    second = create_phase7_scenario("NR4").simulate()
    second_values = (
        second.metrics["phosphorus_product_kg_hr"],
        second.metrics["ammonium_product_kg_hr"],
        second.metrics["gross_electricity_kw"],
    )
    assert second_values == pytest.approx(first_values)
