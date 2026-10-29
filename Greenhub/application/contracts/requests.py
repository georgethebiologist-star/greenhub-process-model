"""Versioned, transport-neutral simulation input contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from math import isfinite
from typing import Any, Mapping

from Greenhub.parameters.enums import CalculationMode, ResolutionMode
from Greenhub.parameters.overrides import ParameterOverride
from Greenhub.parameters.serialization import to_json_compatible

SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ScenarioSelection:
    feed_preparation: str = "F2"
    protein_recovery: str = "PR3"
    anaerobic_digestion: str = "AD1"
    biogas_upgrading: str = "BG2"
    nutrient_recovery: str = "NR4"
    process_order: str = "A"

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return (
            self.feed_preparation,
            self.protein_recovery,
            self.anaerobic_digestion,
            self.biogas_upgrading,
            self.nutrient_recovery,
        )


@dataclass(frozen=True)
class RequestedOutput:
    output_id: str
    detail_level: str = "summary"


@dataclass(frozen=True)
class RequestedPlot:
    plot_id: str
    formats: tuple[str, ...] = ("json", "csv", "png")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: str
    message: str
    blocking: bool
    process_area: str | None = None
    object_id: str | None = None
    field: str | None = None
    observed_value: object | None = None
    expected_condition: str | None = None


@dataclass(frozen=True)
class OperatingSchedule:
    """Explicit campaign schedule; omitted values use workbook monthly hours."""

    operating_days_per_week: float | None = None
    operating_hours_per_day: float | None = None
    target_throughput_kg_hr: float | None = None
    operating_dates: tuple[str, ...] = ()
    shutdown_dates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        numeric_values = (
            self.operating_days_per_week,
            self.operating_hours_per_day,
            self.target_throughput_kg_hr,
        )
        if any(value is not None and not isfinite(float(value)) for value in numeric_values):
            raise ValueError("Operating-schedule values must be finite or null.")
        if self.operating_days_per_week is not None and not 0.0 <= self.operating_days_per_week <= 7.0:
            raise ValueError("operating_days_per_week must be within [0, 7].")
        if self.operating_hours_per_day is not None and not 0.0 <= self.operating_hours_per_day <= 24.0:
            raise ValueError("operating_hours_per_day must be within [0, 24].")
        if self.target_throughput_kg_hr is not None and self.target_throughput_kg_hr < 0.0:
            raise ValueError("target_throughput_kg_hr must be non-negative.")
        for value in (*self.operating_dates, *self.shutdown_dates):
            date.fromisoformat(value)


@dataclass(frozen=True)
class BiomassSchedule:
    """Annual biomass availability and refinery plan shared with the proxy dashboard."""

    annual_available_biomass_tonnes: float = 30000.0
    annual_processed_biomass_tonnes: float = 30000.0
    collection_refinery_fraction: float = 1.0
    feed_basis: str = "tonnes_per_year"
    feed_kg_per_hr: float = 1000.0
    season_start: str = "2026-04-15"
    season_end: str = "2026-11-15"
    peak_date: str = "2026-07-31"
    spread_days: float = 55.0
    active_months: tuple[int, ...] = tuple(range(1, 13))
    source_id: str = "roadside_grass"
    location: str = "Netherlands"
    accessible_area_ha: float | None = None
    harvest_yield_tonnes_per_ha: float | None = None
    collection_efficiency: float = 1.0

    def __post_init__(self) -> None:
        numeric = (
            self.annual_available_biomass_tonnes,
            self.annual_processed_biomass_tonnes,
            self.collection_refinery_fraction,
            self.feed_kg_per_hr,
            self.spread_days,
        )
        if any(isinstance(value, bool) or not isfinite(float(value)) or value < 0.0 for value in numeric):
            raise ValueError("Biomass-schedule values must be finite non-negative numbers.")
        if self.collection_refinery_fraction > 1.0:
            raise ValueError("collection_refinery_fraction must be within [0, 1].")
        if self.feed_basis not in {"tonnes_per_year", "kg_per_hr"}:
            raise ValueError("feed_basis must be 'tonnes_per_year' or 'kg_per_hr'.")
        if not 1.0 <= self.spread_days <= 366.0:
            raise ValueError("spread_days must be between 1 and 366.")
        if (
            not isinstance(self.active_months, (tuple, list))
            or any(type(month) is not int or month not in range(1, 13) for month in self.active_months)
            or len(set(self.active_months)) != len(self.active_months)
        ):
            raise ValueError("active_months must contain unique month numbers from 1 to 12.")
        if not str(self.source_id).strip() or not str(self.location).strip():
            raise ValueError("Biomass source_id and location must be non-empty.")
        for value in (self.accessible_area_ha, self.harvest_yield_tonnes_per_ha):
            if value is not None and (isinstance(value, bool) or not isfinite(float(value)) or value < 0.0):
                raise ValueError("Accessible area and harvest yield must be finite non-negative numbers.")
        if not 0.0 <= self.collection_efficiency <= 1.0:
            raise ValueError("collection_efficiency must be within [0, 1].")
        try:
            start, end, peak = map(date.fromisoformat, (self.season_start, self.season_end, self.peak_date))
        except (TypeError, ValueError) as error:
            raise ValueError("Biomass schedule dates must use YYYY-MM-DD.") from error
        if start.year != end.year or end < start or peak.year != start.year or not start <= peak <= end:
            raise ValueError("Biomass season and peak dates must be ordered within one calendar year.")
        object.__setattr__(self, "active_months", tuple(sorted(self.active_months)))


@dataclass(frozen=True)
class InitialStorageInventory:
    """Initial wet inventory and optional measured composition metadata."""

    total_mass_kg: float = 0.0
    moisture_fraction: float | None = None
    component_mass_fractions: dict[str, float] = field(default_factory=dict)
    temperature_k: float | None = None
    storage_age_h: float = 0.0

    def __post_init__(self) -> None:
        numeric_values = (
            self.total_mass_kg,
            self.moisture_fraction,
            self.temperature_k,
            self.storage_age_h,
            *self.component_mass_fractions.values(),
        )
        if any(value is not None and not isfinite(float(value)) for value in numeric_values):
            raise ValueError("Initial inventory values must be finite or null.")
        if self.total_mass_kg < 0.0 or self.storage_age_h < 0.0:
            raise ValueError("Initial inventory mass and age must be non-negative.")
        if self.moisture_fraction is not None and not 0.0 <= self.moisture_fraction <= 1.0:
            raise ValueError("Initial inventory moisture_fraction must be within [0, 1].")
        if self.temperature_k is not None and self.temperature_k <= 0.0:
            raise ValueError("Initial inventory temperature_k must be greater than zero when supplied.")
        if any(value < 0.0 for value in self.component_mass_fractions.values()):
            raise ValueError("Initial inventory component fractions must be non-negative.")
        if sum(self.component_mass_fractions.values()) > 1.0 + 1e-12:
            raise ValueError("Initial inventory component fractions cannot sum above one.")


@dataclass(frozen=True)
class SimulationRequest:
    schema_version: str
    request_id: str
    project_id: str
    calculation_mode: CalculationMode = CalculationMode.STRUCTURAL
    resolution_mode: ResolutionMode = ResolutionMode.STEADY_STATE
    selected_month: str | None = "July"
    time_horizon: tuple[str, str] | None = None
    scenarios: ScenarioSelection = field(default_factory=ScenarioSelection)
    feed_overrides: tuple[ParameterOverride, ...] = ()
    operating_overrides: tuple[ParameterOverride, ...] = ()
    design_overrides: tuple[ParameterOverride, ...] = ()
    expert_scientific_overrides: tuple[ParameterOverride, ...] = ()
    requested_outputs: tuple[RequestedOutput, ...] = ()
    requested_plots: tuple[RequestedPlot, ...] = ()
    export_formats: tuple[str, ...] = ("json", "csv")
    strict_validation: bool = True
    user_notes: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    time_step: str | None = None
    annual_biomass_target: float | None = None
    operating_schedule: OperatingSchedule | None = None
    biomass_schedule: BiomassSchedule | None = None
    initial_storage_inventory: InitialStorageInventory = field(default_factory=InitialStorageInventory)
    feed_supply_profile_id: str | None = None
    wet_feed_rate_kg_hr: float | None = None
    plant_capacity_kg_hr: float | None = None
    feed_composition: dict[str, float] = field(default_factory=dict)
    storage_conditions: dict[str, object] | None = None

    def __post_init__(self) -> None:
        for name in ("wet_feed_rate_kg_hr", "plant_capacity_kg_hr"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isfinite(float(value)) or value <= 0):
                raise ValueError(f"{name} must be finite and greater than zero.")
        if self.feed_composition and (any(not isfinite(float(v)) or v < 0 for v in self.feed_composition.values()) or abs(sum(self.feed_composition.values())-1)>1e-8):
            raise ValueError("feed_composition must contain nonnegative wet mass fractions summing to one; overlapping fractions are not allowed.")
        if self.storage_conditions is not None:
            from Greenhub.storage import apply_storage_conditions
            apply_storage_conditions({}, self.storage_conditions)
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported SimulationRequest schema '{self.schema_version}'; expected '{SCHEMA_VERSION}'."
            )
        if not self.request_id or not self.project_id:
            raise ValueError("SimulationRequest requires request_id and project_id.")
        if self.time_horizon is not None and len(self.time_horizon) != 2:
            raise ValueError("time_horizon must contain exactly two values.")
        if not isinstance(self.strict_validation, bool):
            raise TypeError("strict_validation must be a boolean.")
        if self.time_step not in {None, "monthly", "daily"}:
            raise ValueError("time_step must be 'monthly', 'daily', or null.")
        if self.annual_biomass_target is not None:
            if not isfinite(float(self.annual_biomass_target)) or self.annual_biomass_target <= 0.0:
                raise ValueError("annual_biomass_target must be finite and greater than zero when supplied.")
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("start_date and end_date must be supplied together.")

    @property
    def all_overrides(self) -> tuple[ParameterOverride, ...]:
        return (
            *self.feed_overrides,
            *self.operating_overrides,
            *self.design_overrides,
            *self.expert_scientific_overrides,
        )

    def to_dict(self) -> dict[str, object]:
        return to_json_compatible(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SimulationRequest":
        allowed_fields = {
            "schema_version", "request_id", "project_id", "calculation_mode",
            "resolution_mode", "selected_month", "time_horizon", "scenarios",
            "feed_overrides", "operating_overrides", "design_overrides",
            "expert_scientific_overrides", "requested_outputs", "requested_plots",
            "export_formats", "strict_validation", "user_notes",
            "start_date", "end_date", "time_step", "annual_biomass_target",
            "operating_schedule", "biomass_schedule", "initial_storage_inventory", "feed_supply_profile_id",
            "wet_feed_rate_kg_hr", "plant_capacity_kg_hr", "feed_composition", "storage_conditions",
        }
        unknown_fields = sorted(set(payload) - allowed_fields)
        if unknown_fields:
            raise ValueError(f"Unknown SimulationRequest fields: {', '.join(unknown_fields)}.")
        for required in ("schema_version", "request_id", "project_id"):
            if not isinstance(payload.get(required), str) or not payload[required]:
                raise ValueError(f"SimulationRequest field '{required}' must be a non-empty string.")
        if "strict_validation" in payload and not isinstance(payload["strict_validation"], bool):
            raise TypeError("strict_validation must be a boolean.")
        scenario_payload = payload.get("scenarios") or {}
        scenarios = (
            scenario_payload
            if isinstance(scenario_payload, ScenarioSelection)
            else ScenarioSelection(**dict(scenario_payload))
        )
        schedule_payload = payload.get("operating_schedule")
        schedule = (
            schedule_payload
            if isinstance(schedule_payload, OperatingSchedule)
            else OperatingSchedule(
                operating_days_per_week=schedule_payload.get("operating_days_per_week"),
                operating_hours_per_day=schedule_payload.get("operating_hours_per_day"),
                target_throughput_kg_hr=schedule_payload.get("target_throughput_kg_hr"),
                operating_dates=tuple(schedule_payload.get("operating_dates", ())),
                shutdown_dates=tuple(schedule_payload.get("shutdown_dates", ())),
            ) if schedule_payload else None
        )
        biomass_payload = payload.get("biomass_schedule")
        biomass_schedule = (
            biomass_payload
            if isinstance(biomass_payload, BiomassSchedule)
            else BiomassSchedule(
                annual_available_biomass_tonnes=float(biomass_payload.get("annual_available_biomass_tonnes", 30000.0)),
                annual_processed_biomass_tonnes=float(biomass_payload.get("annual_processed_biomass_tonnes", 30000.0)),
                collection_refinery_fraction=float(biomass_payload.get("collection_refinery_fraction", 1.0)),
                feed_basis=str(biomass_payload.get("feed_basis", "tonnes_per_year")),
                feed_kg_per_hr=float(biomass_payload.get("feed_kg_per_hr", 1000.0)),
                season_start=str(biomass_payload.get("season_start", "2026-04-15")),
                season_end=str(biomass_payload.get("season_end", "2026-11-15")),
                peak_date=str(biomass_payload.get("peak_date", "2026-07-31")),
                spread_days=float(biomass_payload.get("spread_days", 55.0)),
                active_months=tuple(biomass_payload.get("active_months", range(1, 13))),
                source_id=str(biomass_payload.get("source_id", "roadside_grass")),
                location=str(biomass_payload.get("location", "Netherlands")),
                accessible_area_ha=(None if biomass_payload.get("accessible_area_ha") is None else float(biomass_payload["accessible_area_ha"])),
                harvest_yield_tonnes_per_ha=(None if biomass_payload.get("harvest_yield_tonnes_per_ha") is None else float(biomass_payload["harvest_yield_tonnes_per_ha"])),
                collection_efficiency=float(biomass_payload.get("collection_efficiency", 1.0)),
            ) if biomass_payload else None
        )
        inventory_payload = payload.get("initial_storage_inventory") or {}
        inventory = (
            inventory_payload
            if isinstance(inventory_payload, InitialStorageInventory)
            else InitialStorageInventory(
                total_mass_kg=float(inventory_payload.get("total_mass_kg", 0.0)),
                moisture_fraction=inventory_payload.get("moisture_fraction"),
                component_mass_fractions=dict(inventory_payload.get("component_mass_fractions", {})),
                temperature_k=inventory_payload.get("temperature_k"),
                storage_age_h=float(inventory_payload.get("storage_age_h", 0.0)),
            )
        )

        def overrides(name: str) -> tuple[ParameterOverride, ...]:
            values = payload.get(name) or ()
            return tuple(
                item if isinstance(item, ParameterOverride) else ParameterOverride(**dict(item))
                for item in values
            )

        return cls(
            schema_version=str(payload.get("schema_version", SCHEMA_VERSION)),
            request_id=str(payload.get("request_id", "")),
            project_id=str(payload.get("project_id", "")),
            calculation_mode=CalculationMode(payload.get("calculation_mode", "structural")),
            resolution_mode=ResolutionMode(payload.get("resolution_mode", "steady_state")),
            selected_month=payload.get("selected_month"),
            time_horizon=tuple(payload["time_horizon"]) if payload.get("time_horizon") else None,
            scenarios=scenarios,
            feed_overrides=overrides("feed_overrides"),
            operating_overrides=overrides("operating_overrides"),
            design_overrides=overrides("design_overrides"),
            expert_scientific_overrides=overrides("expert_scientific_overrides"),
            requested_outputs=tuple(
                item if isinstance(item, RequestedOutput) else RequestedOutput(**dict(item))
                for item in payload.get("requested_outputs", ())
            ),
            requested_plots=tuple(
                item if isinstance(item, RequestedPlot) else RequestedPlot(
                    plot_id=item["plot_id"], formats=tuple(item.get("formats", ("json", "csv", "png")))
                )
                for item in payload.get("requested_plots", ())
            ),
            export_formats=tuple(payload.get("export_formats", ("json", "csv"))),
            strict_validation=payload.get("strict_validation", True),
            user_notes=payload.get("user_notes"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            time_step=payload.get("time_step"),
            annual_biomass_target=payload.get("annual_biomass_target"),
            operating_schedule=schedule,
            biomass_schedule=biomass_schedule,
            initial_storage_inventory=inventory,
            feed_supply_profile_id=payload.get("feed_supply_profile_id"),
            wet_feed_rate_kg_hr=payload.get("wet_feed_rate_kg_hr"),
            plant_capacity_kg_hr=payload.get("plant_capacity_kg_hr"),
            feed_composition=dict(payload.get("feed_composition") or {}),
            storage_conditions=payload.get("storage_conditions"),
        )
