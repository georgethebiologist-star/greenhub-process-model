import biosteam as bst

from Greenhub.phase5_units import AnaerobicDigester, digestion_parameters_from_mapping


def _run_sulfate_case(values, enabled):
    adjusted = dict(values, sulfate_reduction_enabled=enabled)
    feed = bst.Stream(f"sulfate_feed_{enabled}", Water=89.5, Glucose=10.0, SulfateIon=0.5, units="kg/hr")
    reactor = AnaerobicDigester(
        f"R59{5 if enabled else 6}",
        ins=feed,
        outs=f"sulfate_broth_{enabled}",
        parameters=digestion_parameters_from_mapping(adjusted, enabled=True),
    )
    reactor.simulate()
    return reactor


def test_sulphate_reduction_off_and_on(phase5_values):
    disabled = _run_sulfate_case(phase5_values, False)
    enabled = _run_sulfate_case(phase5_values, True)
    assert disabled.outs[0].imass["SulfateIon"] == 0.5
    assert enabled.outs[0].imass["SulfateIon"] < 0.5
    assert enabled.generated_kg_hr["HydrogenSulfide"] > disabled.generated_kg_hr["HydrogenSulfide"]
