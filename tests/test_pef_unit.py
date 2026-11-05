import biosteam as bst
import pytest

from Greenhub.phase3_units import PulsedElectricField, pef_parameters_from_mapping


@pytest.fixture
def synthetic_pef_parameters():
    # Isolated unit tests only: these synthetic values do not activate the retired F2/F3 route.
    return {
        "specific_energy_kwh_per_t_wet": 2.0,
        "electric_field_strength_kv_per_cm": 20.0,
        "pulse_width_us": 5.0,
        "number_of_pulses": 10.0,
        "treatment_time_s": 2.0,
        "treatment_temperature_c": 25.0,
        "temperature_rise_c": None,
        "temperature_mode": "specified",
        "thermal_retention_efficiency": 0.8,
        "effective_heat_capacity_kj_per_kg_k": 4.18,
        "cell_disintegration_index": 0.5,
        "soluble_protein_release_fraction": 0.25,
        "suspended_protein_solubilization_fraction": 0.5,
        "sugar_release_fraction": 0.5,
        "soluble_cod_increase_fraction": 0.2,
        "dissolved_nitrogen_release_fraction": 0.2,
        "dissolved_phosphorus_release_fraction": 0.2,
        "potassium_release_fraction": 0.2,
        "juice_yield_improvement_fraction": 0.1,
        "mass_loss_fraction": 0.0,
    }


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


def test_pef_transfers_only_declared_pools(synthetic_pef_parameters):
    unit = PulsedElectricField(
        "U201",
        ins=_feed(),
        outs=("treated", "loss"),
        parameters=pef_parameters_from_mapping(synthetic_pef_parameters),
    )
    unit.simulate()
    assert unit.outs[0].imass["SolubleProtein"] > 0.0
    assert unit.outs[0].imass["Glucose"] > 0.0
    assert unit.outs[1].F_mass == pytest.approx(0.0)


def test_zero_pef_energy_is_supported(synthetic_pef_parameters):
    synthetic_pef_parameters["specific_energy_kwh_per_t_wet"] = 0.0
    unit = PulsedElectricField(
        "U201",
        ins=_feed(),
        outs=("treated", "loss"),
        parameters=pef_parameters_from_mapping(synthetic_pef_parameters),
    )
    unit.simulate()
    assert unit.power_utility.consumption == 0.0


def test_negative_pef_parameter_fails(synthetic_pef_parameters):
    synthetic_pef_parameters["specific_energy_kwh_per_t_wet"] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        pef_parameters_from_mapping(synthetic_pef_parameters)

