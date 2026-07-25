import pytest

from Greenhub.systems import create_phase5_scenario


def test_repeated_phase5_construction_is_isolated_and_deterministic():
    first = create_phase5_scenario("AD1").simulate()
    first_methane = first.metrics["raw_biogas_methane_nm3_hr"]
    second = create_phase5_scenario("AD1").simulate()
    assert first.flowsheet is not second.flowsheet
    assert first.units["R501"] is not second.units["R501"]
    assert second.metrics["raw_biogas_methane_nm3_hr"] == pytest.approx(first_methane)
