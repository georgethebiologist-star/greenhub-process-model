import biosteam as bst

from Greenhub.phase5_units import AnaerobicDigester, digestion_parameters_from_mapping


def test_organic_phosphorus_is_released_not_destroyed(phase5_values):
    feed = bst.Stream("organic_p_feed", Water=89.9, Glucose=10.0, OrganicPhosphorus=0.1, units="kg/hr")
    reactor = AnaerobicDigester(
        "R597",
        ins=feed,
        outs="organic_p_broth",
        parameters=digestion_parameters_from_mapping(phase5_values, enabled=True),
    )
    reactor.simulate()
    assert reactor.outs[0].imass["OrganicPhosphorus"] < 0.1
    assert reactor.outs[0].imass["Orthophosphate"] > 0.0
