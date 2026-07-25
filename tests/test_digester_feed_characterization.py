from Greenhub.analytical import calculate_analytical_indicators
from Greenhub.phase4_validation import stream_component_flows


def test_digester_feed_characterization_is_complete(representative_phase5_reactor):
    feed = representative_phase5_reactor.ins[0]
    indicators = calculate_analytical_indicators(
        stream_component_flows(feed),
        volumetric_flow_m3_hr=feed.F_mass / 1000.0,
    )
    assert indicators["total_wet_mass_kg_hr"] > 0.0
    assert indicators["cod_kg_hr"] > 0.0
    assert indicators["volatile_solids_kg_hr"] > 0.0
    assert indicators["total_nitrogen_kg_hr"] >= 0.0
    assert indicators["c_to_n_ratio"] is not None
