from Greenhub.equilibria import ammonia_equilibrium


def test_high_TAN_equilibrium_is_mass_bounded():
    result = ammonia_equilibrium(10.0, pH=7.5, temperature_K=328.15)
    assert result.ammonium_n + result.ammonia_n == 10.0
    assert 0.0 < result.unionized_fraction < 1.0
    assert result.ammonium_mass > result.ammonia_mass
