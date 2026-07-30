import math
import pytest
from Greenhub.storage import StorageModel


def test_storage_no_degradation_keeps_inventory_and_reports_limitation():
    s = StorageModel(capacity_kg=1000.0, initial_inventory_kg=100.0, degradation_rate_per_day=None)
    out = s.simulate_step(inflow_kg=50.0, outflow_kg=10.0, days=7.0)

    # inventory should equal initial + inflow - outflow because no degradation is implemented
    assert math.isclose(out["inventory_kg"], 100.0 + 50.0 - 10.0, rel_tol=1e-12)
    assert out["applied_degradation_kg"] == 0.0
    assert "degradation_not_implemented" in out["provenance"]["limitations"]


def test_storage_with_degradation_applies_first_order_loss():
    # small k over 1 day
    s = StorageModel(capacity_kg=None, initial_inventory_kg=200.0, degradation_rate_per_day=0.1)
    out = s.simulate_step(inflow_kg=0.0, outflow_kg=0.0, days=1.0)
    expected = 200.0 * math.exp(-0.1 * 1.0)
    assert math.isclose(out["inventory_kg"], expected, rel_tol=1e-12)
    assert out["applied_degradation_kg"] == pytest.approx(200.0 - expected)
    assert "user_provided_degradation_rate" in out["provenance"]["sources"]
