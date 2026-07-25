import biosteam as bst
import pytest

from Greenhub.phase5_units import AnaerobicDigester, digestion_parameters_from_mapping


def test_organic_N_mineralizes_once_to_TAN(phase5_values):
    feed = bst.Stream("organic_n_feed", Water=99.0, OrganicNitrogen=1.0, units="kg/hr")
    reactor = AnaerobicDigester(
        "R594",
        ins=feed,
        outs="organic_n_broth",
        parameters=digestion_parameters_from_mapping(phase5_values, enabled=True),
    )
    reactor.simulate()
    assert reactor.outs[0].imass["OrganicNitrogen"] == pytest.approx(0.3)
    total_tan_n = (
        reactor.outs[0].imass["Ammonium"] * 14.0067 / 18.03846
        + reactor.outs[0].imass["Ammonia"] * 14.0067 / 17.03052
    )
    assert 0.69 < total_tan_n < 0.71
