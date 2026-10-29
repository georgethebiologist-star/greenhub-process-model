"""Storage residence, accounting and seasonal timing invariants."""
from dataclasses import replace
import math

import pytest

from Greenhub.application.contracts import BiomassSchedule, OperatingSchedule, SimulationRequest
from Greenhub.application.seasonal_service import _biomass_schedule_operating_hours
from Greenhub.storage import apply_storage_conditions
from Greenhub.storage_inventory import StorageInventory
from Greenhub.storage_reactions import simulate_reactions
from Greenhub.time_grid import generate_time_grid


def test_incoming_residence_age_is_removed_proportionally_with_overflow():
    inventory = StorageInventory(total_mass_kg=100, component_masses_kg={"Water": 100}, age_mass_kg_h=2400)
    overflow = inventory.receive(100, {"Water": 100}, None, 150, age_h=72)
    assert overflow == 50
    assert inventory.average_age_h == pytest.approx(48)
    assert inventory.age_mass_kg_h == pytest.approx(7200)
    inventory.withdraw(100)
    assert inventory.average_age_h == pytest.approx(48)


@pytest.mark.parametrize("mass,components,age", [(float('nan'), {}, 0), (1, {"Water": -1, "Glucose": 2}, 0), (1, {"Water": 1}, -1)])
def test_invalid_receipt_is_atomic(mass, components, age):
    inventory = StorageInventory()
    with pytest.raises(ValueError):
        inventory.receive(mass, components, None, None, age_h=age)
    assert inventory.total_mass_kg == 0
    assert inventory.component_masses_kg == {}


def test_active_month_shutdown_and_partial_season_hours():
    request = SimulationRequest("1.0.0", "schedule-unit", "greenhub", biomass_schedule=BiomassSchedule(active_months=(4, 6)),
        operating_schedule=OperatingSchedule(operating_hours_per_day=8, shutdown_dates=("2026-04-16",)))
    grid = generate_time_grid("2026-04-01", "2026-06-30", "monthly")
    assert _biomass_schedule_operating_hours(grid[0], request, 30) == (16-1)*8
    assert _biomass_schedule_operating_hours(grid[1], request, 30) == 0
    assert _biomass_schedule_operating_hours(grid[2], request, 30) == 30*8
    daily = generate_time_grid("2026-04-14", "2026-04-16", "daily")
    assert [_biomass_schedule_operating_hours(step, request, 30) for step in daily] == [0, 8, 0]


def test_reaction_lag_is_not_reset_on_carried_batch():
    config = {"storage_days": 0.4, "aerobic_fraction": 0, "allow_assumptions": True,
              "reaction_ids": ["R09"], "max_step_days": 0.01}
    initial = {"Glucose": 10, "Water": 100}
    first = simulate_reactions(initial, config)
    second = simulate_reactions(first["retained_component_masses_kg"], {**config, "elapsed_days": 0.4})
    whole = simulate_reactions(initial, {**config, "storage_days": 0.8})
    assert second["retained_component_masses_kg"]["Glucose"] == pytest.approx(10*math.exp(-0.25*0.3))
    assert second["retained_component_masses_kg"]["LacticAcid"] == pytest.approx(whole["retained_component_masses_kg"]["LacticAcid"])


def test_core_element_discrepancy_is_explicit_blocker():
    from Greenhub.chemicals import create_chemicals
    report = apply_storage_conditions({"Glucose": 180.156, "Water": 1000},
        {"model": "grass_reactions", "storage_days": 2, "aerobic_fraction": 1,
         "allow_assumptions": True, "reaction_ids": ["R08"]}, create_chemicals().IDs)
    assert report["mass_balance_residual_kg"] == pytest.approx(0, abs=1e-8)
    assert max(abs(v) for v in report["element_balance_residual_kg"].values()) < 1e-8
    assert any(abs(v) > 1e-5 for v in report["core_element_residual_kg"].values())
    assert any("element reconciliation" in b for b in report["blockers"])
    assert report["calculation_complete"] is False
    assert report["validated_simulation_ready"] is False


def test_processing_age_is_measured_before_remainder_aging(tmp_path):
    from Greenhub.application.simulation_service import SimulationService
    from Greenhub.parameters import ResolutionMode
    from Greenhub.application.contracts import InitialStorageInventory
    service = SimulationService(run_root=tmp_path)
    service.feed_profiles.register_mapping({"profile_id": "storage_age_day", "resolution": "daily", "points": [{"period": "2026-07-01", "available_wet_biomass_kg": 0}]})
    request = SimulationRequest("1.0.0", "storage-age", "greenhub", resolution_mode=ResolutionMode.QUASI_DYNAMIC,
        start_date="2026-07-01", end_date="2026-07-01", time_step="daily", feed_supply_profile_id="storage_age_day",
        initial_storage_inventory=InitialStorageInventory(total_mass_kg=100, storage_age_h=48),
        operating_schedule=OperatingSchedule(operating_hours_per_day=24, target_throughput_kg_hr=1))
    result = service.execute_run(service.create_run(request))
    row = result.storage_inventory_series[0]
    assert row["biomass_withdrawn_kg"] == pytest.approx(24)
    assert row["storage_age_h"] == pytest.approx(72)
    assert row["processed_feed_storage_age_h"] == pytest.approx(48)
    assert result.process_state_series[0]["inlet"]["storage_age_h"] == pytest.approx(48)
    assert row["storage_mass_residual_kg"] == pytest.approx(0, abs=1e-8)
    evolution = next(item for item in result.inventory_evolution if item["inventory_id"] == "biomass_storage")
    assert evolution["initial_kg"] == pytest.approx(100)
    assert evolution["final_kg"] == pytest.approx(76)
    assert evolution["status"] == "calculated_from_seasonal_storage_inventory"
    assert len(result.process_state_history) == 1
    assert result.process_state_history[0]["time"] == "2026-07-01"
    assert result.process_state_history[0]["inlet"]["storage_age_h"] == pytest.approx(48)
    assert evolution["timeline"][0]["time"] == "2026-07-01"
    assert evolution["timeline"][0]["inventory_kg"] == pytest.approx(76)


def test_steady_storage_report_populates_state_inventory_evolution(tmp_path):
    from Greenhub.application.simulation_service import SimulationService

    service = SimulationService(run_root=tmp_path)
    request = SimulationRequest(
        "1.0.0", "steady-storage-state", "greenhub",
        wet_feed_rate_kg_hr=100.0,
        storage_conditions={
            "model": "component_retention",
            "storage_days": 2.0,
            "aerobic_fraction": 1.0,
        },
    )
    result = service.execute_run(service.create_run(request))
    evolution = next(item for item in result.inventory_evolution if item["inventory_id"] == "biomass_storage")
    assert evolution["status"] == "calculated_from_steady_storage_report"
    assert evolution["basis"] == "steady_state_storage_condition"
    assert evolution["initial_kg"] == pytest.approx(100.0)
    assert evolution["final_kg"] <= evolution["initial_kg"]
    assert evolution["timeline"] == []
