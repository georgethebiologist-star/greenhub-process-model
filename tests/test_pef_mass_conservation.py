import pytest

from Greenhub.analytical import calculate_analytical_indicators, calculate_elemental_flows
from Greenhub.phase3_metrics import component_flows
from Greenhub.systems import create_phase3_scenario


def test_pef_conserves_mass_elements_protein_and_cod():
    model = create_phase3_scenario("F2").simulate()
    unit = model.units["U201"]
    feed = component_flows(unit.ins[0])
    outputs = {
        ID: sum(float(stream.imass[ID]) for stream in unit.outs)
        for ID in unit.ins[0].chemicals.IDs
    }
    assert sum(feed.values()) == pytest.approx(sum(outputs.values()), abs=1e-9)
    assert calculate_elemental_flows(feed) == pytest.approx(calculate_elemental_flows(outputs), abs=1e-9)
    feed_cod = calculate_analytical_indicators(feed, volumetric_flow_m3_hr=None)["cod_kg_hr"]
    output_cod = calculate_analytical_indicators(outputs, volumetric_flow_m3_hr=None)["cod_kg_hr"]
    assert output_cod == pytest.approx(feed_cod, abs=1e-9)

