from dataclasses import replace

import biosteam as bst
import pytest

from Greenhub.phase3_units import ScrewPress, press_parameters_from_mapping


def _unit(parameters):
    feed = bst.Stream("feed", Water=80, Cellulose=15, Glucose=5, units="kg/hr")
    return ScrewPress("S201", ins=feed, outs=("cake", "juice"), parameters=parameters)


def test_cake_moisture_priority_hits_feasible_target(phase3_values):
    parameters = replace(
        press_parameters_from_mapping(phase3_values),
        cake_moisture_fraction=0.50,
        juice_yield_kg_per_kg_wet_feed=None,
        constraint_priority="cake_moisture_priority",
    )
    unit = _unit(parameters)
    unit.simulate()
    moisture = unit.outs[0].imass["Water"] / unit.outs[0].F_mass
    assert moisture == pytest.approx(0.50)


def test_impossible_cake_moisture_raises(phase3_values):
    parameters = replace(
        press_parameters_from_mapping(phase3_values),
        cake_moisture_fraction=0.99,
        juice_yield_kg_per_kg_wet_feed=None,
        constraint_priority="cake_moisture_priority",
    )
    with pytest.raises(ValueError, match="physically impossible"):
        _unit(parameters).simulate()

