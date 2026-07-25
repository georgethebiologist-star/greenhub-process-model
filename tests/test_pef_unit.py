import biosteam as bst
import pytest

from Greenhub.phase3_units import PulsedElectricField, pef_parameters_from_mapping


def _feed():
    return bst.Stream(
        "pef_feed",
        Water=65,
        SuspendedProtein=10,
        EntrappedSugars=5,
        ParticulateBiodegradableOrganics=5,
        ParticulateNitrogen=1,
        ParticulatePhosphorus=1,
        ParticulatePotassium=1,
        Cellulose=12,
        units="kg/hr",
    )


def test_pef_transfers_only_declared_pools(phase3_values):
    unit = PulsedElectricField(
        "U201",
        ins=_feed(),
        outs=("treated", "loss"),
        parameters=pef_parameters_from_mapping(phase3_values),
    )
    unit.simulate()
    assert unit.outs[0].imass["SolubleProtein"] > 0.0
    assert unit.outs[0].imass["Glucose"] > 0.0
    assert unit.outs[1].F_mass == pytest.approx(0.0)


def test_zero_pef_energy_is_supported(phase3_values):
    phase3_values["specific_energy_kwh_per_t_wet"] = 0.0
    unit = PulsedElectricField(
        "U201",
        ins=_feed(),
        outs=("treated", "loss"),
        parameters=pef_parameters_from_mapping(phase3_values),
    )
    unit.simulate()
    assert unit.power_utility.consumption == 0.0


def test_negative_pef_parameter_fails(phase3_values):
    phase3_values["specific_energy_kwh_per_t_wet"] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        pef_parameters_from_mapping(phase3_values)

