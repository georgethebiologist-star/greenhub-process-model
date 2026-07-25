import biosteam as bst

from Greenhub.phase5_units import AnaerobicDigester, digestion_parameters_from_mapping


def test_high_protein_feed_is_partly_digested_without_complete_conversion(phase5_values):
    feed = bst.Stream("high_protein_feed", Water=80.0, SolubleProtein=20.0, units="kg/hr")
    reactor = AnaerobicDigester(
        "R593",
        ins=feed,
        outs="high_protein_broth",
        parameters=digestion_parameters_from_mapping(phase5_values, enabled=True),
    )
    reactor.simulate()
    residual = float(reactor.outs[0].imass["SolubleProtein"])
    assert 0.0 < residual < 20.0
    assert reactor.generated_kg_hr["Ammonium"] > 0.0
