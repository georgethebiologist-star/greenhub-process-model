from types import SimpleNamespace

from Greenhub.logistics import LogisticsScenario, VehicleSpec, simulate_logistics, simulate_monthly_logistics


def test_logistics_missing_inputs_reports_limitations():
    scenario = LogisticsScenario(total_biomass_kg=None, distance_km=None)
    vehicle = VehicleSpec(payload_kg=None, fuel_consumption_l_per_100km=None, fuel_cost_per_l=None, fuel_emission_kg_co2_per_l=None)
    res = simulate_logistics(scenario, vehicle)
    assert res.limitations


def test_logistics_basic_calculation():
    scenario = LogisticsScenario(total_biomass_kg=1000.0, distance_km=10.0)
    vehicle = VehicleSpec(payload_kg=500.0, fuel_consumption_l_per_100km=30.0, fuel_cost_per_l=1.5, fuel_emission_kg_co2_per_l=2.68)
    res = simulate_logistics(scenario, vehicle)
    assert res.trips == 2
    assert res.delivered_biomass_kg == 1000.0
    assert res.payload_utilization == 1.0
    # fuel: trips=2 distance per trip 20km => total 40km; fuel 30 L/100km => 12 L
    assert abs(res.fuel_used_l - 12.0) < 1e-9
    assert abs(res.transport_cost_currency - (12.0 * 1.5)) < 1e-9
    assert abs(res.emissions_kg_co2 - (12.0 * 2.68)) < 1e-9


def test_simulate_monthly_logistics_aggregates_totals():
    vehicle = VehicleSpec(payload_kg=500.0, fuel_consumption_l_per_100km=30.0, fuel_cost_per_l=1.5, fuel_emission_kg_co2_per_l=2.68)
    monthly = {"January": 1000.0, "February": 0.0, "March": 500.0}
    out = simulate_monthly_logistics(monthly, vehicle, distance_km_input=10.0)
    totals = out["totals"]
    # delivered = 1000 + 0 + 500 = 1500
    assert totals["delivered_biomass_kg"] == 1500.0
    # trips: January 2, March 1 => 3
    assert totals["trips"] == 3
    # fuel: January trips=2 => 40km; March 1 => 20km total 60km; fuel 30L/100km => 18L
    assert abs(totals["fuel_used_l"] - 18.0) < 1e-9


def test_simulate_monthly_logistics_missing_distance_reports_limitations():
    vehicle = VehicleSpec(payload_kg=500.0, fuel_consumption_l_per_100km=30.0, fuel_cost_per_l=1.5, fuel_emission_kg_co2_per_l=2.68)
    monthly = {"January": 1000.0}
    out = simulate_monthly_logistics(monthly, vehicle, distance_km_input=None)
    assert out["limitations"]


def test_simulate_logistics_cost_breakdown_optional_components():
    scenario = LogisticsScenario(total_biomass_kg=1000.0, distance_km=10.0)
    vehicle = VehicleSpec(
        payload_kg=500.0,
        fuel_consumption_l_per_100km=30.0,
        fuel_cost_per_l=1.5,
        fuel_emission_kg_co2_per_l=2.68,
        fixed_cost_per_trip=10.0,
        driver_cost_per_hour=20.0,
        average_speed_km_per_hour=40.0,
        loading_unloading_time_hr_per_trip=0.25,
        maintenance_cost_per_km=0.1,
    )
    res = simulate_logistics(scenario, vehicle)
    cb = getattr(res, "cost_breakdown", {})
    # expected: fuel_cost 18.0, fixed 20.0, maintenance 4.0, driver 30.0 => total 72.0
    assert abs(cb["fuel_cost"] - 18.0) < 1e-9
    assert abs(cb["fixed_cost"] - 20.0) < 1e-9
    assert abs(cb["maintenance_cost"] - 4.0) < 1e-9
    assert abs(cb["driver_cost"] - 30.0) < 1e-9
    assert abs(res.transport_cost_currency - (18.0 + 20.0 + 4.0 + 30.0)) < 1e-9


def test_missing_optional_driver_avg_speed_provenance_note():
    scenario = LogisticsScenario(total_biomass_kg=1000.0, distance_km=10.0)
    vehicle = VehicleSpec(
        payload_kg=500.0,
        fuel_consumption_l_per_100km=30.0,
        fuel_cost_per_l=1.5,
        fuel_emission_kg_co2_per_l=2.68,
        driver_cost_per_hour=20.0,
        average_speed_km_per_hour=None,
    )
    res = simulate_logistics(scenario, vehicle)
    assert "driver_cost" not in getattr(res, "cost_breakdown", {})
    pn = res.provenance.get("cost_notes", [])
    assert any("average_speed_km_per_hour" in s for s in pn)
