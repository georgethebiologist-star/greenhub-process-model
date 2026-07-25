import biosteam as bst
import pytest

from Greenhub.phase3_units import ScrewPress, press_parameters_from_mapping


def _press_feed():
    return bst.Stream(
        "press_feed",
        Water=65,
        Cellulose=20,
        SolubleProtein=5,
        Glucose=5,
        SuspendedSolids=5,
        units="kg/hr",
    )


def test_press_outlet_order_and_mass_closure(phase3_values):
    unit = ScrewPress(
        "S201",
        ins=_press_feed(),
        outs=("pressed_fibre_cake", "raw_liquid_fraction"),
        parameters=press_parameters_from_mapping(phase3_values),
    )
    unit.simulate()
    assert unit.outs[0].ID == "pressed_fibre_cake"
    assert unit.outs[1].ID == "raw_liquid_fraction"
    assert unit.ins[0].F_mass == pytest.approx(sum(stream.F_mass for stream in unit.outs))


def test_press_rejects_out_of_bounds_recovery(phase3_values):
    phase3_values["sugar_recovery_to_juice"] = 1.1
    with pytest.raises(ValueError, match="within"):
        press_parameters_from_mapping(phase3_values)

