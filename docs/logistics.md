# Logistics module (lightweight skeleton)

Added: Greenhub/logistics.py — a simple, additive logistics skeleton for biomass
collection and transport.

What it provides

- Data classes:
  - LogisticsScenario(total_biomass_kg, distance_km, notes)
  - VehicleSpec(payload_kg, fuel_consumption_l_per_100km, fuel_cost_per_l, fuel_emission_kg_co2_per_l)
  - LogisticsResult (delivered mass, trips, payload utilization, fuel use, cost, emissions,
    provenance, limitations)
- Function: simulate_logistics(scenario, vehicle) -> LogisticsResult

Simple calculation implemented

- trips = ceil(total_biomass_kg / payload_kg)
- distance_per_trip_km = 2 * distance_km (round trip)
- total_distance_km = trips * distance_per_trip_km
- fuel_used_l = total_distance_km * (fuel_consumption_l_per_100km / 100)
- transport_cost_currency = fuel_used_l * fuel_cost_per_l
- emissions_kg_co2 = fuel_used_l * fuel_emission_kg_co2_per_l
- payload_utilization = total_biomass_kg / (trips * payload_kg)

Provenance and limitations

- Each result contains a `provenance` dict echoing the inputs and listing explicit
  assumptions applied (no backhaul, perfect loading). Calculations are recorded.
- If any required input is missing or non-positive, the function does not invent a
  default value. Instead, it returns a result with `limitations` populated with
  keys like `missing:distance_km` or `nonpositive:payload_kg` and leaves numeric
  outputs as zero. This preserves scientific traceability and avoids hidden
  assumptions.

Limitations / what's missing

- No defaults or literature values are provided (distance, capacity, fuel intensity, fuel cost, and emission factors must be supplied by the caller).
- Optional non-fuel cost components are supported but strict: inputs must be supplied explicitly. The optional fields (on VehicleSpec) are:
  - fixed_cost_per_trip: flat cost applied per loaded trip (currency units)
  - driver_cost_per_hour: hourly driver wage (currency per hour)
  - average_speed_km_per_hour: average travel speed used to convert distance to hours (km/h)
  - loading_unloading_time_hr_per_trip: time per trip spent loading/unloading (hours)
  - maintenance_cost_per_km: maintenance cost per driven kilometer (currency per km)

  If optional inputs are missing or invalid, the calculation does not invent defaults; instead, the result includes `provenance["cost_notes"]` explaining which optional components were excluded or invalid.

- No consolidation, backhauls, multimodal, or routing optimization is performed.
- Not yet integrated into the seasonal controller or API. This is an additive helper for future integration.

Usage example

```python
from Greenhub.logistics import LogisticsScenario, VehicleSpec, simulate_logistics

scenario = LogisticsScenario(total_biomass_kg=1000.0, distance_km=10.0)
vehicle = VehicleSpec(payload_kg=500.0, fuel_consumption_l_per_100km=30.0, fuel_cost_per_l=1.5, fuel_emission_kg_co2_per_l=2.68)
result = simulate_logistics(scenario, vehicle)
print(result.to_dict())
```

Next steps for v1.0

- Add optional driver/cost parameters and a transport-cost-per-km candidate in the
  parameter registry so runs can resolve realistic costs with provenance.
- Add an integration path into the seasonal controller (opt-in) where available
  feed supply collection points and routing decisions can be mapped to trips.
- Expand to support consolidation, scheduling windows, and emissions accounting for
  other fuel types or electrified vehicles when validated data exist.

Monthly/batch helper

- simulate_monthly_logistics(monthly_biomass_kg, vehicle, distance_km_input=None, distance_km_by_month=None)
  - monthly_biomass_kg: mapping month->kg
  - vehicle: VehicleSpec
  - distance_km_input: single one-way distance applied to all months
  - distance_km_by_month: optional mapping per-month distances

The helper returns a dict containing per-month results, aggregated totals, and any limitations aggregated from months missing required inputs. Example usage:

```python
from Greenhub.logistics import create_simple_road_transport_scenario, create_demo_vehicle_spec, simulate_monthly_logistics

vehicle = create_demo_vehicle_spec()  # demo-only helper; values are illustrative and documented as such
monthly = {"January": 1000.0, "February": 0.0, "March": 500.0}
result = simulate_monthly_logistics(monthly, vehicle, distance_km_input=10.0)
print(result["totals"])
```

Notes

- The demo vehicle helper returns illustrative values: do not treat these as literature or project values.
- If a month lacks required inputs (e.g., missing distance or vehicle payload), that month records a limitation and its numeric contribution is excluded from aggregated totals.
