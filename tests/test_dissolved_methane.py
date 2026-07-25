from dataclasses import replace

import biosteam as bst
import pytest

from Greenhub.phase5_units import BiogasDisengagement, gas_partition_parameters_from_mapping


@pytest.mark.parametrize(
    "dissolved,capture,expected_raw,expected_digestate,expected_uncaptured",
    [
        (0.0, 1.0, 1.0, 0.0, 0.0),
        (0.2, 1.0, 0.8, 0.2, 0.0),
        (0.0, 0.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 1.0, 0.0, 0.0),
    ],
)
def test_dissolved_methane_and_capture_endpoints(
    phase5_values,
    dissolved,
    capture,
    expected_raw,
    expected_digestate,
    expected_uncaptured,
):
    parameters = gas_partition_parameters_from_mapping(phase5_values)
    parameters = replace(
        parameters,
        dissolved_methane_fraction=dissolved,
        gas_capture_efficiency=capture,
        raw_biogas_water_vapor_mol_fraction=0.0,
    )
    broth = bst.Stream(f"partition_broth_{dissolved}_{capture}", Water=99.0, Methane=1.0, units="kg/hr")
    unit = BiogasDisengagement(
        f"V59{int(dissolved * 10)}{int(capture)}",
        ins=broth,
        outs=(f"gas_{dissolved}_{capture}", f"digestate_{dissolved}_{capture}", f"loss_{dissolved}_{capture}"),
        parameters=parameters,
        digester_pH=7.2,
    )
    unit.simulate()
    assert unit.outs[0].imass["Methane"] == pytest.approx(expected_raw)
    assert unit.outs[1].imass["Methane"] == pytest.approx(expected_digestate)
    assert unit.outs[2].imass["Methane"] == pytest.approx(expected_uncaptured)
