"""
Lightweight logistics module for biomass collection and transport.

Design goals:
- Additive skeleton that performs transparent, traceable calculations for simple
  collection/transport tasks.
- No defaults invented for distance, payload, fuel intensity, cost, or emission
  factors. If required values are missing, the result reports limitations instead
  of producing silently-assumed numbers.
- Each result contains provenance and explicit limitations to preserve
  scientific traceability.

This module intentionally stays small and does not integrate with the seasonal
controller by itself. It is a reusable helper for future integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from math import ceil
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class VehicleSpec:
    """Specification of a transport vehicle.

    Fields that are required for calculations must be provided by the caller.
    - payload_kg: useful cargo mass per trip (kg)
    - fuel_consumption_l_per_100km: fuel consumption in liters per 100 km
    - fuel_cost_per_l: currency per liter (for diesel cost calculation)
    - fuel_emission_kg_co2_per_l: emission factor kg CO2 per liter of fuel
    """

    payload_kg: Optional[float] = None
    fuel_consumption_l_per_100km: Optional[float] = None
    fuel_cost_per_l: Optional[float] = None
    fuel_emission_kg_co2_per_l: Optional[float] = None

    # Optional non-fuel cost components (strict: no defaults invented)
    fixed_cost_per_trip: Optional[float] = None
    driver_cost_per_hour: Optional[float] = None
    average_speed_km_per_hour: Optional[float] = None
    loading_unloading_time_hr_per_trip: Optional[float] = None
    maintenance_cost_per_km: Optional[float] = None


@dataclass(frozen=True)
class LogisticsScenario:
    """Inputs describing the collection scenario.

    - total_biomass_kg: total wet biomass mass to collect (kg)
    - distance_km: one-way distance between collection and processing site (km)
    - notes: optional free-text notes or identifier
    """

    total_biomass_kg: Optional[float] = None
    distance_km: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class LogisticsResult:
    delivered_biomass_kg: float = 0.0
    trips: int = 0
    payload_utilization: float = 0.0
    fuel_used_l: float = 0.0
    transport_cost_currency: float = 0.0
    emissions_kg_co2: float = 0.0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def simulate_logistics(scenario: LogisticsScenario, vehicle: VehicleSpec) -> LogisticsResult:
    """Run a lightweight logistics calculation.

    Behavior and required inputs:
    - Requires scenario.total_biomass_kg, scenario.distance_km, vehicle.payload_kg,
      vehicle.fuel_consumption_l_per_100km, vehicle.fuel_cost_per_l,
      vehicle.fuel_emission_kg_co2_per_l to perform full calculations.
    - If any required value is missing or non-positive, return a LogisticsResult with
      `limitations` populated and numeric outputs set to zero.

    Returned fields:
    - delivered_biomass_kg: biomass mass accounted as delivered (kg) — equals requested
      mass when calculations succeed.
    - trips: integer number of trips required (ceiling of mass / payload)
    - payload_utilization: fraction of payload used on average (0-1)
    - fuel_used_l: total diesel liters consumed
    - transport_cost_currency: total fuel cost (currency units) — only fuel cost is included
      in this lightweight skeleton; additional cost elements (driver, maintenance) are not included
      unless supplied by future extensions.
    - emissions_kg_co2: kg CO2 equivalent emitted from fuel combustion
    - provenance: dict listing inputs used and assumptions applied
    - limitations: list of limitation keys/messages when inputs are missing
    """

    res = LogisticsResult()
    provenance: Dict[str, Any] = {"inputs": {}, "assumptions": []}
    limitations: List[str] = []

    # Validate required inputs
    tb = scenario.total_biomass_kg
    dist = scenario.distance_km
    payload = vehicle.payload_kg
    fuel_cons = vehicle.fuel_consumption_l_per_100km
    fuel_cost = vehicle.fuel_cost_per_l
    fuel_emission = vehicle.fuel_emission_kg_co2_per_l

    provenance["inputs"]["scenario"] = {
        "total_biomass_kg": tb,
        "distance_km_one_way": dist,
        "notes": scenario.notes,
    }
    provenance["inputs"]["vehicle"] = {
        "payload_kg": payload,
        "fuel_consumption_l_per_100km": fuel_cons,
        "fuel_cost_per_l": fuel_cost,
        "fuel_emission_kg_co2_per_l": fuel_emission,
    }

    # Check for missing or invalid numeric values
    def _missing(name: str, value: Optional[float]):
        if value is None:
            limitations.append(f"missing:{name}")
            return True
        try:
            v = float(value)
        except Exception:
            limitations.append(f"invalid:{name}")
            return True
        if v <= 0.0:
            limitations.append(f"nonpositive:{name}")
            return True
        return False

    reqs = [
        ("total_biomass_kg", tb),
        ("distance_km", dist),
        ("payload_kg", payload),
        ("fuel_consumption_l_per_100km", fuel_cons),
        ("fuel_cost_per_l", fuel_cost),
        ("fuel_emission_kg_co2_per_l", fuel_emission),
    ]

    for name, val in reqs:
        _missing(name, val)

    if limitations:
        res.limitations = limitations
        res.provenance = provenance
        provenance["assumptions"].append("calculation_skipped_due_to_missing_inputs")
        return res

    # All required inputs are present and positive; run calculations
    total_biomass = float(tb)
    distance_one_way = float(dist)
    payload_kg = float(payload)
    fuel_l_per_100km = float(fuel_cons)
    fuel_cost_l = float(fuel_cost)
    emission_kg_per_l = float(fuel_emission)

    # number of trips (ceiling). A trip is one loaded delivery (one-way) with return to collect next load.
    trips = int(ceil(total_biomass / payload_kg)) if total_biomass > 0 else 0

    # total distance: round trip per trip
    distance_per_trip_km = 2.0 * distance_one_way
    total_distance_km = trips * distance_per_trip_km

    # fuel used (liters) = total_distance_km * (fuel_l_per_100km / 100)
    fuel_used_l = total_distance_km * (fuel_l_per_100km / 100.0)

    # transport cost (currency) = fuel_used_l * fuel_cost_l
    transport_cost = fuel_used_l * fuel_cost_l

    # emissions
    emissions_kg_co2 = fuel_used_l * emission_kg_per_l

    # payload utilization average (mass / (trips * payload))
    payload_util = total_biomass / (trips * payload_kg) if trips > 0 else 0.0

    # Fill result
    res.delivered_biomass_kg = total_biomass
    res.trips = trips
    res.payload_utilization = payload_util
    res.fuel_used_l = fuel_used_l
    res.emissions_kg_co2 = emissions_kg_co2

    # Build cost breakdown (fuel cost always present here)
    cost_breakdown: Dict[str, float] = {}
    cost_breakdown["fuel_cost"] = transport_cost

    # Optional costs: fixed per trip
    fixed_cost = None
    if vehicle.fixed_cost_per_trip is not None:
        try:
            fixed_cost = float(vehicle.fixed_cost_per_trip)
            if fixed_cost < 0:
                provenance.setdefault("cost_notes", []).append("nonpositive:fixed_cost_per_trip_ignored")
                fixed_cost = None
            else:
                cost_breakdown["fixed_cost"] = fixed_cost * trips
        except Exception:
            provenance.setdefault("cost_notes", []).append("invalid:fixed_cost_per_trip")
            fixed_cost = None

    # Maintenance cost (per km)
    maintenance_cost = None
    if vehicle.maintenance_cost_per_km is not None:
        try:
            maintenance_cost = float(vehicle.maintenance_cost_per_km)
            if maintenance_cost < 0:
                provenance.setdefault("cost_notes", []).append("nonpositive:maintenance_cost_per_km_ignored")
                maintenance_cost = None
            else:
                cost_breakdown["maintenance_cost"] = maintenance_cost * total_distance_km
        except Exception:
            provenance.setdefault("cost_notes", []).append("invalid:maintenance_cost_per_km")
            maintenance_cost = None

    # Driver cost: requires driver_cost_per_hour and average_speed_km_per_hour
    driver_cost = None
    if vehicle.driver_cost_per_hour is not None and vehicle.average_speed_km_per_hour is None:
        provenance.setdefault("cost_notes", []).append("missing:average_speed_km_per_hour_driver_cost_not_computed")
    if vehicle.driver_cost_per_hour is not None and vehicle.average_speed_km_per_hour is not None:
        try:
            drv_rate = float(vehicle.driver_cost_per_hour)
            avg_speed = float(vehicle.average_speed_km_per_hour)
            if drv_rate < 0 or avg_speed <= 0:
                provenance.setdefault("cost_notes", []).append("invalid:driver_rate_or_avg_speed")
            else:
                travel_hours = total_distance_km / avg_speed
                loading_time_total = 0.0
                if vehicle.loading_unloading_time_hr_per_trip is not None:
                    try:
                        loading_time_total = float(vehicle.loading_unloading_time_hr_per_trip) * trips
                        if loading_time_total < 0:
                            provenance.setdefault("cost_notes", []).append("nonpositive:loading_unloading_time_hr_per_trip_ignored")
                            loading_time_total = 0.0
                    except Exception:
                        provenance.setdefault("cost_notes", []).append("invalid:loading_unloading_time_hr_per_trip")
                        loading_time_total = 0.0
                else:
                    provenance.setdefault("cost_notes", []).append("missing:loading_unloading_time_hr_per_trip_excluded_from_driver_cost")
                driver_hours = travel_hours + loading_time_total
                driver_cost = drv_rate * driver_hours
                cost_breakdown["driver_cost"] = driver_cost
        except Exception:
            provenance.setdefault("cost_notes", []).append("invalid:driver_cost_or_avg_speed")

    # Sum total transport cost (fuel + optional components)
    total_cost = sum(cost_breakdown.values())

    res.transport_cost_currency = total_cost
    res.cost_breakdown = cost_breakdown

    provenance["assumptions"].append("no_backhaul_or_consolidation")
    provenance["assumptions"].append("perfect_loading_efficiency")
    provenance["calculations"] = {
        "distance_per_trip_km": distance_per_trip_km,
        "total_distance_km": total_distance_km,
        "fuel_used_l": fuel_used_l,
        "fuel_cost": cost_breakdown.get("fuel_cost", 0.0),
        "cost_breakdown": cost_breakdown,
        "emissions_kg_co2": emissions_kg_co2,
    }
    res.provenance = provenance
    res.limitations = []
    return res


# --- Convenience builders and monthly helper ---

def create_simple_road_transport_scenario(total_biomass_kg: float, distance_km: float, notes: Optional[str] = None) -> LogisticsScenario:
    """Create a simple LogisticsScenario. Does not invent values; caller must provide explicit numbers.

    This builder is just a small convenience to create a LogisticsScenario with required fields.
    """
    return LogisticsScenario(total_biomass_kg=total_biomass_kg, distance_km=distance_km, notes=notes)


def create_demo_vehicle_spec() -> VehicleSpec:
    """Return a demo VehicleSpec populated with example values.

    This is explicitly a demo helper. Values are illustrative only and should NOT be used
    in production runs without replacement by validated project or literature values.
    Callers using this function should acknowledge demo assumptions.
    """
    return VehicleSpec(payload_kg=500.0, fuel_consumption_l_per_100km=30.0, fuel_cost_per_l=1.5, fuel_emission_kg_co2_per_l=2.68)


def simulate_monthly_logistics(monthly_biomass_kg: dict[str, Optional[float]], vehicle: VehicleSpec, distance_km_input: Optional[float] = None, distance_km_by_month: Optional[dict[str, float]] = None) -> dict:
    """Simulate logistics on a per-month basis and aggregate annual totals.

    Inputs:
    - monthly_biomass_kg: mapping of month name (e.g., 'January') to biomass kg (may be None for months with no data).
    - vehicle: VehicleSpec instance (must contain required values or monthly results will report limitations).
    - distance_km_input: single one-way distance to apply to all months (optional if distance_km_by_month provided).
    - distance_km_by_month: optional mapping month->distance_km to vary distances.

    Returns a dict with keys:
    - monthly: mapping month -> LogisticsResult (as dict)
    - totals: aggregated annual totals (delivered_biomass_kg, trips, fuel_used_l, transport_cost_currency, emissions_kg_co2)
    - limitations: sorted list of unique limitation messages across months

    Note: function will not invent missing distances. If both distance_km_input and distance_km_by_month are None, months will record missing:distance_km limitation.
    """
    monthly_results: dict[str, dict] = {}
    totals = {
        "delivered_biomass_kg": 0.0,
        "trips": 0,
        "fuel_used_l": 0.0,
        "transport_cost_currency": 0.0,
        "emissions_kg_co2": 0.0,
        # aggregated optional breakdowns (populated as months provide them)
        "cost_breakdown": {},
    }
    limitations_set = set()

    for month, mass in monthly_biomass_kg.items():
        # determine distance for this month
        if distance_km_by_month and month in distance_km_by_month:
            dist = distance_km_by_month[month]
        else:
            dist = distance_km_input
        scenario = LogisticsScenario(total_biomass_kg=mass, distance_km=dist, notes=f"month:{month}")
        result = simulate_logistics(scenario, vehicle)
        monthly_results[month] = result.to_dict()
        # aggregate only if no limitations for that month
        if not result.limitations:
            totals["delivered_biomass_kg"] += result.delivered_biomass_kg
            totals["trips"] += result.trips
            totals["fuel_used_l"] += result.fuel_used_l
            totals["transport_cost_currency"] += result.transport_cost_currency
            totals["emissions_kg_co2"] += result.emissions_kg_co2
            # aggregate optional cost breakdowns when present
            cb = getattr(result, "cost_breakdown", None)
            if cb:
                for k, v in cb.items():
                    totals["cost_breakdown"][k] = totals["cost_breakdown"].get(k, 0.0) + float(v)
        else:
            for lim in result.limitations:
                limitations_set.add(f"{month}:{lim}")

    return {"monthly": monthly_results, "totals": totals, "limitations": sorted(limitation for limitation in limitations_set)}
