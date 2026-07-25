from Greenhub.phase4_specifications import first_order_recovery, temperature_adjusted_rate_constant


def test_first_order_recovery_is_bounded_and_temperature_response_is_finite():
    recovery = first_order_recovery(maximum_recovery=0.9, rate_constant_per_min=0.1, residence_time_min=30)
    adjusted = temperature_adjusted_rate_constant(
        reference_rate_per_min=0.1,
        activation_energy_kj_per_mol=20,
        temperature_K=333.15,
        reference_temperature_K=298.15,
    )
    assert 0.0 < recovery < 0.9
    assert adjusted > 0.1
