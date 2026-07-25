from dataclasses import replace

import biosteam as bst
import pytest

from Greenhub.phase4_units import ProteinSeparator


def test_separator_uses_configured_precipitated_protein_capture(simulated_phase4_pr3):
    unit = simulated_phase4_pr3.units["C401"]
    feed = float(unit.ins[0].imass["PrecipitatedProtein"])
    cake = float(unit.outs[0].imass["PrecipitatedProtein"])
    assert cake / feed == pytest.approx(unit.parameters.precipitated_protein_capture_fraction)
    assert unit.ins[0].F_mass == pytest.approx(sum(stream.F_mass for stream in unit.outs))


@pytest.mark.parametrize("capture", [0.5, 1.0])
def test_separator_supports_partial_and_complete_protein_capture(
    capture,
    simulated_phase4_pr3,
):
    parameters = replace(
        simulated_phase4_pr3.parameters["separator"],
        precipitated_protein_capture_fraction=capture,
        cake_moisture_fraction=0.5,
    )
    feed = bst.Stream(
        f"separator_feed_{capture}",
        Water=90.0,
        PrecipitatedProtein=10.0,
        units="kg/hr",
    )
    unit = ProteinSeparator(
        f"C49{int(capture * 10)}",
        ins=feed,
        outs=(f"cake_{capture}", f"centrate_{capture}"),
        parameters=parameters,
    )
    unit.simulate()
    assert unit.outs[0].imass["PrecipitatedProtein"] == pytest.approx(10.0 * capture)
