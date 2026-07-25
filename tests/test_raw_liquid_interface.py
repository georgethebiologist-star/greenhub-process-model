from Greenhub.systems import create_phase3_scenario


def test_modes_share_standard_raw_liquid_interface():
    measured = create_phase3_scenario("F0").simulate()
    grass = create_phase3_scenario("F2").simulate()
    for model in (measured, grass):
        interface = model.raw_liquid_interface
        assert interface.stream_id == "raw_liquid_fraction"
        assert interface.volumetric_flow_m3_hr > 0.0
        assert "cod_kg_hr" in interface.indicators
        assert "tss_mg_L" in interface.indicators
    assert measured.raw_liquid_interface.measured_reconciliation
    assert not grass.raw_liquid_interface.measured_reconciliation

