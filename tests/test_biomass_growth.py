def test_combined_anaerobic_biomass_is_generated(representative_phase5_reactor):
    reactor = representative_phase5_reactor
    assert reactor.generated_kg_hr["MicrobialBiomass"] > 0.0
    assert reactor.outs[0].imass["MicrobialBiomass"] > reactor.ins[0].imass["MicrobialBiomass"]
