"""Versioned, transport-neutral simulation input contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import json
from functools import lru_cache
from math import isfinite
from pathlib import Path
from typing import Any, Mapping

from Greenhub.parameters.enums import CalculationMode, ResolutionMode
from Greenhub.parameters.overrides import ParameterOverride
from Greenhub.parameters.serialization import to_json_compatible

SCHEMA_VERSION = "1.0.0"


@lru_cache(maxsize=1)
def _feed_composition_profile() -> dict[str, object]:
    """Load the canonical feed profile shared with the frontend reset form."""
    profile_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "Pre-treatment"
        / "Feedstock"
        / "greenhub_feed_composition_defaults.json"
    )
    with profile_path.open(encoding="utf-8") as source:
        return json.load(source)


_FEED_PROFILE = _feed_composition_profile()
_FEED_COMPOSITION_LIMITS = _FEED_PROFILE["composition_limits"]
FEED_COMPOSITION_MIN_TOTAL = float(_FEED_COMPOSITION_LIMITS["minimum_total_fraction"])
FEED_COMPOSITION_MAX_TOTAL = float(_FEED_COMPOSITION_LIMITS["maximum_total_fraction"])
FEED_COMPOSITION_NORMALIZED_TOTAL = float(_FEED_COMPOSITION_LIMITS["normalized_total_fraction"])


def _default_feed_composition() -> dict[str, float]:
    """Return fresh wet-basis fractions from the canonical feed profile."""
    return {
        component_id: float(record["wet_mass_fraction"])
        for component_id, record in _FEED_PROFILE["compounds"].items()
    }


@dataclass(frozen=True)
class ScenarioSelection:
    feed_preparation: str = "F1"
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
    processing_delay_days: int = 14
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
        if type(self.processing_delay_days) is not int or not 0 <= self.processing_delay_days <= 365:
            raise ValueError("processing_delay_days must be an integer from 0 to 365.")
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
class BiostimulantRouteOptions:
    """Explicit PR7 membrane and evidence selections for steady-state or seasonal runs."""

    technology_id: str
    retention_matrix_source: str
    flux_L_m2_h: float | None = None
    flux_source: str | None = None
    component_retention_overrides: dict[str, float] = field(default_factory=dict)
    component_retention_override_sources: dict[str, str] = field(default_factory=dict)
    feed_to_reference_concentration_ratio: float | None = None
    flux_model_source: str | None = None
    viscosity_Pa_s: float | None = None
    viscosity_source: str | None = None
    transmembrane_pressure_bar: float | None = None
    pressure_source: str | None = None
    pump_efficiency_fraction: float | None = None
    pump_efficiency_source: str | None = None
    crossflow_electricity_kwh_m3_feed: float | None = None
    crossflow_electricity_source: str | None = None
    use_hormone_benchmarks: bool = False
    hormone_benchmark_source: str | None = None
    cip_solution_volume_L_per_step: float | None = None
    cip_makeup_fraction_per_cycle: float | None = None
    cip_input_source: str | None = None

    def __post_init__(self) -> None:
        technology = str(self.technology_id).strip().upper()
        if technology not in {"TUF", "LNF", "MEUF"}:
            raise ValueError("PR7 technology_id must be TUF, LNF, or MEUF.")
        object.__setattr__(self, "technology_id", technology)
        if not isinstance(self.retention_matrix_source, str) or not self.retention_matrix_source.strip():
            raise ValueError("PR7 retention_matrix_source is required as an evidence note.")
        if self.flux_L_m2_h is not None:
            if not isfinite(float(self.flux_L_m2_h)) or self.flux_L_m2_h <= 0.0:
                raise ValueError("PR7 flux_L_m2_h must be finite and positive.")
            if not isinstance(self.flux_source, str) or not self.flux_source.strip():
                raise ValueError("PR7 empirical flux requires a non-empty flux_source evidence note.")
        elif self.flux_source is not None:
            raise ValueError("PR7 flux_source can only be supplied with an explicit flux_L_m2_h.")
        if self.feed_to_reference_concentration_ratio is not None:
            if self.flux_L_m2_h is not None:
                raise ValueError("PR7 must select either empirical flux or resistance-model flux, not both.")
            if not isfinite(float(self.feed_to_reference_concentration_ratio)) or self.feed_to_reference_concentration_ratio <= 0.0:
                raise ValueError("PR7 feed_to_reference_concentration_ratio must be finite and positive.")
            if not isinstance(self.flux_model_source, str) or not self.flux_model_source.strip():
                raise ValueError("PR7 resistance-model concentration ratio requires a flux_model_source evidence note.")
            if self.transmembrane_pressure_bar is None:
                raise ValueError("PR7 resistance-model flux requires transmembrane_pressure_bar.")
            if self.viscosity_Pa_s is None or not isfinite(float(self.viscosity_Pa_s)) or self.viscosity_Pa_s <= 0.0:
                raise ValueError("PR7 no-fermentation resistance-model flux requires a positive measured viscosity_Pa_s.")
            if not isinstance(self.viscosity_source, str) or not self.viscosity_source.strip():
                raise ValueError("PR7 viscosity_Pa_s requires a viscosity_source evidence note.")
        elif self.flux_model_source is not None:
            raise ValueError("PR7 flux_model_source requires feed_to_reference_concentration_ratio.")
        elif self.viscosity_Pa_s is not None or self.viscosity_source is not None:
            raise ValueError("PR7 viscosity inputs are only accepted with the resistance-model flux method.")
        if self.flux_L_m2_h is None and self.feed_to_reference_concentration_ratio is None:
            raise ValueError("PR7 requires either an empirical flux or pressure and Cf/C0 for the resistance model.")
        if self.transmembrane_pressure_bar is not None:
            if not isfinite(float(self.transmembrane_pressure_bar)) or self.transmembrane_pressure_bar <= 0.0:
                raise ValueError("PR7 transmembrane_pressure_bar must be finite and positive.")
            if not isinstance(self.pressure_source, str) or not self.pressure_source.strip():
                raise ValueError("PR7 transmembrane_pressure_bar requires a pressure_source evidence note.")
        elif self.pressure_source is not None:
            raise ValueError("PR7 pressure_source requires transmembrane_pressure_bar.")
        if self.pump_efficiency_fraction is not None:
            if self.transmembrane_pressure_bar is None:
                raise ValueError("PR7 pump efficiency requires transmembrane_pressure_bar.")
            if not isfinite(float(self.pump_efficiency_fraction)) or not 0.0 < self.pump_efficiency_fraction <= 1.0:
                raise ValueError("PR7 pump_efficiency_fraction must be in (0, 1].")
            if not isinstance(self.pump_efficiency_source, str) or not self.pump_efficiency_source.strip():
                raise ValueError("PR7 pump_efficiency_fraction requires a pump_efficiency_source note.")
        elif self.pump_efficiency_source is not None:
            raise ValueError("PR7 pump_efficiency_source requires pump_efficiency_fraction.")
        if self.crossflow_electricity_kwh_m3_feed is not None:
            if (
                not isfinite(float(self.crossflow_electricity_kwh_m3_feed))
                or float(self.crossflow_electricity_kwh_m3_feed) < 0.0
            ):
                raise ValueError("PR7 crossflow electricity must be finite and non-negative.")
            if not isinstance(self.crossflow_electricity_source, str) or not self.crossflow_electricity_source.strip():
                raise ValueError("PR7 crossflow electricity requires a source/evidence note.")
        elif self.crossflow_electricity_source is not None:
            raise ValueError("PR7 crossflow electricity source requires a crossflow electricity value.")
        if not isinstance(self.use_hormone_benchmarks, bool):
            raise TypeError("PR7 use_hormone_benchmarks must be boolean.")
        if self.use_hormone_benchmarks:
            if not isinstance(self.hormone_benchmark_source, str) or not self.hormone_benchmark_source.strip():
                raise ValueError("PR7 benchmark hormone feed requires a hormone_benchmark_source evidence note.")
        elif self.hormone_benchmark_source is not None:
            raise ValueError("PR7 hormone_benchmark_source requires use_hormone_benchmarks=true.")
        cip_values = (self.cip_solution_volume_L_per_step, self.cip_makeup_fraction_per_cycle)
        if any(value is not None for value in cip_values):
            if any(value is None for value in cip_values):
                raise ValueError("PR7 CIP volume and make-up fraction must be supplied together.")
            if not isfinite(float(self.cip_solution_volume_L_per_step)) or self.cip_solution_volume_L_per_step <= 0.0:
                raise ValueError("PR7 CIP solution volume per step must be finite and positive.")
            if not isfinite(float(self.cip_makeup_fraction_per_cycle)) or not 0.0 <= self.cip_makeup_fraction_per_cycle <= 1.0:
                raise ValueError("PR7 CIP make-up fraction per cycle must be in [0, 1].")
            if not isinstance(self.cip_input_source, str) or not self.cip_input_source.strip():
                raise ValueError("PR7 CIP volume and make-up fraction require a source/evidence note.")
        elif self.cip_input_source is not None:
            raise ValueError("PR7 cip_input_source requires both CIP volume and make-up fraction.")
        if set(self.component_retention_overrides) != set(self.component_retention_override_sources):
            raise ValueError("Every PR7 component retention override requires exactly one matching source note.")
        for component_id, value in self.component_retention_overrides.items():
            if not isinstance(component_id, str) or not component_id.strip():
                raise ValueError("PR7 component retention override IDs must be non-empty strings.")
            if isinstance(value, bool) or not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"PR7 retention override for {component_id} must be in [0, 1].")
            source = self.component_retention_override_sources[component_id]
            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"PR7 retention override for {component_id} requires a source note.")

    def to_dict(self) -> dict[str, object]:
        return to_json_compatible(self)


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
    feed_composition: dict[str, float] = field(default_factory=_default_feed_composition)
    storage_conditions: dict[str, object] | None = None
    biostimulant_route: BiostimulantRouteOptions | None = None

    def __post_init__(self) -> None:
        if not self.feed_composition:
            object.__setattr__(self, "feed_composition", _default_feed_composition())
        for name in ("wet_feed_rate_kg_hr", "plant_capacity_kg_hr"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isfinite(float(value)) or value <= 0):
                raise ValueError(f"{name} must be finite and greater than zero.")
        canonical_composition = _default_feed_composition()
        unknown_components = set(self.feed_composition) - set(canonical_composition)
        if unknown_components:
            names = ", ".join(sorted(map(str, unknown_components)))
            raise ValueError(f"feed_composition contains unknown compounds: {names}.")
        numeric_composition = {}
        for component_id, value in self.feed_composition.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("feed_composition values must be numeric wet-mass fractions.")
            numeric_value = float(value)
            if not isfinite(numeric_value) or numeric_value < 0:
                raise ValueError("feed_composition values must be finite, non-negative wet-mass fractions.")
            numeric_composition[component_id] = numeric_value
        object.__setattr__(self, "feed_composition", numeric_composition)
        total = sum(numeric_composition.values())
        if not FEED_COMPOSITION_MIN_TOTAL <= total <= FEED_COMPOSITION_MAX_TOTAL:
            raise ValueError(
                "feed_composition total must be between "
                f"{FEED_COMPOSITION_MIN_TOTAL:.2f} and {FEED_COMPOSITION_MAX_TOTAL:.2f} "
                "on a wet-mass basis; "
                f"received {total:.6g}."
            )
        if abs(total - FEED_COMPOSITION_NORMALIZED_TOTAL) > 1e-12:
            object.__setattr__(
                self,
                "feed_composition",
                {
                    key: value * FEED_COMPOSITION_NORMALIZED_TOTAL / total
                    for key, value in numeric_composition.items()
                },
            )
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
        if self.time_step not in {None, "monthly", "weekly", "daily"}:
            raise ValueError("time_step must be 'monthly', 'weekly', 'daily', or null.")
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
            "biostimulant_route",
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
                processing_delay_days=biomass_payload.get("processing_delay_days", 14),
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
        biostimulant_payload = payload.get("biostimulant_route")
        if biostimulant_payload is not None and not isinstance(biostimulant_payload, Mapping):
            raise ValueError("biostimulant_route must be an object or null.")
        biostimulant_route = (
            biostimulant_payload
            if isinstance(biostimulant_payload, BiostimulantRouteOptions)
            else BiostimulantRouteOptions(
                technology_id=str(biostimulant_payload.get("technology_id", "")),
                flux_L_m2_h=(None if biostimulant_payload.get("flux_L_m2_h") is None else float(biostimulant_payload["flux_L_m2_h"])),
                flux_source=biostimulant_payload.get("flux_source"),
                retention_matrix_source=str(biostimulant_payload.get("retention_matrix_source", "")),
                component_retention_overrides={k: float(v) for k, v in dict(biostimulant_payload.get("component_retention_overrides", {})).items()},
                component_retention_override_sources=dict(biostimulant_payload.get("component_retention_override_sources", {})),
                feed_to_reference_concentration_ratio=(None if biostimulant_payload.get("feed_to_reference_concentration_ratio") is None else float(biostimulant_payload["feed_to_reference_concentration_ratio"])),
                flux_model_source=biostimulant_payload.get("flux_model_source"),
                viscosity_Pa_s=(None if biostimulant_payload.get("viscosity_Pa_s") is None else float(biostimulant_payload["viscosity_Pa_s"])),
                viscosity_source=biostimulant_payload.get("viscosity_source"),
                transmembrane_pressure_bar=(None if biostimulant_payload.get("transmembrane_pressure_bar") is None else float(biostimulant_payload["transmembrane_pressure_bar"])),
                pressure_source=biostimulant_payload.get("pressure_source"),
                pump_efficiency_fraction=(None if biostimulant_payload.get("pump_efficiency_fraction") is None else float(biostimulant_payload["pump_efficiency_fraction"])),
                pump_efficiency_source=biostimulant_payload.get("pump_efficiency_source"),
                crossflow_electricity_kwh_m3_feed=(None if biostimulant_payload.get("crossflow_electricity_kwh_m3_feed") is None else float(biostimulant_payload["crossflow_electricity_kwh_m3_feed"])),
                crossflow_electricity_source=biostimulant_payload.get("crossflow_electricity_source"),
                use_hormone_benchmarks=biostimulant_payload.get("use_hormone_benchmarks", False),
                hormone_benchmark_source=biostimulant_payload.get("hormone_benchmark_source"),
                cip_solution_volume_L_per_step=(None if biostimulant_payload.get("cip_solution_volume_L_per_step") is None else float(biostimulant_payload["cip_solution_volume_L_per_step"])),
                cip_makeup_fraction_per_cycle=(None if biostimulant_payload.get("cip_makeup_fraction_per_cycle") is None else float(biostimulant_payload["cip_makeup_fraction_per_cycle"])),
                cip_input_source=biostimulant_payload.get("cip_input_source"),
            ) if biostimulant_payload else None
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
            feed_composition=dict(payload.get("feed_composition") or _default_feed_composition()),
            storage_conditions=payload.get("storage_conditions"),
            biostimulant_route=biostimulant_route,
        )
