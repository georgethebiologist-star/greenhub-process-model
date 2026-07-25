from dataclasses import replace

import biosteam as bst
import pytest

from Greenhub.phase3_units import PrimaryCentrifuge, centrifuge_parameters_from_mapping


def _centrifuge(parameters, *, water=90.0):
    feed = bst.Stream("raw", Water=water, SuspendedSolids=5, SolubleProtein=5, units="kg/hr")
    return PrimaryCentrifuge(
        "C301",
        ins=(feed, bst.Stream("wash"), bst.Stream("polymer")),
        outs=("clarified", "sludge"),
        parameters=parameters,
    )


def test_centrifuge_hits_sludge_moisture(phase3_values):
    unit = _centrifuge(centrifuge_parameters_from_mapping(phase3_values))
    unit.simulate()
    moisture = unit.outs[1].imass["Water"] / unit.outs[1].F_mass
    assert moisture == pytest.approx(0.80)


def test_impossible_sludge_moisture_raises(phase3_values):
    parameters = replace(
        centrifuge_parameters_from_mapping(phase3_values),
        sludge_solids_fraction=0.001,
        sludge_moisture_fraction=0.999,
    )
    with pytest.raises(ValueError, match="physically impossible"):
        _centrifuge(parameters, water=1.0).simulate()

