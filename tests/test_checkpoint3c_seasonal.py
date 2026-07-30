"""Checkpoint 3C seasonal and quasi-dynamic behavior."""

from __future__ import annotations

import json
import re
from io import BytesIO

import pytest

from api.app import create_app
from Greenhub.application import FeedProfileService, SimulationService
from Greenhub.application.contracts import (
    InitialStorageInventory,
    OperatingSchedule,
    SimulationRequest,
)
from Greenhub.application.seasonal_service import capacity_limited_throughput
from Greenhub.feed_profiles import (
    FeedProfile,
    FeedProfilePoint,
    load_feed_profile_csv,
    resolve_feed_profile,
)
from Greenhub.parameters import ResolutionMode
from Greenhub.storage_inventory import StorageInventory
from Greenhub.time_grid import generate_time_grid


def invoke(app, method: str, path: str, payload=None):
    body = b"" if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    captured = {}

    def start_response(status, headers):
        captured["status"] = int(status.split()[0])

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": "application/json",
        "wsgi.input": BytesIO(body),
    }
    response = json.loads(b"".join(app(environ, start_response)))
    return captured["status"], response


def test_default_monthly_grid_is_may_through_november():
    grid = generate_time_grid()
    assert [item.label for item in grid] == [f"2026-{month:02d}" for month in range(5, 12)]
    assert sum(item.duration_days for item in grid) == 214


def test_daily_grid_is_inclusive_and_deterministic():
    first = generate_time_grid("2026-06-01", "2026-06-03", "daily")
    second = generate_time_grid("2026-06-01", "2026-06-03", "daily")
    assert first == second
    assert [item.duration_hours for item in first] == [24.0, 24.0, 24.0]


def test_normalized_profile_scales_exactly_to_annual_target():
    profile = FeedProfile(
        "normalized", "Normalized", "monthly", True,
        (
            FeedProfilePoint("May", normalized_weight=1.0),
            FeedProfilePoint("June", normalized_weight=3.0),
        ),
        "test", "test",
    )
    rows = resolve_feed_profile(
        profile, generate_time_grid("2026-05-01", "2026-06-30", "monthly"), 4000.0
    )
    assert [item["available_wet_biomass_kg"] for item in rows] == [1000.0, 3000.0]
    assert sum(item["available_wet_biomass_kg"] for item in rows) == 4000.0


def test_monthly_profile_accepts_year_specific_period_keys():
    profile = FeedProfile(
        "dated", "Dated", "monthly", False,
        (FeedProfilePoint("2026-05", available_wet_biomass_kg=125.0),),
        "test", "test",
    )
    rows = resolve_feed_profile(
        profile, generate_time_grid("2026-05-01", "2027-05-31", "monthly"), None
    )
    assert rows[0]["available_wet_biomass_kg"] == 125.0
    assert rows[-1]["available_wet_biomass_kg"] == 0.0


def test_csv_and_zero_feed_periods_are_explicit(tmp_path):
    path = tmp_path / "daily.csv"
    path.write_text(
        "period,available_wet_biomass_kg,collection_fraction,source\n"
        "2026-06-01,0,0,user\n2026-06-02,100,1,user\n",
        encoding="utf-8",
    )
    profile = load_feed_profile_csv(path, "daily")
    rows = resolve_feed_profile(
        profile, generate_time_grid("2026-06-01", "2026-06-02", "daily"), None
    )
    assert rows[0]["available_wet_biomass_kg"] == 0.0
    assert rows[0]["collected_biomass_kg"] == 0.0
    assert rows[1]["collected_biomass_kg"] == 100.0


def test_inventory_conservation_overflow_age_and_initial_inventory():
    inventory = StorageInventory(
        total_mass_kg=50.0,
        component_masses_kg={"Water": 40.0, "Solids": 10.0},
        age_mass_kg_h=500.0,
        temperature_mass_kg_k=50.0 * 290.0,
    )
    overflow = inventory.receive(100.0, {"Water": 80.0, "Solids": 20.0}, 300.0, 120.0)
    withdrawn, components = inventory.withdraw(70.0)
    inventory.age(24.0)
    assert overflow == pytest.approx(30.0)
    assert withdrawn == pytest.approx(70.0)
    assert sum(components.values()) == pytest.approx(withdrawn)
    assert 50.0 + 100.0 == pytest.approx(overflow + withdrawn + inventory.total_mass_kg)
    assert inventory.average_age_h >= 24.0


def test_capacity_limit_unmet_demand_and_idle_capacity():
    result = capacity_limited_throughput(1000.0, 10.0, 80.0, 50.0)
    assert result["actual_mass_kg"] == 500.0
    assert result["unmet_demand_kg"] == 300.0
    assert result["idle_capacity_kg"] == 0.0
    idle = capacity_limited_throughput(100.0, 10.0, None, 50.0)
    assert idle["actual_mass_kg"] == 100.0
    assert idle["idle_capacity_kg"] == 400.0


def test_initial_inventory_contract_and_steady_state_compatibility():
    inventory = InitialStorageInventory(100.0, 0.8, {"Water": 0.8}, 290.0, 12.0)
    assert inventory.total_mass_kg == 100.0
    steady = SimulationRequest("1.0.0", "steady", "greenhub")
    assert SimulationService().validate_request(steady) == ()
    seasonal_fields = SimulationRequest(
        "1.0.0", "invalid", "greenhub", start_date="2026-05-01", end_date="2026-05-31"
    )
    assert any(item.code == "SEASONAL_FIELDS_REQUIRE_QUASI_DYNAMIC" for item in SimulationService().validate_request(seasonal_fields))


@pytest.mark.parametrize(
    "payload",
    (
        {"annual_biomass_target": float("nan")},
        {"operating_schedule": {"operating_hours_per_day": float("inf")}},
        {"initial_storage_inventory": {"total_mass_kg": float("nan")}},
    ),
)
def test_non_finite_seasonal_request_values_are_rejected(payload):
    base = {"schema_version": "1.0.0", "request_id": "finite", "project_id": "greenhub"}
    with pytest.raises(ValueError, match="finite"):
        SimulationRequest.from_dict({**base, **payload})


def test_profile_registries_do_not_leak_mutable_state():
    first = FeedProfileService()
    second = FeedProfileService()
    first.register(
        FeedProfile("private", "Private", "monthly", False, (FeedProfilePoint("May", available_wet_biomass_kg=1.0),), "test", "test")
    )
    assert any(item["profile_id"] == "private" for item in first.list_profiles())
    assert not any(item["profile_id"] == "private" for item in second.list_profiles())


def test_seasonal_api_serialization_overflow_and_mass_balance(tmp_path):
    app = create_app(tmp_path)
    profile_payload = {
        "profile_id": "api-june",
        "display_name": "API June",
        "resolution": "monthly",
        "normalized": True,
        "provenance": "test payload",
        "points": [{"period": "June", "normalized_weight": 1.0}],
    }
    status, profile = invoke(app, "POST", "/api/v1/feed-profiles", profile_payload)
    assert status == 201
    assert profile["profile_id"] == "api-june"
    request = {
        "schema_version": "1.0.0",
        "request_id": "seasonal-api",
        "project_id": "greenhub",
        "resolution_mode": "quasi_dynamic",
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "time_step": "monthly",
        "annual_biomass_target": 1000.0,
        "feed_supply_profile_id": "api-june",
        "operating_schedule": {"operating_days_per_week": 7, "operating_hours_per_day": 24},
        "design_overrides": [
            {"parameter_id": "seasonal.storage_capacity_kg", "value": 500.0, "unit": "kg"}
        ],
    }
    status, result = invoke(app, "POST", "/api/v1/simulations", request)
    assert status == 201
    summary = result["seasonal_summary"]
    assert summary["total_biomass_available_kg"] == 1000.0
    assert summary["total_overflow_kg"] == pytest.approx(500.0)
    assert summary["total_biomass_processed_kg"] == pytest.approx(500.0)
    assert summary["storage_mass_residual_kg"] == pytest.approx(0.0, abs=1e-9)
    assert result["storage_inventory_series"][0]["degradation_status"] == "not_implemented_no_eligible_data"
    assert result["capacity_utilization_series"]
    assert result["process_state_series"]
    rendered = json.dumps(result, allow_nan=False)
    assert not re.search(r"[A-Za-z]:[\\/]", rendered)
    run_id = result["run_id"]
    for resource in ("time-series", "inventory", "utilization", "seasonal-summary"):
        endpoint_status, payload = invoke(app, "GET", f"/api/v1/simulations/{run_id}/{resource}")
        assert endpoint_status == 200
        json.dumps(payload, allow_nan=False)
