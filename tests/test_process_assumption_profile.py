from Greenhub.application.decision_support_service import default_configuration, options
from Greenhub.process_assumption_profile import screening_pretreatment_parameters, screening_process_assumption_profile, screening_storage_conditions
from Greenhub.application.contracts.requests import SimulationRequest
from Greenhub.application.biomass_schedule import build_empirical_biomass_schedule
from Greenhub.application.contracts.requests import BiomassSchedule
from Greenhub.application.decision_support_service import options
from Greenhub.dynamic_biosteam_adapter import DynamicBioSTEAMAdapterConfig
from Greenhub.pretreatment_state import apply_screening_pretreatment_state
from Greenhub.state_engine import state_from_stream


def test_process_assumption_profile_is_opt_in_and_traceable():
    assert default_configuration()["use_screening_process_assumptions"] is False
    conditions = screening_storage_conditions()
    assert conditions["storage_days"] == 30.0
    SimulationRequest.from_dict({
        "schema_version": "1.0.0",
        "request_id": "assumption-profile-test",
        "project_id": "test",
        "storage_conditions": conditions,
    })
    assert screening_process_assumption_profile()["storage_traceability"]["status"] == "screening_assumption"
    pretreatment = screening_pretreatment_parameters()
    assert pretreatment["water_addition_kg_per_kg_wet_feed"] == 5.0
    assert pretreatment["calculation_ready"] is False
    schedule = build_empirical_biomass_schedule(BiomassSchedule(source_id="varta_grass", location="North Brabant", accessible_area_ha=100.0, harvest_yield_tonnes_per_ha=20.0, collection_efficiency=0.8))
    assert schedule["feedstock_source_id"] == "varta_grass"
    assert schedule["feedstock_location"] == "North Brabant"
    assert schedule["availability_basis"]["calculated_collectable_biomass_tonnes"] == 1600.0
    assert any(item["id"] == "grass_varta_default" for item in options()["feedstock_options"])
    config = DynamicBioSTEAMAdapterConfig(
        pretreatment_water_addition_kg_per_kg_wet_feed=5.0,
        press_energy_kwh_per_t_wet_feed=1.25,
    )
    assert config.pretreatment_water_addition_kg_per_kg_wet_feed == 5.0
    state = apply_screening_pretreatment_state({"Water": 700.0, "SolubleProtein": 100.0}, water_addition_kg_per_kg_wet_feed=0.5, press_energy_kwh_per_t_wet_feed=1.25)
    assert state.water_added_kg_hr == 400.0
    assert state.press_energy_kwh_hr == 1.0
    assert abs(state.mass_residual_kg_hr) < 1e-12
    inventory = state.to_lca_inventory(annualization_factor=100.0)
    assert inventory[0]["quantity"] == 100.0
    assert inventory[1]["quantity"] == 40000.0
    assert "screening_process_assumptions" in options()
