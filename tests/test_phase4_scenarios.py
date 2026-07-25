import pytest

from Greenhub.systems import create_phase4_scenario


@pytest.mark.parametrize("scenario", ["PR0", "PR1", "PR2", "PR3"])
def test_active_phase4_scenarios_share_common_outputs(scenario):
    model = create_phase4_scenario(scenario).simulate()
    assert "dry_protein_product" in model.streams
    assert "conditioned_protein_depleted_liquid" in model.streams
    assert abs(model.validation.overall_error_kg_hr) < 1e-6
