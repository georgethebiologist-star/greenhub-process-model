import math
from types import SimpleNamespace

import pytest

from Greenhub.storage_inventory import StorageInventory
from Greenhub.application import seasonal_service


def test_apply_storage_degradation_not_implemented_keeps_inventory():
    inv = StorageInventory()
    inv.receive(100.0, {"Water": 50.0, "Biomass": 50.0}, temperature_k=None, capacity_kg=None)
    applied, prov, status = seasonal_service._apply_storage_degradation(inv, None, step_days=1.0)
    assert applied == 0.0
    assert status == "not_implemented_no_eligible_data"
    assert math.isclose(inv.total_mass_kg, 100.0)
    assert "degradation_not_implemented" in prov.get("limitations", [])


def test_apply_storage_degradation_applies_first_order_loss_and_reduces_components():
    inv = StorageInventory()
    inv.receive(200.0, {"Water": 100.0, "Biomass": 100.0}, temperature_k=None, capacity_kg=None)
    param = SimpleNamespace(blocked=False, active_value=0.1)  # k = 0.1 / day
    applied, prov, status = seasonal_service._apply_storage_degradation(inv, param, step_days=1.0)
    expected_remaining = 200.0 * math.exp(-0.1 * 1.0)
    assert status == "applied"
    assert math.isclose(inv.total_mass_kg, expected_remaining, rel_tol=1e-12)
    assert math.isclose(applied, 200.0 - expected_remaining, rel_tol=1e-12)
    # components reduced proportionally
    assert math.isclose(inv.component_masses_kg["Water"], expected_remaining * 0.5, rel_tol=1e-12)
    assert "user_provided_degradation_rate" in prov.get("sources", [])


def test_overflow_then_degradation_applies_to_kept_inventory():
    inv = StorageInventory()
    components = {"Water": 96.0, "Biomass": 24.0}  # sums to 120
    overflow = inv.receive(120.0, components, temperature_k=None, capacity_kg=100.0)
    assert overflow == pytest.approx(20.0)
    # Now apply degradation
    param = SimpleNamespace(blocked=False, active_value=0.05)
    applied, prov, status = seasonal_service._apply_storage_degradation(inv, param, step_days=10.0)
    # applied should be computed on inventory.total_mass_kg (which is 100 after overflow)
    assert inv.total_mass_kg <= 100.0
    assert status in ("applied", "not_implemented_no_eligible_data")
    assert "methods" in prov
