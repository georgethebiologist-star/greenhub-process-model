def test_phase5_system_has_named_units_and_outputs(simulated_phase5_ad1):
    model = simulated_phase5_ad1
    assert {"M501", "H501", "R501", "V501"}.issubset(model.units)
    assert {"raw_biogas", "digestate", "uncaptured_biogas"}.issubset(model.streams)
    assert model.system.ID.startswith("greenhub_phase5_")
    assert not model.system.recycle
    assert model.reactions["calculation_mode"] == "hybrid"
    assert model.reactions["hydrolysis"]
    assert model.data_needs
