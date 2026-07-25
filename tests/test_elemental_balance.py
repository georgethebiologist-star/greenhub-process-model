import pytest

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.systems import create_greenhub_system


def test_elemental_flow_calculation_for_glucose():
    elements = calculate_elemental_flows({"Glucose": 180.15588})
    assert elements["carbon"] == pytest.approx(72.0642, rel=1e-5)
    assert elements["nitrogen"] == 0.0


def test_system_elemental_balance_closes():
    model = create_greenhub_system()
    model.system.simulate()
    inlet = calculate_elemental_flows({ID: float(model.streams["feed"].imass[ID]) for ID in model.streams["feed"].chemicals.IDs})
    outlet = calculate_elemental_flows({ID: float(model.streams["clarified_liquid"].imass[ID] + model.streams["wet_solids"].imass[ID]) for ID in model.streams["feed"].chemicals.IDs})
    assert inlet == pytest.approx(outlet, abs=1e-6)
