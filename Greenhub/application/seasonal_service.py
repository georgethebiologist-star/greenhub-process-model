"""Quasi-dynamic seasonal controller around the existing integrated pathway."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from math import isfinite
from typing import Iterable

from Greenhub.integration import create_integrated_greenhub_system
from Greenhub.state_engine import build_state_outputs, state_from_stream
from Greenhub.storage_inventory import StorageInventory
from Greenhub.time_grid import TimeGridStep, generate_time_grid

from .contracts import InitialStorageInventory, OperatingSchedule, SimulationRequest
from .feed_profile_service import FeedProfileService
from .result_factory import build_balances, build_products, build_unit_results, build_utilities


@dataclass(frozen=True)
class SeasonalComputation:
    representative_model: object
    time_grid: tuple[dict[str, object], ...]
    feed_supply_series: tuple[dict[str, object], ...]
    storage_inventory_series: tuple[dict[str, object], ...]
    throughput_series: tuple[dict[str, object], ...]
    capacity_utilization_series: tuple[dict[str, object], ...]
    bottleneck_series: tuple[dict[str, object], ...]
    product_series: tuple[dict[str, object], ...]
    residual_series: tuple[dict[str, object], ...]
    utility_series: tuple[dict[str, object], ...]
    balance_residual_series: tuple[dict[str, object], ...]
    process_state_series: tuple[dict[str, object], ...]
    seasonal_summary: dict[str, object]
    warnings: tuple[str, ...]


_CAPACITY_PARAMETERS = {
    "phase3.cleaning_capacity_t_per_h": ("U101", "mass_t_h"),
    "phase3.pef_capacity_t_per_h": ("U201", "mass_t_h"),
    "phase3.press_capacity_t_per_h": ("S201", "mass_t_h"),
    "phase3.centrifuge_capacity_m3_per_h": ("C301", "volume_m3_h"),
    "phase4.protein_separator_capacity_m3_hr": ("C401", "volume_m3_h"),
    "phase4.protein_separator_solids_capacity_kg_hr": ("C401", "solids_kg_h"),
    "phase4.dewatering_capacity_kg_hr": ("D401", "mass_kg_h"),
    "phase4.dryer_capacity_kg_hr": ("DR401", "mass_kg_h"),
}


def calculate_operating_hours(
    step: TimeGridStep,
    schedule: OperatingSchedule | None,
    workbook_operating_days: float | None,
) -> float:
    """Resolve explicit hours or prorate the existing monthly workbook schedule."""

    if schedule is None:
        if workbook_operating_days is None:
            return 0.0
        start = date.fromisoformat(step.start_date)
        month_days = monthrange(start.year, start.month)[1]
        return float(workbook_operating_days * 24.0 * step.duration_days / month_days)
    start = date.fromisoformat(step.start_date)
    end = date.fromisoformat(step.end_date)
    shutdown = {date.fromisoformat(item) for item in schedule.shutdown_dates}
    explicit = {date.fromisoformat(item) for item in schedule.operating_dates}
    hours_per_day = schedule.operating_hours_per_day
    if hours_per_day is None:
        hours_per_day = 24.0
    if explicit:
        days = sum(1 for item in _dates(start, end) if item in explicit and item not in shutdown)
    else:
        days_per_week = schedule.operating_days_per_week
        if days_per_week is None:
            days_per_week = 7.0
        whole_days = int(days_per_week)
        fractional_day = days_per_week - whole_days
        days = sum(1.0 for item in _dates(start, end) if item.weekday() < whole_days and item not in shutdown)
        if fractional_day:
            days += sum(
                fractional_day
                for item in _dates(start, end)
                if item.weekday() == whole_days and item not in shutdown
            )
    return float(days * hours_per_day)


def capacity_limited_throughput(
    inventory_kg: float,
    operating_hours: float,
    target_throughput_kg_hr: float | None,
    raw_capacity_kg_hr: float | None,
) -> dict[str, float]:
    """Pure throughput decision used by the controller and boundary tests."""

    target_mass = inventory_kg if target_throughput_kg_hr is None else target_throughput_kg_hr * operating_hours
    capacity_mass = float("inf") if raw_capacity_kg_hr is None else raw_capacity_kg_hr * operating_hours
    actual = min(inventory_kg, target_mass, capacity_mass) if operating_hours > 0.0 else 0.0
    unmet = max(target_mass - actual, 0.0) if target_throughput_kg_hr is not None else 0.0
    return {
        "target_mass_kg": float(target_mass),
        "actual_mass_kg": float(actual),
        "unmet_demand_kg": float(unmet),
        "idle_capacity_kg": 0.0 if raw_capacity_kg_hr is None else max(capacity_mass - actual, 0.0),
    }


class SeasonalSimulationService:
    def __init__(self, profiles: FeedProfileService) -> None:
        self.profiles = profiles

    def run(
        self,
        request: SimulationRequest,
        resolved_parameters: Iterable[object],
        model_overrides: dict[str, object],
    ) -> SeasonalComputation:
        grid = generate_time_grid(request.start_date, request.end_date, request.time_step or "monthly")
        profile = self.profiles.get_profile(request.feed_supply_profile_id)
        from Greenhub.feed_profiles import resolve_feed_profile

        supply = list(resolve_feed_profile(profile, grid, request.annual_biomass_target))
        resolved = {item.parameter_id: item for item in resolved_parameters}
        storage_capacity = _resolved_number(resolved.get("seasonal.storage_capacity_kg"))
        warnings = list(profile.warnings)
        if storage_capacity is None:
            warnings.append(
                "Storage capacity is unavailable; inventory is preserved without an overflow limit until seasonal.storage_capacity_kg is overridden."
            )
        warnings.append(
            "Storage water loss, dry-matter loss, protein degradation, and COD degradation are not implemented because no eligible rates are available."
        )
        inventory = StorageInventory()
        initial_pending = request.initial_storage_inventory
        storage_rows = []
        throughput_rows = []
        utilization_rows = []
        bottleneck_rows = []
        product_rows = []
        residual_rows = []
        utility_rows = []
        balance_rows = []
        state_rows = []
        representative = None
        total_products: dict[str, float] = {}
        total_utilities = {"electricity_kwh": 0.0, "heating_kwh": 0.0, "cooling_kwh": 0.0}
        elemental_totals: dict[str, float] = {}
        utilization_totals: dict[str, list[float]] = {}

        for step, feed_row in zip(grid, supply):
            month = date.fromisoformat(step.start_date).strftime("%B")
            template = self._build_model(request, month, model_overrides)
            template_feed = template.streams["feed"]
            template_fractions = _stream_fractions(template_feed)
            supplied_fractions = _complete_fractions(
                template_fractions,
                feed_row["component_mass_fractions"],
                feed_row["moisture_fraction"],
            )
            feed_row["component_mass_fractions"] = supplied_fractions
            feed_row["moisture_fraction"] = supplied_fractions.get("Water")
            feed_row["dry_matter_kg"] = feed_row["available_wet_biomass_kg"] * (1.0 - supplied_fractions.get("Water", 0.0))
            if initial_pending is not None:
                self._initialize_inventory(inventory, initial_pending, template_fractions, template_feed.T)
                initial_pending = None
            entering = inventory.total_mass_kg
            received = float(feed_row["collected_biomass_kg"])
            received_components = {name: received * fraction for name, fraction in supplied_fractions.items()}
            overflow = inventory.receive(
                received,
                received_components,
                feed_row["temperature_k"] or float(template_feed.T),
                storage_capacity,
            )
            workbook_days = float(template.feed_specification.operating_days)
            operating_hours = calculate_operating_hours(step, request.operating_schedule, workbook_days)
            target_rate = request.operating_schedule.target_throughput_kg_hr if request.operating_schedule else None
            desired = capacity_limited_throughput(inventory.total_mass_kg, operating_hours, target_rate, None)
            desired_mass = desired["actual_mass_kg"]
            desired_rate = desired_mass / operating_hours if operating_hours > 0.0 else 0.0
            fractions = _inventory_fractions(inventory)
            temperature = inventory.temperature_k or float(template_feed.T)
            model = None
            capacity_records = ()
            raw_capacity = None
            if desired_rate > 0.0:
                model = template
                self._simulate_at_rate(model, desired_rate, fractions, temperature)
                capacity_records = self._capacity_records(model, resolved)
                raw_capacity = _raw_capacity_from_records(desired_rate, capacity_records)
                decision = capacity_limited_throughput(
                    inventory.total_mass_kg, operating_hours, target_rate, raw_capacity
                )
                actual_mass = decision["actual_mass_kg"]
                actual_rate = actual_mass / operating_hours if operating_hours > 0.0 else 0.0
                if actual_rate + 1e-9 < desired_rate:
                    model = self._build_model(request, month, model_overrides)
                    self._simulate_at_rate(model, actual_rate, fractions, temperature)
                    capacity_records = self._capacity_records(model, resolved)
            else:
                decision = capacity_limited_throughput(
                    inventory.total_mass_kg, operating_hours, target_rate, raw_capacity
                )
                actual_mass = actual_rate = 0.0
            withdrawn, withdrawn_components = inventory.withdraw(actual_mass)
            inventory.age(step.duration_hours)
            if model is not None:
                representative = model
            ending = inventory.total_mass_kg
            storage_residual = entering + received - overflow - withdrawn - ending
            storage_rows.append({
                "time": step.label, "inventory_entering_kg": entering, "biomass_received_kg": received,
                "biomass_withdrawn_kg": withdrawn, "inventory_remaining_kg": ending,
                "storage_age_h": inventory.average_age_h, "overflow_kg": overflow,
                "unmet_process_demand_kg": decision["unmet_demand_kg"], "water_loss_kg": 0.0,
                "dry_matter_loss_kg": 0.0, "degradation_status": "not_implemented_no_eligible_data",
                "storage_mass_residual_kg": storage_residual,
            })
            max_mass = None if raw_capacity is None else raw_capacity * operating_hours
            throughput_rows.append({
                "time": step.label, "available_operating_hours": operating_hours,
                "maximum_throughput_kg": max_mass, "actual_throughput_kg": withdrawn,
                "actual_throughput_kg_hr": actual_rate, "idle_capacity_kg": (
                    None if max_mass is None else max(max_mass - withdrawn, 0.0)
                ), "backlog_kg": ending, "rejected_or_overflow_kg": overflow,
            })
            step_bottleneck = _bottleneck(capacity_records)
            bottleneck_rows.append({"time": step.label, "bottleneck_unit": step_bottleneck})
            for item in capacity_records:
                row = {"time": step.label, **item}
                utilization_rows.append(row)
                utilization_totals.setdefault(item["unit_id"], []).append(item["utilization"])
            if model is None:
                product_rows.append({"time": step.label, "products_kg": {}})
                residual_rows.append({"time": step.label, "residual_output_kg": 0.0})
                utility_rows.append({"time": step.label, **{key: 0.0 for key in total_utilities}})
                balance_rows.append({"time": step.label, "overall_mass_residual_kg": 0.0, "element_residuals_kg": {}})
                state_rows.append({"time": step.label, "inlet": None, "outlets": (), "status": "zero_throughput"})
                continue
            products = {
                item.product_id: float(item.mass_flow.value or 0.0) * operating_hours
                for item in build_products(model)
            }
            for name, value in products.items():
                total_products[name] = total_products.get(name, 0.0) + value
            product_rows.append({"time": step.label, "products_kg": products})
            units = build_unit_results(model)
            utilities = build_utilities(units)
            electricity = sum(float(item.demand.value or 0.0) for item in utilities if item.kind == "electricity") * operating_hours
            heating_kj = sum(max(float(item.demand.value or 0.0), 0.0) for item in utilities if item.kind == "heat") * operating_hours
            cooling_kj = -sum(min(float(item.demand.value or 0.0), 0.0) for item in utilities if item.kind == "heat") * operating_hours
            utility = {"time": step.label, "electricity_kwh": electricity, "heating_kwh": heating_kj / 3600.0, "cooling_kwh": cooling_kj / 3600.0}
            utility_rows.append(utility)
            for key in total_utilities:
                total_utilities[key] += utility[key]
            balances = build_balances(model)
            overall = next(item for item in balances if item.balance_id == "overall_mass")
            element_residuals = {
                item.balance_id.removeprefix("element_"): float(item.residual.value or 0.0) * operating_hours
                for item in balances if item.balance_id.startswith("element_")
            }
            for name, value in element_residuals.items():
                elemental_totals[name] = elemental_totals.get(name, 0.0) + value
            overall_residual = float(overall.residual.value or 0.0) * operating_hours
            balance_rows.append({"time": step.label, "overall_mass_residual_kg": overall_residual, "element_residuals_kg": element_residuals})
            outlet_mass = float(overall.outlet.value or 0.0) * operating_hours
            residual_rows.append({"time": step.label, "residual_output_kg": max(outlet_mass - sum(products.values()), 0.0)})
            inlet_state = state_from_stream("seasonal_storage", model.streams["feed"]).to_dict()
            inlet_state["storage_age_h"] = storage_rows[-1]["storage_age_h"]
            states = build_state_outputs(model, resolved_parameters, request.resolution_mode.value)
            state_rows.append({"time": step.label, "inlet": inlet_state, "outlets": tuple(states["process_state_snapshots"]), "status": "calculated"})

        if representative is None:
            month = date.fromisoformat(grid[0].start_date).strftime("%B")
            representative = self._build_model(request, month, model_overrides)
            self._simulate_at_rate(representative, 0.0, _stream_fractions(representative.streams["feed"]), float(representative.streams["feed"].T))
        initial_mass = request.initial_storage_inventory.total_mass_kg
        collected = sum(float(item["collected_biomass_kg"]) for item in supply)
        processed = sum(float(item["actual_throughput_kg"]) for item in throughput_rows)
        overflow_total = sum(float(item["overflow_kg"]) for item in storage_rows)
        final_inventory = inventory.total_mass_kg
        summary = {
            "total_biomass_available_kg": sum(float(item["available_wet_biomass_kg"]) for item in supply),
            "total_biomass_collected_kg": collected,
            "total_biomass_processed_kg": processed,
            "total_biomass_uncollected_kg": sum(float(item["uncollected_biomass_kg"]) for item in supply),
            "total_overflow_kg": overflow_total,
            "final_inventory_kg": final_inventory,
            "average_inventory_kg": sum(float(item["inventory_remaining_kg"]) for item in storage_rows) / len(storage_rows),
            "peak_inventory_kg": max(float(item["inventory_remaining_kg"]) for item in storage_rows),
            "average_throughput_kg_hr": processed / sum(
                float(item["available_operating_hours"]) for item in throughput_rows
            ) if any(float(item["available_operating_hours"]) > 0.0 for item in throughput_rows) else 0.0,
            "peak_throughput_kg_hr": max(float(item["actual_throughput_kg_hr"]) for item in throughput_rows),
            "unit_utilization": {
                unit: {"average": sum(values) / len(values), "peak": max(values)}
                for unit, values in sorted(utilization_totals.items())
            },
            "total_products_kg": dict(sorted(total_products.items())),
            "total_utilities": total_utilities,
            "storage_mass_residual_kg": initial_mass + collected - processed - overflow_total - final_inventory,
            "process_mass_residual_kg": sum(float(item["overall_mass_residual_kg"]) for item in balance_rows),
            "element_residuals_kg": dict(sorted(elemental_totals.items())),
            "missing_data_warning_count": sum(len(item["warnings"]) for item in supply) + len(warnings),
        }
        return SeasonalComputation(
            representative, tuple(item.to_dict() for item in grid), tuple(supply), tuple(storage_rows),
            tuple(throughput_rows), tuple(utilization_rows), tuple(bottleneck_rows), tuple(product_rows),
            tuple(residual_rows), tuple(utility_rows), tuple(balance_rows), tuple(state_rows), summary,
            tuple(dict.fromkeys(warnings)),
        )

    @staticmethod
    def _build_model(request: SimulationRequest, month: str, model_overrides: dict[str, object]):
        selection = request.scenarios
        return create_integrated_greenhub_system(
            scenario_id=selection.nutrient_recovery,
            biogas_upgrading_scenario_id=selection.biogas_upgrading,
            anaerobic_digestion_scenario_id=selection.anaerobic_digestion,
            protein_recovery_scenario_id=selection.protein_recovery,
            feed_preparation_scenario_id=selection.feed_preparation,
            selected_month=month,
            process_order=selection.process_order,
            parameter_overrides=model_overrides or None,
        )

    @staticmethod
    def _simulate_at_rate(model, rate_kg_hr: float, fractions: dict[str, float], temperature_k: float) -> None:
        feed = model.streams["feed"]
        unknown = set(fractions) - set(feed.chemicals.IDs)
        if unknown:
            raise ValueError(f"Feed profile references unknown model components: {sorted(unknown)}")
        feed.empty()
        for name, fraction in fractions.items():
            feed.imass[name] = rate_kg_hr * fraction
        feed.T = temperature_k
        model.simulate()

    @staticmethod
    def _capacity_records(model, resolved: dict[str, object]) -> tuple[dict[str, object], ...]:
        records = []
        for parameter_id, (unit_id, basis) in _CAPACITY_PARAMETERS.items():
            capacity = _resolved_number(resolved.get(parameter_id))
            if capacity is None or unit_id not in model.units:
                continue
            unit = model.units[unit_id]
            inlet = unit.ins[0]
            if basis == "mass_t_h":
                actual, maximum, unit_name = float(inlet.F_mass), capacity * 1000.0, "kg/hr"
            elif basis == "mass_kg_h":
                actual, maximum, unit_name = float(inlet.F_mass), capacity, "kg/hr"
            elif basis == "volume_m3_h":
                actual, maximum, unit_name = float(inlet.F_vol), capacity, "m3/hr"
            else:
                water = float(inlet.imass["Water"]) if "Water" in inlet.chemicals.IDs else 0.0
                actual, maximum, unit_name = max(float(inlet.F_mass) - water, 0.0), capacity, "kg/hr"
            utilization = actual / maximum if maximum > 0.0 else 0.0
            records.append({
                "unit_id": unit_id, "parameter_id": parameter_id, "basis": basis,
                "actual_load": actual, "maximum_load": maximum, "unit": unit_name,
                "utilization": utilization,
            })
        return tuple(records)

    @staticmethod
    def _initialize_inventory(
        inventory: StorageInventory,
        initial: InitialStorageInventory,
        template_fractions: dict[str, float],
        template_temperature: float,
    ) -> None:
        if initial.total_mass_kg <= 0.0:
            return
        fractions = _complete_fractions(
            template_fractions, initial.component_mass_fractions, initial.moisture_fraction
        )
        inventory.receive(
            initial.total_mass_kg,
            {name: initial.total_mass_kg * fraction for name, fraction in fractions.items()},
            initial.temperature_k or float(template_temperature),
            None,
        )
        inventory.age_mass_kg_h = initial.total_mass_kg * initial.storage_age_h


def _dates(start: date, end: date):
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def _resolved_number(item: object | None) -> float | None:
    if item is None or getattr(item, "blocked", True) or getattr(item, "active_value", None) is None:
        return None
    value = float(item.active_value)
    return value if isfinite(value) and value > 0.0 else None


def _stream_fractions(stream) -> dict[str, float]:
    total = float(stream.F_mass)
    if total <= 0.0:
        raise ValueError("Workbook feed template has zero mass and cannot define composition.")
    return {
        name: float(stream.imass[name]) / total
        for name in stream.chemicals.IDs
        if float(stream.imass[name]) > 0.0
    }


def _complete_fractions(
    template: dict[str, float], supplied: dict[str, float], moisture_fraction: float | None,
) -> dict[str, float]:
    explicit = dict(supplied)
    if moisture_fraction is not None and "Water" not in explicit:
        explicit["Water"] = float(moisture_fraction)
    explicit_total = sum(explicit.values())
    if explicit_total > 1.0 + 1e-12:
        raise ValueError("Supplied feed component fractions exceed one.")
    remaining = max(1.0 - explicit_total, 0.0)
    candidates = {name: value for name, value in template.items() if name not in explicit}
    candidate_total = sum(candidates.values())
    if remaining > 1e-12 and candidate_total <= 0.0:
        raise ValueError("Incomplete feed fractions cannot be reconciled to the workbook composition.")
    completed = dict(explicit)
    for name, value in candidates.items():
        completed[name] = remaining * value / candidate_total
    total = sum(completed.values())
    return {name: value / total for name, value in completed.items() if value > 0.0}


def _inventory_fractions(inventory: StorageInventory) -> dict[str, float]:
    if inventory.total_mass_kg <= 0.0:
        return {}
    return {name: value / inventory.total_mass_kg for name, value in inventory.component_masses_kg.items()}


def _raw_capacity_from_records(raw_rate: float, records: tuple[dict[str, object], ...]) -> float | None:
    equivalents = []
    for item in records:
        utilization = float(item["utilization"])
        if utilization > 0.0:
            equivalents.append(raw_rate / utilization)
    return min(equivalents) if equivalents else None


def _bottleneck(records: tuple[dict[str, object], ...]) -> str | None:
    active = [item for item in records if float(item["actual_load"]) > 0.0]
    return max(active, key=lambda item: float(item["utilization"]))["unit_id"] if active else None
