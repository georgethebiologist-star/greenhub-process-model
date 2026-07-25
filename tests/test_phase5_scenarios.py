import pytest

from Greenhub.phase5_inputs import load_phase5_inputs
from Greenhub.scenarios import DIGESTION_SCENARIOS
from Greenhub.systems import create_phase5_scenario


def test_active_and_data_gated_scenarios():
    assert all(DIGESTION_SCENARIOS[ID].active for ID in ("AD0", "AD1", "AD2", "AD3"))
    assert all(not DIGESTION_SCENARIOS[ID].active for ID in ("AD4", "AD5"))
    assert not DIGESTION_SCENARIOS["AD0"].digestion_enabled
    assert load_phase5_inputs(scenario_id="AD3").parameter_values["digester_temperature_c"] == 55.0
    ad2 = create_phase5_scenario("AD2").simulate()
    assert ad2.input_bundle.phase4_scenario_id == "PR0"
    assert ad2.metrics["raw_biogas_methane_nm3_hr"] > 0.0
    del ad2
    with pytest.raises(NotImplementedError, match="stage-specific"):
        create_phase5_scenario("AD4")
    with pytest.raises(NotImplementedError, match="biomass-retention"):
        create_phase5_scenario("AD5")
