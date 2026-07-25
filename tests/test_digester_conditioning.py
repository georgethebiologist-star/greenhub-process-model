import biosteam as bst
import pytest

from Greenhub.phase5_units import DigesterFeedConditioner, conditioning_parameters_from_mapping


def test_conditioning_adds_declared_solution_mass(phase5_values):
    feed = bst.Stream("conditioning_feed", Water=95.0, Glucose=5.0, units="kg/hr")
    unit = DigesterFeedConditioner(
        "M598",
        ins=(
            feed,
            bst.Stream("conditioning_base"),
            bst.Stream("conditioning_water"),
            bst.Stream("conditioning_nutrients"),
        ),
        outs="conditioned_test_feed",
        parameters=conditioning_parameters_from_mapping(phase5_values, enabled=True),
    )
    unit.simulate()
    assert unit.outs[0].F_mass == pytest.approx(sum(i.F_mass for i in unit.ins))
    assert unit.base_solution_kg_hr == pytest.approx(unit.ins[1].F_mass)
    assert unit.pure_base_kg_hr > 0.0
