"""Custom BioSTEAM units for GreenHub Phase 4 protein recovery.

The units in this module are material-allocation and utility models. They do
not claim rigorous electrolyte equilibrium, equipment purchase costs, or air
psychrometrics. Every empirical pool transfer and physical loss is retained
in a named outlet so plant-wide mass, element, nitrogen, COD, and TOC closure
can be checked explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, isfinite
from typing import Iterable, Mapping

import biosteam as bst

from Greenhub.scientific_equations import protein_precipitation_mass_balance

from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase4_specifications import (
    AcidDemandResult,
    BaseDemandResult,
    DryerEnergyResult,
    DryerMassResult,
    LiquidEntrainmentResult,
    bounded_fraction,
    calculate_acid_demand,
    calculate_dryer_energy,
    calculate_stoichiometric_base_demand,
    nonnegative,
    resolve_recovery,
    solve_dryer_mass_balance,
    solve_liquid_entrainment_for_cake_moisture,
    validate_component_fraction_mapping,
    validate_pH,
)
from Greenhub.reactions import REACTION_DEFINITIONS


def _required_float(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if value is None:
        raise ValueError(f"Missing required Phase 4 parameter '{name}'.")
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Phase 4 parameter '{name}' must be numeric.") from error


def _optional_float(
    values: Mapping[str, object],
    name: str,
    default: float | None = None,
) -> float | None:
    value = values.get(name, default)
    return None if value is None else float(value)


def _text(values: Mapping[str, object], name: str, default: str) -> str:
    value = values.get(name, default)
    return default if value is None else str(value).strip()


def _set_conditions(stream, source, *, temperature: float | None = None) -> None:
    stream.T = source.T if temperature is None else temperature
    stream.P = source.P
    stream.phase = source.phase


def _sum_inlets(streams: Iterable[bst.Stream]) -> dict[str, float]:
    return {
        component_id: sum(float(stream.imass[component_id]) for stream in streams)
        for component_id in chemicals.IDs
    }


def _mix_material(output: bst.Stream, streams: Iterable[bst.Stream]) -> None:
    """Mix material conservatively without invoking electrolyte equilibrium."""

    sources = tuple(streams)
    output.empty()
    for component_id, mass in _sum_inlets(sources).items():
        output.imass[component_id] = mass
    total_mass = sum(stream.F_mass for stream in sources)
    if total_mass:
        output.T = sum(stream.F_mass * stream.T for stream in sources) / total_mass
        output.P = min(stream.P for stream in sources if stream.F_mass) if any(
            stream.F_mass for stream in sources
        ) else sources[0].P
        output.phase = sources[0].phase


def _component_is_suspended(component_id: str) -> bool:
    metadata = COMPONENT_METADATA[component_id]
    return (
        component_id in COMPONENT_GROUPS["suspended_solids"]
        or metadata.particle_class == "suspended"
        or metadata.default_phase == "s"
    )


def _equipment_count(load: float, capacity: float | None) -> int:
    if load <= 0.0:
        return 0
    return max(1, ceil(load / capacity)) if capacity else 1


@dataclass(frozen=True)
class AcidificationParameters:
    """Commercial-acid dosing and screening-level pH metadata."""

    enabled: bool
    acid_type: str
    acid_solution_mass_fraction: float
    acid_purity: float
    acid_demand_method: str
    acid_dose_kg_per_m3: float | None
    feed_pH: float
    target_pH: float
    feed_density_kg_m3: float
    feed_alkalinity_mg_caco3_L: float | None
    buffer_capacity_mol_H_per_L_pH: float | None
    titration_points: tuple[tuple[float, float], ...]
    reagent_temperature_C: float
    mixing_time_min: float
    mixing_power_kw_per_m3: float

    def validate(self) -> None:
        if self.acid_type not in {"HydrochloricAcid", "SulfuricAcid"}:
            raise ValueError("Phase 4 acid_type must be HydrochloricAcid or SulfuricAcid.")
        bounded_fraction(
            self.acid_solution_mass_fraction,
            "Acid solution mass fraction",
            positive=True,
        )
        bounded_fraction(self.acid_purity, "Acid purity", positive=True)
        validate_pH(self.feed_pH, "Feed pH")
        validate_pH(self.target_pH, "Target precipitation pH")
        if self.enabled and self.target_pH > self.feed_pH:
            raise ValueError("Acidification target pH cannot exceed feed pH.")
        if self.feed_density_kg_m3 <= 0.0:
            raise ValueError("Phase 4 feed density must be positive.")
        nonnegative(self.mixing_time_min, "Acid mixing time")
        nonnegative(self.mixing_power_kw_per_m3, "Acid mixing power")
        if self.acid_dose_kg_per_m3 is not None:
            nonnegative(self.acid_dose_kg_per_m3, "Acid dose")


@dataclass(frozen=True)
class PrecipitationParameters:
    """Empirical acid precipitation and heat-coagulation assumptions."""

    acid_enabled: bool
    heat_enabled: bool
    acid_recovery_mode: str
    acid_direct_recovery: float | None
    acid_maximum_recovery: float
    heat_recovery_mode: str
    heat_direct_recovery: float | None
    heat_maximum_recovery: float
    target_pH: float
    effective_protein_pI: float
    pH_width: float
    precipitation_temperature_C: float
    residence_time_min: float
    acid_rate_constant_per_min: float | None
    heat_rate_constant_per_min: float | None
    activation_energy_kj_per_mol: float | None
    reference_temperature_C: float
    working_volume_fraction: float
    mixing_power_kw_per_m3: float
    feed_density_kg_m3: float

    def validate(self) -> None:
        for name in ("acid_maximum_recovery", "heat_maximum_recovery"):
            bounded_fraction(getattr(self, name), name)
        for name in ("acid_direct_recovery", "heat_direct_recovery"):
            value = getattr(self, name)
            if value is not None:
                bounded_fraction(value, name)
        validate_pH(self.target_pH, "Precipitation pH")
        validate_pH(self.effective_protein_pI, "Effective protein pI")
        if self.pH_width <= 0.0:
            raise ValueError("Protein pH-response width must be positive.")
        if not -5.0 <= self.precipitation_temperature_C <= 150.0:
            raise ValueError("Precipitation temperature must be within -5 to 150 degC.")
        nonnegative(self.residence_time_min, "Precipitation residence time")
        bounded_fraction(
            self.working_volume_fraction,
            "Precipitation working-volume fraction",
            positive=True,
        )
        nonnegative(self.mixing_power_kw_per_m3, "Precipitation mixing power")
        if self.feed_density_kg_m3 <= 0.0:
            raise ValueError("Precipitation feed density must be positive.")


@dataclass(frozen=True)
class ProteinSeparatorParameters:
    """Protein capture, co-precipitation, cake moisture, and power inputs."""

    precipitated_protein_capture_fraction: float
    suspended_protein_capture_fraction: float
    soluble_protein_loss_fraction: float
    cake_moisture_fraction: float
    electricity_kwh_per_m3: float
    feed_density_kg_m3: float
    hydraulic_capacity_m3_hr: float | None
    solids_capacity_kg_hr: float | None
    co_precipitation_fractions: Mapping[str, float] = field(default_factory=dict)

    def validate(self) -> None:
        for name in (
            "precipitated_protein_capture_fraction",
            "suspended_protein_capture_fraction",
            "soluble_protein_loss_fraction",
        ):
            bounded_fraction(getattr(self, name), name)
        bounded_fraction(
            self.cake_moisture_fraction,
            "Protein cake moisture",
            upper_open=True,
        )
        nonnegative(self.electricity_kwh_per_m3, "Protein-separator electricity")
        if self.feed_density_kg_m3 <= 0.0:
            raise ValueError("Protein-separator feed density must be positive.")
        for name, value in self.co_precipitation_fractions.items():
            if name not in CO_PRECIPITATION_GROUPS:
                raise KeyError(f"Unknown co-precipitation category '{name}'.")
            bounded_fraction(value, f"Co-precipitation fraction for {name}")
        for name, value in (
            ("hydraulic_capacity_m3_hr", self.hydraulic_capacity_m3_hr),
            ("solids_capacity_kg_hr", self.solids_capacity_kg_hr),
        ):
            if value is not None and value <= 0.0:
                raise ValueError(f"{name} must be positive when supplied.")


@dataclass(frozen=True)
class WashingParameters:
    """Single-stage displacement-wash assumptions."""

    enabled: bool
    wash_water_kg_per_kg_dry_cake: float
    soluble_salt_removal_fraction: float
    residual_sugar_removal_fraction: float
    residual_acid_removal_fraction: float
    soluble_cod_removal_fraction: float
    protein_loss_fraction: float
    stage_count: int
    target_cake_moisture_fraction: float

    def validate(self) -> None:
        nonnegative(self.wash_water_kg_per_kg_dry_cake, "Wash-water ratio")
        for name in (
            "soluble_salt_removal_fraction",
            "residual_sugar_removal_fraction",
            "residual_acid_removal_fraction",
            "soluble_cod_removal_fraction",
            "protein_loss_fraction",
        ):
            bounded_fraction(getattr(self, name), name)
        bounded_fraction(
            self.target_cake_moisture_fraction,
            "Washed-cake moisture",
            upper_open=True,
        )
        if self.stage_count != 1:
            raise ValueError("Phase 4 currently supports exactly one wash stage.")


@dataclass(frozen=True)
class DewateringParameters:
    """Mechanical dewatering assumptions before the belt dryer."""

    target_solids_fraction: float
    protein_capture_fraction: float
    electricity_kwh_per_t_wet: float
    capacity_kg_hr: float | None

    def validate(self) -> None:
        bounded_fraction(
            self.target_solids_fraction,
            "Target dryer-feed solids",
            positive=True,
            upper_open=True,
        )
        bounded_fraction(self.protein_capture_fraction, "Dewatering protein capture")
        nonnegative(self.electricity_kwh_per_t_wet, "Dewatering electricity")
        if self.capacity_kg_hr is not None and self.capacity_kg_hr <= 0.0:
            raise ValueError("Dewatering capacity must be positive when supplied.")


@dataclass(frozen=True)
class DryerParameters:
    """Low-temperature cake-dryer mass and selected-method energy inputs."""

    dryer_type: str
    target_product_moisture_fraction: float
    dryer_temperature_C: float
    product_outlet_temperature_C: float
    energy_calculation_method: str
    thermal_efficiency: float
    heat_loss_fraction: float
    specific_heat_demand_kj_per_kg_water: float | None
    electricity_kwh_per_kg_water_evaporated: float
    dust_loss_fraction: float
    protein_entrainment_loss_fraction: float
    thermal_protein_degradation_fraction: float
    capacity_kg_hr: float | None
    residence_time_min: float
    heat_source: str

    def validate(self) -> None:
        bounded_fraction(
            self.target_product_moisture_fraction,
            "Target product moisture",
            upper_open=True,
        )
        bounded_fraction(self.thermal_efficiency, "Dryer thermal efficiency", positive=True)
        bounded_fraction(self.heat_loss_fraction, "Dryer heat-loss fraction", upper_open=True)
        for name in (
            "dust_loss_fraction",
            "protein_entrainment_loss_fraction",
            "thermal_protein_degradation_fraction",
        ):
            bounded_fraction(getattr(self, name), name)
        nonnegative(
            self.electricity_kwh_per_kg_water_evaporated,
            "Dryer electricity demand",
        )
        nonnegative(self.residence_time_min, "Dryer residence time")
        if not -5.0 <= self.dryer_temperature_C <= 200.0:
            raise ValueError("Dryer temperature must be within -5 to 200 degC.")
        if not -5.0 <= self.product_outlet_temperature_C <= 200.0:
            raise ValueError("Dryer product temperature must be within -5 to 200 degC.")
        if self.capacity_kg_hr is not None and self.capacity_kg_hr <= 0.0:
            raise ValueError("Dryer capacity must be positive when supplied.")
        if self.heat_source not in {
            "external_steam",
            "hot_water",
            "natural_gas",
            "electric_heating",
            "waste_heat",
            "heat_pump",
        }:
            raise ValueError(f"Unsupported Phase 4 dryer heat source '{self.heat_source}'.")


@dataclass(frozen=True)
class NeutralizationParameters:
    """Base-solution dosing and molecular salt bookkeeping assumptions."""

    acid_type: str
    base_type: str
    base_solution_mass_fraction: float
    base_purity: float
    base_demand_method: str
    empirical_base_dose_kg_per_m3: float | None
    inlet_pH: float
    target_pH: float
    feed_density_kg_m3: float
    mixing_time_min: float
    mixing_power_kw_per_m3: float
    reagent_temperature_C: float

    def validate(self) -> None:
        if self.base_type not in {"SodiumHydroxide", "CalciumHydroxide"}:
            raise ValueError("base_type must be SodiumHydroxide or CalciumHydroxide.")
        bounded_fraction(
            self.base_solution_mass_fraction,
            "Base solution mass fraction",
            positive=True,
        )
        bounded_fraction(self.base_purity, "Base purity", positive=True)
        validate_pH(self.inlet_pH, "Neutralization inlet pH")
        validate_pH(self.target_pH, "Conditioned-liquid target pH")
        if self.target_pH < self.inlet_pH:
            raise ValueError("Neutralization target pH cannot be below inlet pH.")
        if self.feed_density_kg_m3 <= 0.0:
            raise ValueError("Neutralization feed density must be positive.")
        nonnegative(self.mixing_time_min, "Neutralization mixing time")
        nonnegative(self.mixing_power_kw_per_m3, "Neutralization mixing power")
        if self.empirical_base_dose_kg_per_m3 is not None:
            nonnegative(self.empirical_base_dose_kg_per_m3, "Empirical base dose")


CO_PRECIPITATION_GROUPS: dict[str, frozenset[str]] = {
    "suspended_solids": COMPONENT_GROUPS["suspended_solids"],
    "colloidal_carbohydrates": frozenset({"Pectin", "Starch", "EntrappedSugars"}),
    "lipids": frozenset({"Lipids"}),
    "particulate_phosphorus": COMPONENT_GROUPS["particulate_phosphorus"],
    "mineral_ash": frozenset(
        {"Ash", "InertSolids", "SuspendedInertSolids", "Sand", "CalciumSulfate"}
    ),
    "heavy_metals": COMPONENT_GROUPS["heavy_metals"],
    "microplastics": frozenset({"Microplastics"}),
    "other_particulates": frozenset(
        {"ParticulateBiodegradableOrganics", "MicrobialBiomass", "SuspendedSolids"}
    ),
}


def acidification_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    enabled: bool,
    titration_points: Iterable[tuple[float, float]] = (),
) -> AcidificationParameters:
    parameters = AcidificationParameters(
        enabled=enabled,
        acid_type=_text(values, "acid_type", "HydrochloricAcid"),
        acid_solution_mass_fraction=_required_float(values, "acid_solution_mass_fraction"),
        acid_purity=_required_float(values, "acid_purity"),
        acid_demand_method=_text(values, "acid_demand_method", "empirical_dose"),
        acid_dose_kg_per_m3=_optional_float(values, "acid_dose_kg_per_m3"),
        feed_pH=_required_float(values, "feed_pH"),
        target_pH=(
            _required_float(values, "target_pH")
            if enabled
            else _required_float(values, "feed_pH")
        ),
        feed_density_kg_m3=_required_float(values, "phase4_feed_density_kg_m3"),
        feed_alkalinity_mg_caco3_L=_optional_float(values, "feed_alkalinity_mg_caco3_L"),
        buffer_capacity_mol_H_per_L_pH=_optional_float(
            values,
            "buffer_capacity_mol_H_per_L_pH",
        ),
        titration_points=tuple((float(dose), float(pH)) for dose, pH in titration_points),
        reagent_temperature_C=_required_float(values, "acid_reagent_temperature_C"),
        mixing_time_min=_required_float(values, "acid_mixing_time_min"),
        mixing_power_kw_per_m3=_required_float(values, "acid_mixing_power_kw_per_m3"),
    )
    parameters.validate()
    return parameters


def precipitation_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    acid_enabled: bool,
    heat_enabled: bool,
) -> PrecipitationParameters:
    parameters = PrecipitationParameters(
        acid_enabled=acid_enabled,
        heat_enabled=heat_enabled,
        acid_recovery_mode=_text(values, "precipitation_kinetic_model", "direct_yield"),
        acid_direct_recovery=_optional_float(values, "precipitation_efficiency"),
        acid_maximum_recovery=_required_float(values, "maximum_protein_recovery"),
        heat_recovery_mode=_text(values, "heat_coagulation_kinetic_model", "direct_yield"),
        heat_direct_recovery=_optional_float(values, "heat_coagulation_efficiency"),
        heat_maximum_recovery=_required_float(values, "maximum_heat_coagulation_recovery"),
        target_pH=_required_float(values, "target_pH") if acid_enabled else _required_float(values, "feed_pH"),
        effective_protein_pI=_required_float(values, "effective_protein_pI"),
        pH_width=_required_float(values, "effective_precipitation_pH_width"),
        precipitation_temperature_C=_required_float(values, "precipitation_temperature_C"),
        residence_time_min=_required_float(values, "precipitation_residence_time_min"),
        acid_rate_constant_per_min=_optional_float(values, "precipitation_rate_constant_per_min"),
        heat_rate_constant_per_min=_optional_float(values, "heat_coagulation_rate_constant_per_min"),
        activation_energy_kj_per_mol=_optional_float(values, "precipitation_activation_energy_kj_per_mol"),
        reference_temperature_C=_required_float(values, "kinetic_reference_temperature_C"),
        working_volume_fraction=_required_float(values, "precipitation_working_volume_fraction"),
        mixing_power_kw_per_m3=_required_float(values, "precipitation_mixing_power_kw_per_m3"),
        feed_density_kg_m3=_required_float(values, "phase4_feed_density_kg_m3"),
    )
    parameters.validate()
    return parameters


def separator_parameters_from_mapping(values: Mapping[str, object]) -> ProteinSeparatorParameters:
    co_precipitation = {
        name: _required_float(values, f"co_precipitation_{name}_fraction")
        for name in CO_PRECIPITATION_GROUPS
    }
    parameters = ProteinSeparatorParameters(
        precipitated_protein_capture_fraction=_required_float(
            values,
            "precipitated_protein_capture_fraction",
        ),
        suspended_protein_capture_fraction=_required_float(
            values,
            "suspended_protein_capture_fraction",
        ),
        soluble_protein_loss_fraction=_required_float(values, "separator_soluble_protein_loss_fraction"),
        cake_moisture_fraction=_required_float(values, "protein_cake_moisture_fraction"),
        electricity_kwh_per_m3=_required_float(values, "protein_separator_electricity_kwh_per_m3"),
        feed_density_kg_m3=_required_float(values, "phase4_feed_density_kg_m3"),
        hydraulic_capacity_m3_hr=_optional_float(values, "protein_separator_capacity_m3_hr"),
        solids_capacity_kg_hr=_optional_float(values, "protein_separator_solids_capacity_kg_hr"),
        co_precipitation_fractions=co_precipitation,
    )
    parameters.validate()
    return parameters


def washing_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    enabled: bool,
) -> WashingParameters:
    parameters = WashingParameters(
        enabled=enabled,
        wash_water_kg_per_kg_dry_cake=_required_float(values, "wash_water_kg_per_kg_dry_cake"),
        soluble_salt_removal_fraction=_required_float(values, "salt_wash_efficiency"),
        residual_sugar_removal_fraction=_required_float(values, "residual_sugar_removal_fraction"),
        residual_acid_removal_fraction=_required_float(values, "residual_acid_removal_fraction"),
        soluble_cod_removal_fraction=_required_float(values, "soluble_cod_removal_fraction"),
        protein_loss_fraction=_required_float(values, "protein_wash_loss_fraction"),
        stage_count=int(_required_float(values, "wash_stage_count")),
        target_cake_moisture_fraction=_required_float(values, "washed_cake_moisture_fraction"),
    )
    parameters.validate()
    return parameters


def dewatering_parameters_from_mapping(values: Mapping[str, object]) -> DewateringParameters:
    parameters = DewateringParameters(
        target_solids_fraction=_required_float(values, "target_dryer_feed_solids_fraction"),
        protein_capture_fraction=_required_float(values, "dewatering_protein_capture_fraction"),
        electricity_kwh_per_t_wet=_required_float(values, "dewatering_electricity_kwh_per_t_wet"),
        capacity_kg_hr=_optional_float(values, "dewatering_capacity_kg_hr"),
    )
    parameters.validate()
    return parameters


def dryer_parameters_from_mapping(values: Mapping[str, object]) -> DryerParameters:
    parameters = DryerParameters(
        dryer_type=_text(values, "dryer_type", "low_temperature_belt_dryer"),
        target_product_moisture_fraction=_required_float(values, "target_product_moisture_fraction"),
        dryer_temperature_C=_required_float(values, "dryer_temperature_C"),
        product_outlet_temperature_C=_required_float(values, "product_outlet_temperature_C"),
        energy_calculation_method=_text(values, "dryer_energy_method", "thermodynamic"),
        thermal_efficiency=_required_float(values, "dryer_thermal_efficiency"),
        heat_loss_fraction=_required_float(values, "dryer_heat_loss_fraction"),
        specific_heat_demand_kj_per_kg_water=_optional_float(
            values,
            "specific_heat_demand_kj_per_kg_water",
        ),
        electricity_kwh_per_kg_water_evaporated=_required_float(
            values,
            "dryer_electricity_kwh_per_kg_water_evaporated",
        ),
        dust_loss_fraction=_required_float(values, "dryer_dust_loss_fraction"),
        protein_entrainment_loss_fraction=_required_float(
            values,
            "dryer_protein_entrainment_loss_fraction",
        ),
        thermal_protein_degradation_fraction=_required_float(
            values,
            "thermal_protein_degradation_fraction",
        ),
        capacity_kg_hr=_optional_float(values, "dryer_capacity_kg_hr"),
        residence_time_min=_required_float(values, "dryer_residence_time_min"),
        heat_source=_text(values, "dryer_heat_source", "hot_water"),
    )
    parameters.validate()
    return parameters


def neutralization_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    acid_enabled: bool = True,
) -> NeutralizationParameters:
    parameters = NeutralizationParameters(
        acid_type=_text(values, "acid_type", "HydrochloricAcid"),
        base_type=_text(values, "base_type", "SodiumHydroxide"),
        base_solution_mass_fraction=_required_float(values, "base_solution_mass_fraction"),
        base_purity=_required_float(values, "base_purity"),
        base_demand_method=_text(values, "base_demand_method", "stoichiometric"),
        empirical_base_dose_kg_per_m3=_optional_float(values, "base_dose_kg_per_m3"),
        inlet_pH=(
            _required_float(values, "target_pH")
            if acid_enabled
            else _required_float(values, "feed_pH")
        ),
        target_pH=_required_float(values, "target_digester_feed_pH"),
        feed_density_kg_m3=_required_float(values, "phase4_feed_density_kg_m3"),
        mixing_time_min=_required_float(values, "neutralization_mixing_time_min"),
        mixing_power_kw_per_m3=_required_float(values, "neutralization_mixing_power_kw_per_m3"),
        reagent_temperature_C=_required_float(values, "base_reagent_temperature_C"),
    )
    parameters.validate()
    return parameters


class AcidificationMixer(bst.Unit):
    """Dose commercial acid solution and assign pH as non-rigorous metadata."""

    _N_ins = 2
    _N_outs = 1
    line = "Acid dosing and mixing"
    _units = {
        "Liquid throughput": "m3/hr",
        "Pure acid flow": "kg/hr",
        "Acid solution flow": "kg/hr",
        "Reagent water": "kg/hr",
        "Pure acid dose": "kg/m3",
        "Initial pH": "-",
        "Target pH": "-",
        "Mixing time": "min",
        "Mixing volume": "m3",
        "Specific mixing power": "kW/m3",
    }

    def _init(self, parameters: AcidificationParameters):
        parameters.validate()
        self.parameters = parameters
        self.acid_demand: AcidDemandResult | None = None
        self.inlet_pH = parameters.feed_pH
        self.outlet_pH = parameters.target_pH if parameters.enabled else parameters.feed_pH
        self.warnings: list[str] = []

    def _run(self):
        feed, acid_solution = self.ins
        acidified = self.outs[0]
        acid_solution.empty()
        target = self.parameters.target_pH if self.parameters.enabled else self.parameters.feed_pH
        self.acid_demand = calculate_acid_demand(
            method=self.parameters.acid_demand_method,
            acid_type=self.parameters.acid_type,
            liquid_flow_m3_hr=feed.F_mass / self.parameters.feed_density_kg_m3,
            initial_pH=self.parameters.feed_pH,
            target_pH=target,
            acid_solution_mass_fraction=self.parameters.acid_solution_mass_fraction,
            acid_purity=self.parameters.acid_purity,
            empirical_dose_kg_per_m3=(
                self.parameters.acid_dose_kg_per_m3 if self.parameters.enabled else 0.0
            ),
            alkalinity_mg_caco3_L=self.parameters.feed_alkalinity_mg_caco3_L,
            buffer_capacity_mol_H_per_L_pH=self.parameters.buffer_capacity_mol_H_per_L_pH,
            titration_points=self.parameters.titration_points,
        )
        acid_solution.imass[self.parameters.acid_type] = self.acid_demand.pure_acid_kg_hr
        acid_solution.imass["Water"] = self.acid_demand.reagent_water_kg_hr
        acid_solution.T = self.parameters.reagent_temperature_C + 273.15
        acid_solution.P = feed.P
        acid_solution.phase = "l"
        _mix_material(acidified, self.ins)
        if self.acid_demand.warning and self.acid_demand.warning not in self.warnings:
            self.warnings.append(self.acid_demand.warning)

    def _design(self):
        feed = self.ins[0]
        volume_flow = feed.F_mass / self.parameters.feed_density_kg_m3
        mixing_volume = volume_flow * self.parameters.mixing_time_min / 60.0
        demand = self.acid_demand
        self.design_results["Liquid throughput"] = volume_flow
        self.design_results["Pure acid flow"] = demand.pure_acid_kg_hr if demand else 0.0
        self.design_results["Acid solution flow"] = demand.acid_solution_kg_hr if demand else 0.0
        self.design_results["Reagent water"] = demand.reagent_water_kg_hr if demand else 0.0
        self.design_results["Pure acid dose"] = demand.pure_acid_dose_kg_m3 if demand else 0.0
        self.design_results["Initial pH"] = self.inlet_pH
        self.design_results["Target pH"] = self.outlet_pH
        self.design_results["Mixing time"] = self.parameters.mixing_time_min
        self.design_results["Mixing volume"] = mixing_volume
        self.design_results["Specific mixing power"] = self.parameters.mixing_power_kw_per_m3
        self.power_utility.consumption = mixing_volume * self.parameters.mixing_power_kw_per_m3


class ProteinPrecipitation(bst.Unit):
    """Transfer soluble protein into empirical acid and heat-recovered pools."""

    _N_ins = 1
    _N_outs = 1
    line = "Protein precipitation and coagulation"
    _units = {
        "Liquid throughput": "m3/hr",
        "Residence time": "min",
        "Working volume": "m3",
        "Vessel volume": "m3",
        "Working-volume fraction": "fraction",
        "Acid recovery": "fraction",
        "Heat recovery": "fraction",
        "Acid-precipitated protein": "kg/hr",
        "Heat-coagulated protein": "kg/hr",
        "Temperature": "degC",
        "Specific mixing power": "kW/m3",
    }

    def _init(self, parameters: PrecipitationParameters):
        parameters.validate()
        self.parameters = parameters
        self.acid_recovery_fraction = 0.0
        self.heat_recovery_fraction = 0.0
        self.transfers_kg_hr: dict[str, float] = {}
        self.warnings: list[str] = []

    def _run(self):
        feed = self.ins[0]
        slurry = self.outs[0]
        slurry.copy_like(feed)
        temperature_K = self.parameters.precipitation_temperature_C + 273.15
        if self.parameters.acid_enabled:
            self.acid_recovery_fraction = resolve_recovery(
                mode=self.parameters.acid_recovery_mode,
                direct_recovery=self.parameters.acid_direct_recovery,
                maximum_recovery=self.parameters.acid_maximum_recovery,
                pH=self.parameters.target_pH,
                isoelectric_pH=self.parameters.effective_protein_pI,
                pH_width=self.parameters.pH_width,
                residence_time_min=self.parameters.residence_time_min,
                rate_constant_per_min=self.parameters.acid_rate_constant_per_min,
                activation_energy_kj_per_mol=self.parameters.activation_energy_kj_per_mol,
                temperature_K=temperature_K,
                reference_temperature_K=self.parameters.reference_temperature_C + 273.15,
            )
        else:
            self.acid_recovery_fraction = 0.0
        acid_balance = protein_precipitation_mass_balance(
            float(slurry.imass["SolubleProtein"]),
            self.acid_recovery_fraction,
        )
        acid_mass = acid_balance.protein_cake_kg_hr
        slurry.imass["SolubleProtein"] = acid_balance.protein_supernatant_kg_hr
        slurry.imass["PrecipitatedProtein"] += acid_mass

        if self.parameters.heat_enabled:
            self.heat_recovery_fraction = resolve_recovery(
                mode=self.parameters.heat_recovery_mode,
                direct_recovery=self.parameters.heat_direct_recovery,
                maximum_recovery=self.parameters.heat_maximum_recovery,
                pH=self.parameters.target_pH,
                isoelectric_pH=self.parameters.effective_protein_pI,
                pH_width=self.parameters.pH_width,
                residence_time_min=self.parameters.residence_time_min,
                rate_constant_per_min=self.parameters.heat_rate_constant_per_min,
                activation_energy_kj_per_mol=self.parameters.activation_energy_kj_per_mol,
                temperature_K=temperature_K,
                reference_temperature_K=self.parameters.reference_temperature_C + 273.15,
            )
        else:
            self.heat_recovery_fraction = 0.0
        heat_balance = protein_precipitation_mass_balance(
            float(slurry.imass["SolubleProtein"]),
            self.heat_recovery_fraction,
        )
        heat_mass = heat_balance.protein_cake_kg_hr
        slurry.imass["SolubleProtein"] = heat_balance.protein_supernatant_kg_hr
        slurry.imass["HeatCoagulatedProtein"] += heat_mass
        self.transfers_kg_hr = {
            "SolubleProtein_to_PrecipitatedProtein": acid_mass,
            "SolubleProtein_to_HeatCoagulatedProtein": heat_mass,
        }
        slurry.T = temperature_K if self.parameters.heat_enabled else feed.T
        slurry.P = feed.P

    def _design(self):
        feed = self.ins[0]
        volume_flow = feed.F_mass / self.parameters.feed_density_kg_m3
        working_volume = volume_flow * self.parameters.residence_time_min / 60.0
        vessel_volume = working_volume / self.parameters.working_volume_fraction
        self.design_results["Liquid throughput"] = volume_flow
        self.design_results["Residence time"] = self.parameters.residence_time_min
        self.design_results["Working volume"] = working_volume
        self.design_results["Vessel volume"] = vessel_volume
        self.design_results["Working-volume fraction"] = self.parameters.working_volume_fraction
        self.design_results["Acid recovery"] = self.acid_recovery_fraction
        self.design_results["Heat recovery"] = self.heat_recovery_fraction
        self.design_results["Acid-precipitated protein"] = self.transfers_kg_hr.get(
            "SolubleProtein_to_PrecipitatedProtein",
            0.0,
        )
        self.design_results["Heat-coagulated protein"] = self.transfers_kg_hr.get(
            "SolubleProtein_to_HeatCoagulatedProtein",
            0.0,
        )
        self.design_results["Temperature"] = self.outs[0].T - 273.15
        self.design_results["Specific mixing power"] = self.parameters.mixing_power_kw_per_m3
        self.power_utility.consumption = working_volume * self.parameters.mixing_power_kw_per_m3


class ProteinSeparator(bst.Unit):
    """Custom separator with fixed capture plus uniform dissolved-liquid entrainment."""

    _N_ins = 1
    _N_outs = 2
    line = "Protein separator"
    _units = {
        "Hydraulic throughput": "m3/hr",
        "Dry-solids capture": "kg/hr",
        "Wet cake flow": "kg/hr",
        "Cake moisture": "fraction",
        "Target cake moisture": "fraction",
        "Liquid entrainment": "fraction",
        "Protein captured": "kg/hr",
        "Equipment count": "-",
        "Specific electricity": "kWh/m3",
    }

    def _init(self, parameters: ProteinSeparatorParameters):
        parameters.validate()
        self.parameters = parameters
        self.partitioning: dict[str, dict[str, float | str]] = {}
        self.entrainment_result: LiquidEntrainmentResult | None = None
        self.warnings: list[str] = []

    def _fixed_capture(self, component_id: str) -> tuple[float, str]:
        if component_id in {"PrecipitatedProtein", "HeatCoagulatedProtein"}:
            return self.parameters.precipitated_protein_capture_fraction, "precipitated_protein"
        if component_id == "SuspendedProtein":
            return self.parameters.suspended_protein_capture_fraction, "suspended_protein"
        if component_id == "SolubleProtein":
            return self.parameters.soluble_protein_loss_fraction, "soluble_protein_adsorption"
        matches = [
            name
            for name, components in CO_PRECIPITATION_GROUPS.items()
            if component_id in components and name in self.parameters.co_precipitation_fractions
        ]
        if matches:
            selected = max(
                matches,
                key=lambda name: self.parameters.co_precipitation_fractions[name],
            )
            return float(self.parameters.co_precipitation_fractions[selected]), f"co_precipitation:{selected}"
        return 0.0, "no_fixed_capture"

    def _run(self):
        slurry = self.ins[0]
        cake, centrate = self.outs
        cake.empty()
        centrate.empty()
        fixed_cake = 0.0
        dissolved_available = 0.0
        interim: dict[str, tuple[float, float, str, bool]] = {}
        for component_id in chemicals.IDs:
            if component_id == "Water":
                continue
            inlet = float(slurry.imass[component_id])
            capture, source = self._fixed_capture(component_id)
            fixed = inlet * capture
            remaining = inlet - fixed
            suspended = _component_is_suspended(component_id)
            fixed_cake += fixed
            if not suspended:
                dissolved_available += remaining
            interim[component_id] = fixed, remaining, source, suspended

        self.entrainment_result = solve_liquid_entrainment_for_cake_moisture(
            fixed_cake_dry_solids_kg_hr=fixed_cake,
            dissolved_solids_available_kg_hr=dissolved_available,
            water_available_kg_hr=float(slurry.imass["Water"]),
            target_cake_moisture_fraction=self.parameters.cake_moisture_fraction,
        )
        entrainment = self.entrainment_result.liquid_entrainment_fraction
        self.partitioning = {}
        for component_id, (fixed, remaining, source, suspended) in interim.items():
            entrained = 0.0 if suspended else remaining * entrainment
            cake.imass[component_id] = fixed + entrained
            centrate.imass[component_id] = remaining - entrained
            inlet = fixed + remaining
            self.partitioning[component_id] = {
                "fixed_capture_fraction": fixed / inlet if inlet else 0.0,
                "liquid_entrainment_fraction": entrainment if not suspended else 0.0,
                "total_to_cake_fraction": float(cake.imass[component_id]) / inlet if inlet else 0.0,
                "source": source,
            }
        cake.imass["Water"] = self.entrainment_result.cake_water_kg_hr
        centrate.imass["Water"] = float(slurry.imass["Water"]) - float(cake.imass["Water"])
        _set_conditions(cake, slurry)
        _set_conditions(centrate, slurry)

    def _design(self):
        slurry = self.ins[0]
        cake = self.outs[0]
        volume = slurry.F_mass / self.parameters.feed_density_kg_m3
        dry_cake = cake.F_mass - float(cake.imass["Water"])
        count_hydraulic = _equipment_count(volume, self.parameters.hydraulic_capacity_m3_hr)
        count_solids = _equipment_count(dry_cake, self.parameters.solids_capacity_kg_hr)
        count = max(count_hydraulic, count_solids)
        moisture = float(cake.imass["Water"]) / cake.F_mass if cake.F_mass else 0.0
        protein = sum(float(cake.imass[ID]) for ID in COMPONENT_GROUPS["protein_product_components"])
        self.design_results["Hydraulic throughput"] = volume
        self.design_results["Dry-solids capture"] = dry_cake
        self.design_results["Wet cake flow"] = cake.F_mass
        self.design_results["Cake moisture"] = moisture
        self.design_results["Target cake moisture"] = self.parameters.cake_moisture_fraction
        self.design_results["Liquid entrainment"] = (
            self.entrainment_result.liquid_entrainment_fraction
            if self.entrainment_result
            else 0.0
        )
        self.design_results["Protein captured"] = protein
        self.design_results["Equipment count"] = count
        self.design_results["Specific electricity"] = self.parameters.electricity_kwh_per_m3
        self.power_utility.consumption = volume * self.parameters.electricity_kwh_per_m3


class CakeWasher(bst.Unit):
    """Single-stage cake wash that removes only configured entrained solutes."""

    _N_ins = 2
    _N_outs = 2
    line = "Protein-cake washer"
    _units = {
        "Dry cake entering": "kg/hr",
        "Wash-water ratio": "kg/kg dry cake",
        "Wash-water flow": "kg/hr",
        "Washed cake flow": "kg/hr",
        "Washed cake moisture": "fraction",
        "Protein wash loss": "kg/hr",
        "Dissolved solids removed": "kg/hr",
        "Stage count": "-",
    }

    def _init(self, parameters: WashingParameters):
        parameters.validate()
        self.parameters = parameters
        self.removal_kg_hr: dict[str, float] = {}
        self.warnings: list[str] = []

    def _removal_fraction(self, component_id: str) -> tuple[float, str]:
        if component_id in COMPONENT_GROUPS["protein_product_components"] or component_id == "DegradedProtein":
            return self.parameters.protein_loss_fraction, "protein_wash_loss"
        if component_id in {"HydrochloricAcid", "SulfuricAcid"}:
            return self.parameters.residual_acid_removal_fraction, "residual_acid"
        if component_id in COMPONENT_GROUPS["soluble_sugars"]:
            return self.parameters.residual_sugar_removal_fraction, "residual_sugar"
        if component_id in COMPONENT_GROUPS["neutralization_salts"] or component_id in COMPONENT_GROUPS["dissolved_minerals"]:
            return self.parameters.soluble_salt_removal_fraction, "soluble_salt"
        if component_id in COMPONENT_GROUPS["soluble_cod_components"]:
            return self.parameters.soluble_cod_removal_fraction, "soluble_cod"
        return 0.0, "retained"

    def _run(self):
        wet_cake, wash_water = self.ins
        washed_cake, wash_filtrate = self.outs
        wash_water.empty()
        dry_cake = wet_cake.F_mass - float(wet_cake.imass["Water"])
        if self.parameters.enabled:
            wash_water.imass["Water"] = dry_cake * self.parameters.wash_water_kg_per_kg_dry_cake
        _set_conditions(wash_water, wet_cake)
        if not self.parameters.enabled:
            washed_cake.copy_like(wet_cake)
            wash_filtrate.empty()
            _set_conditions(wash_filtrate, wet_cake)
            self.removal_kg_hr = {}
            return

        washed_cake.empty()
        wash_filtrate.empty()
        self.removal_kg_hr = {}
        for component_id in chemicals.IDs:
            if component_id == "Water":
                continue
            inlet = float(wet_cake.imass[component_id])
            fraction, source = self._removal_fraction(component_id)
            removed = inlet * fraction
            washed_cake.imass[component_id] = inlet - removed
            wash_filtrate.imass[component_id] = removed
            if removed:
                self.removal_kg_hr[f"{component_id}:{source}"] = removed
        final_dry = washed_cake.F_mass
        water_available = float(wet_cake.imass["Water"]) + float(wash_water.imass["Water"])
        target_water = final_dry * self.parameters.target_cake_moisture_fraction / (
            1.0 - self.parameters.target_cake_moisture_fraction
        )
        if target_water > water_available + 1e-9:
            raise ValueError(
                "Washed-cake moisture target requires more water than the cake and wash stream provide."
            )
        washed_cake.imass["Water"] = target_water
        wash_filtrate.imass["Water"] = water_available - target_water
        _set_conditions(washed_cake, wet_cake)
        _set_conditions(wash_filtrate, wet_cake)

    def _design(self):
        wet_cake, wash_water = self.ins
        washed_cake, wash_filtrate = self.outs
        dry_entering = wet_cake.F_mass - float(wet_cake.imass["Water"])
        moisture = (
            float(washed_cake.imass["Water"]) / washed_cake.F_mass
            if washed_cake.F_mass
            else 0.0
        )
        protein_loss = sum(
            float(wash_filtrate.imass[ID])
            for ID in COMPONENT_GROUPS["protein_equivalents"]
        )
        dissolved_removed = wash_filtrate.F_mass - float(wash_filtrate.imass["Water"])
        self.design_results["Dry cake entering"] = dry_entering
        self.design_results["Wash-water ratio"] = (
            self.parameters.wash_water_kg_per_kg_dry_cake if self.parameters.enabled else 0.0
        )
        self.design_results["Wash-water flow"] = wash_water.F_mass
        self.design_results["Washed cake flow"] = washed_cake.F_mass
        self.design_results["Washed cake moisture"] = moisture
        self.design_results["Protein wash loss"] = protein_loss
        self.design_results["Dissolved solids removed"] = dissolved_removed
        self.design_results["Stage count"] = self.parameters.stage_count if self.parameters.enabled else 0
        self.power_utility.consumption = 0.0


class MechanicalDewatering(bst.Unit):
    """Raise cake solids by expressing water and dissolved solutes."""

    _N_ins = 1
    _N_outs = 2
    line = "Mechanical protein-cake dewatering"
    _units = {
        "Wet throughput": "kg/hr",
        "Inlet solids": "fraction",
        "Target solids": "fraction",
        "Achieved solids": "fraction",
        "Water removed": "kg/hr",
        "Protein loss": "kg/hr",
        "Equipment count": "-",
        "Specific electricity": "kWh/t wet",
    }

    def _init(self, parameters: DewateringParameters):
        parameters.validate()
        self.parameters = parameters
        self.entrainment_result: LiquidEntrainmentResult | None = None
        self.bypassed = False
        self.warnings: list[str] = []

    def _run(self):
        cake = self.ins[0]
        dewatered, filtrate = self.outs
        dry = cake.F_mass - float(cake.imass["Water"])
        inlet_solids = dry / cake.F_mass if cake.F_mass else 0.0
        if not cake.F_mass or inlet_solids >= self.parameters.target_solids_fraction - 1e-12:
            dewatered.copy_like(cake)
            filtrate.empty()
            _set_conditions(filtrate, cake)
            self.entrainment_result = None
            self.bypassed = True
            return

        self.bypassed = False
        dewatered.empty()
        filtrate.empty()
        fixed = 0.0
        dissolved = 0.0
        interim: dict[str, tuple[float, float, bool]] = {}
        for component_id in chemicals.IDs:
            if component_id == "Water":
                continue
            inlet = float(cake.imass[component_id])
            if component_id in COMPONENT_GROUPS["protein_equivalents"]:
                fixed_mass = inlet * self.parameters.protein_capture_fraction
            elif _component_is_suspended(component_id):
                fixed_mass = inlet
            else:
                fixed_mass = 0.0
            remaining = inlet - fixed_mass
            suspended = _component_is_suspended(component_id)
            fixed += fixed_mass
            if not suspended:
                dissolved += remaining
            interim[component_id] = fixed_mass, remaining, suspended
        target_moisture = 1.0 - self.parameters.target_solids_fraction
        self.entrainment_result = solve_liquid_entrainment_for_cake_moisture(
            fixed_cake_dry_solids_kg_hr=fixed,
            dissolved_solids_available_kg_hr=dissolved,
            water_available_kg_hr=float(cake.imass["Water"]),
            target_cake_moisture_fraction=target_moisture,
        )
        entrainment = self.entrainment_result.liquid_entrainment_fraction
        for component_id, (fixed_mass, remaining, suspended) in interim.items():
            entrained = 0.0 if suspended else remaining * entrainment
            dewatered.imass[component_id] = fixed_mass + entrained
            filtrate.imass[component_id] = remaining - entrained
        dewatered.imass["Water"] = self.entrainment_result.cake_water_kg_hr
        filtrate.imass["Water"] = float(cake.imass["Water"]) - float(dewatered.imass["Water"])
        _set_conditions(dewatered, cake)
        _set_conditions(filtrate, cake)

    def _design(self):
        cake = self.ins[0]
        dewatered, filtrate = self.outs
        inlet_dry = cake.F_mass - float(cake.imass["Water"])
        outlet_dry = dewatered.F_mass - float(dewatered.imass["Water"])
        inlet_solids = inlet_dry / cake.F_mass if cake.F_mass else 0.0
        achieved = outlet_dry / dewatered.F_mass if dewatered.F_mass else 0.0
        protein_loss = sum(
            float(filtrate.imass[ID]) for ID in COMPONENT_GROUPS["protein_equivalents"]
        )
        self.design_results["Wet throughput"] = cake.F_mass
        self.design_results["Inlet solids"] = inlet_solids
        self.design_results["Target solids"] = self.parameters.target_solids_fraction
        self.design_results["Achieved solids"] = achieved
        self.design_results["Water removed"] = float(filtrate.imass["Water"])
        self.design_results["Protein loss"] = protein_loss
        self.design_results["Equipment count"] = _equipment_count(
            cake.F_mass,
            self.parameters.capacity_kg_hr,
        )
        self.design_results["Specific electricity"] = self.parameters.electricity_kwh_per_t_wet
        self.power_utility.consumption = (
            0.0
            if self.bypassed
            else cake.F_mass / 1000.0 * self.parameters.electricity_kwh_per_t_wet
        )


class ProteinDryer(bst.Unit):
    """Utility-only-air low-temperature belt dryer with explicit exhaust losses."""

    _N_ins = 1
    _N_outs = 2
    line = "Low-temperature protein belt dryer"
    _units = {
        "Wet throughput": "kg/hr",
        "Dry matter entering": "kg/hr",
        "Product flow": "kg/hr",
        "Target product moisture": "fraction",
        "Product moisture": "fraction",
        "Evaporated water": "kg/hr",
        "Dry dust and entrainment": "kg/hr",
        "Protein degradation": "kg/hr",
        "External heat duty": "kW",
        "Specific electricity": "kWh/kg water",
        "Equipment count": "-",
        "Residence time": "min",
    }

    def _init(self, parameters: DryerParameters):
        parameters.validate()
        self.parameters = parameters
        self.mass_result: DryerMassResult | None = None
        self.energy_result: DryerEnergyResult | None = None
        self.transfers_kg_hr: dict[str, float] = {}
        self.dry_losses_kg_hr: dict[str, float] = {}
        self.warnings = [
            "Drying air is represented as a utility-only interface; air mass, humidity, and recycle are not modelled."
        ]

    def _run(self):
        cake = self.ins[0]
        product, exhaust = self.outs
        product.empty()
        exhaust.empty()
        self.dry_losses_kg_hr = {}
        for component_id in chemicals.IDs:
            if component_id == "Water":
                continue
            inlet = float(cake.imass[component_id])
            loss_fraction = self.parameters.dust_loss_fraction
            if component_id in COMPONENT_GROUPS["protein_equivalents"]:
                loss_fraction = 1.0 - (
                    (1.0 - self.parameters.dust_loss_fraction)
                    * (1.0 - self.parameters.protein_entrainment_loss_fraction)
                )
            loss = inlet * loss_fraction
            product.imass[component_id] = inlet - loss
            exhaust.imass[component_id] = loss
            if loss:
                self.dry_losses_kg_hr[component_id] = loss

        self.transfers_kg_hr = {}
        for source in ("PrecipitatedProtein", "HeatCoagulatedProtein"):
            degraded = float(product.imass[source]) * self.parameters.thermal_protein_degradation_fraction
            product.imass[source] -= degraded
            product.imass["DegradedProtein"] += degraded
            self.transfers_kg_hr[f"{source}_to_DegradedProtein"] = degraded

        retained_dry = product.F_mass
        self.mass_result = solve_dryer_mass_balance(
            inlet_dry_matter_kg_hr=retained_dry,
            inlet_water_kg_hr=float(cake.imass["Water"]),
            target_product_moisture_fraction=self.parameters.target_product_moisture_fraction,
        )
        product.imass["Water"] = self.mass_result.product_water_kg_hr
        exhaust.imass["Water"] = self.mass_result.evaporated_water_kg_hr
        product.T = self.parameters.product_outlet_temperature_C + 273.15
        product.P = cake.P
        product.phase = cake.phase
        exhaust.T = self.parameters.dryer_temperature_C + 273.15
        exhaust.P = cake.P
        exhaust.phase = cake.phase

    def _design(self):
        cake = self.ins[0]
        product, exhaust = self.outs
        effective_efficiency = self.parameters.thermal_efficiency * (
            1.0 - self.parameters.heat_loss_fraction
        )
        self.energy_result = calculate_dryer_energy(
            calculation_method=self.parameters.energy_calculation_method,
            inlet_water_kg_hr=float(cake.imass["Water"]),
            dry_solids_kg_hr=(cake.F_mass - float(cake.imass["Water"])),
            evaporated_water_kg_hr=float(exhaust.imass["Water"]),
            inlet_temperature_K=cake.T,
            product_temperature_K=product.T,
            thermal_efficiency=effective_efficiency,
            specific_heat_demand_kj_per_kg_water=self.parameters.specific_heat_demand_kj_per_kg_water,
        )
        if self.energy_result.external_heat_kj_hr:
            utility_outlet_temperature = max(
                self.parameters.dryer_temperature_C + 273.15,
                product.T,
            )
            utility_inlet_temperature = min(
                cake.T,
                utility_outlet_temperature - 1.0,
            )
            self.add_heat_utility(
                self.energy_result.external_heat_kj_hr,
                utility_inlet_temperature,
                utility_outlet_temperature,
            )
        product_moisture = float(product.imass["Water"]) / product.F_mass if product.F_mass else 0.0
        dry_loss = exhaust.F_mass - float(exhaust.imass["Water"])
        degradation = sum(self.transfers_kg_hr.values())
        self.design_results["Wet throughput"] = cake.F_mass
        self.design_results["Dry matter entering"] = cake.F_mass - float(cake.imass["Water"])
        self.design_results["Product flow"] = product.F_mass
        self.design_results["Target product moisture"] = self.parameters.target_product_moisture_fraction
        self.design_results["Product moisture"] = product_moisture
        self.design_results["Evaporated water"] = float(exhaust.imass["Water"])
        self.design_results["Dry dust and entrainment"] = dry_loss
        self.design_results["Protein degradation"] = degradation
        self.design_results["External heat duty"] = self.energy_result.external_heat_kw
        self.design_results["Specific electricity"] = self.parameters.electricity_kwh_per_kg_water_evaporated
        self.design_results["Equipment count"] = _equipment_count(
            cake.F_mass,
            self.parameters.capacity_kg_hr,
        )
        self.design_results["Residence time"] = self.parameters.residence_time_min
        self.power_utility.consumption = (
            float(exhaust.imass["Water"])
            * self.parameters.electricity_kwh_per_kg_water_evaporated
        )


class BiostimulantMembraneRecovery(bst.Unit):
    """Component-retention split and nominal membrane-area design for PR7.

    Component retentions come from the user-supplied screening matrices. Feed
    pools without a stated retention are conserved in a third, unresolved
    outlet; this permits partial mass-balanced simulation without guessing
    their fate. Optional pressure work covers idealized permeate-side pumping
    only; crossflow, pressure loss, cleaning, installed cost, and conditioning
    remain outside the unit.
    """

    _N_ins = 2
    _N_outs = 3
    line = "Biostimulant membrane screening"
    _units = {
        "Permeate flux": "L/m2/hr",
        "Membrane area": "m2",
        "Minimum membrane area": "m2",
        "Maximum membrane area": "m2",
        "Retentate flow": "kg/hr",
        "Permeate flow": "kg/hr",
        "Feed volumetric flow": "m3/hr",
        "Retentate volumetric flow": "m3/hr",
        "Permeate volumetric flow": "m3/hr",
        "Unresolved volumetric flow": "m3/hr",
        "Unresolved component mass": "kg/hr",
        "Target concentration factor": "dimensionless",
        "Actual volume concentration factor": "dimensionless",
        "Mass closure error": "kg/hr",
        "Pressure work": "kW",
        "Crossflow electricity": "kW",
        "Total electricity demand": "kW",
        "Transmembrane pressure": "bar",
        "Pump efficiency": "fraction",
        "Crossflow specific electricity": "kWh/m3 feed",
    }

    def _init(
        self,
        technology_id: str,
        flux_L_m2_h: float | None = None,
        component_retention_overrides: Mapping[str, float] | None = None,
        transmembrane_pressure_bar: float | None = None,
        pump_efficiency_fraction: float | None = None,
        crossflow_electricity_kwh_m3_feed: float | None = None,
        crossflow_electricity_source: str | None = None,
        concentration_factor: float | None = None,
        hormone_benchmark_source: str | None = None,
    ):
        from Greenhub.biostimulant_screening import FLUX_BASELINE_L_M2_H

        technology = str(technology_id).strip().upper()
        if technology not in FLUX_BASELINE_L_M2_H:
            raise ValueError("technology_id must be TUF, LNF, or MEUF.")
        selected_flux = (
            FLUX_BASELINE_L_M2_H[technology]
            if flux_L_m2_h is None else float(flux_L_m2_h)
        )
        if selected_flux <= 0.0:
            raise ValueError("flux_L_m2_h must be positive.")
        self.technology_id = technology
        self.flux_L_m2_h = selected_flux
        from Greenhub.biostimulant_screening import _parameter_value
        self.concentration_factor = (
            _parameter_value("Concentration_Factor", "Retentate")
            if concentration_factor is None else float(concentration_factor)
        )
        if not isfinite(self.concentration_factor) or self.concentration_factor <= 1.0:
            raise ValueError("PR7 concentration_factor must be finite and greater than one.")
        self.component_retention_overrides = dict(component_retention_overrides or {})
        self.hormone_benchmark_source = hormone_benchmark_source
        self.transmembrane_pressure_bar = transmembrane_pressure_bar
        self.pump_efficiency_fraction = pump_efficiency_fraction
        self.crossflow_electricity_kwh_m3_feed = crossflow_electricity_kwh_m3_feed
        self.crossflow_electricity_source = crossflow_electricity_source
        self.pressure_work_kw = 0.0
        self.crossflow_electricity_kw = 0.0
        if crossflow_electricity_kwh_m3_feed is not None and (
            not isfinite(float(crossflow_electricity_kwh_m3_feed))
            or float(crossflow_electricity_kwh_m3_feed) < 0.0
            or not str(crossflow_electricity_source or "").strip()
        ):
            raise ValueError("PR7 crossflow electricity must be non-negative and include an evidence note.")
        if crossflow_electricity_kwh_m3_feed is None and crossflow_electricity_source is not None:
            raise ValueError("PR7 crossflow electricity source requires a specific-energy value.")
        if transmembrane_pressure_bar is not None and (
            not isfinite(float(transmembrane_pressure_bar)) or float(transmembrane_pressure_bar) <= 0.0
        ):
            raise ValueError("PR7 transmembrane pressure must be finite and positive.")
        if pump_efficiency_fraction is not None and (
            not isfinite(float(pump_efficiency_fraction)) or not 0.0 < float(pump_efficiency_fraction) <= 1.0
        ):
            raise ValueError("PR7 pump efficiency must be in (0, 1].")
        if pump_efficiency_fraction is not None and transmembrane_pressure_bar is None:
            raise ValueError("PR7 pump efficiency requires transmembrane pressure.")
        self.component_split: dict[str, object] = {}
        self.component_balance: dict[str, object] = {}
        self.warnings = [
            "Membrane unit omits fermentation, unsupplied crossflow recirculation, pressure losses, CIP, installed membrane cost, and product conditioning.",
            f"Bulk water hold-up is set from target VCF={self.concentration_factor:g}; this is a volume-balance assumption, not measured membrane water rejection. Actual stream VCF is reported.",
        ]
        if technology == "MEUF":
            self.warnings.append(
                "MEUF SDS dosing and 94.5% recovery are screened separately; surfactant and acid precipitation-loop mass are not included in this BioSTEAM component balance or retentate composition."
            )
        if transmembrane_pressure_bar is None or pump_efficiency_fraction is None:
            self.warnings.append("No sourced PR7 TMP/pump-efficiency pair was supplied; membrane pumping electricity is excluded.")
        else:
            self.warnings.append("PR7 electricity is an idealized permeate-side pressure-work estimate; crossflow recirculation and auxiliary loads are excluded.")
        if crossflow_electricity_kwh_m3_feed is None:
            self.warnings.append("PR7 crossflow recirculation electricity is unresolved; no default specific energy is assumed.")
        else:
            self.warnings.append("PR7 crossflow electricity uses an explicit sourced kWh/m3 clarified-feed input and excludes optional permeate-side pressure work.")
        if hormone_benchmark_source:
            self.warnings.append(
                "PR7 includes a separate user-supplied benchmark analyte-equivalent feed at the clarified-juice boundary; it is an explicit screening correction, not measured GreenHub hormone content. Source: "
                + str(hormone_benchmark_source).strip()
            )

    def _run(self):
        from Greenhub.biostimulant_screening import (
            calculate_component_split_balance,
            split_component_flows,
        )

        feed, analyte_feed = self.ins
        retentate, permeate, unresolved = self.outs
        split = split_component_flows(
            {
                ID: float(feed.imass[ID]) + float(analyte_feed.imass[ID])
                for ID in chemicals.IDs
            },
            self.technology_id,
            flux_L_m2_h=self.flux_L_m2_h,
            component_retention_overrides=self.component_retention_overrides,
            concentration_factor=self.concentration_factor,
        )
        if not split["complete_mass_split"]:
            self.unmapped_component_ids = tuple(split["unmapped_component_ids"])
            self.warnings.append(
                "PR7 retention gate: pools without a documented class-specific membrane retention are preserved in the unresolved outlet; "
                "product/permeate allocation, VCF, membrane area and complete TEA/LCA remain unresolved: "
                + ", ".join(self.unmapped_component_ids)
            )
        else:
            self.unmapped_component_ids = ()
        if split.get("assumed_solid_phase_component_ids"):
            self.warnings.append(
                "PR7 screening assumption: unclassified solid-phase pools are fully retained by sieving; verify particulate capture, fouling, and feed clarification with membrane tests."
            )
        retentate.empty()
        permeate.empty()
        unresolved.empty()
        for ID, flow in split["retentate_kg_hr"].items():
            retentate.imass[ID] = flow
        for ID, flow in split["permeate_kg_hr"].items():
            permeate.imass[ID] = flow
        for ID, flow in split["unresolved_kg_hr"].items():
            unresolved.imass[ID] = flow
        for outlet in (retentate, permeate, unresolved):
            outlet.T = feed.T
            outlet.P = feed.P
            outlet.phase = feed.phase
        self.component_split = split
        self.component_balance = calculate_component_split_balance(
            {
                ID: float(feed.imass[ID]) + float(analyte_feed.imass[ID])
                for ID in chemicals.IDs
            },
            self.technology_id,
            flux_L_m2_h=self.flux_L_m2_h,
            component_retention_overrides=self.component_retention_overrides,
            concentration_factor=self.concentration_factor,
        )
        if self.transmembrane_pressure_bar is not None and self.pump_efficiency_fraction is not None:
            pressure_pa = float(self.transmembrane_pressure_bar) * 1e5
            permeate_m3_hr = max(0.0, float(permeate.F_vol))
            self.pressure_work_kw = (
                pressure_pa * permeate_m3_hr / 3600.0 / 1000.0
                / float(self.pump_efficiency_fraction)
            )
        if self.crossflow_electricity_kwh_m3_feed is not None:
            feed_m3_hr = float(feed.F_vol) + float(analyte_feed.F_vol)
            self.crossflow_electricity_kw = (
                float(self.crossflow_electricity_kwh_m3_feed) * feed_m3_hr
            )
        self.power_utility.consumption = self.pressure_work_kw + self.crossflow_electricity_kw

    def _design(self):
        feed, analyte_feed = self.ins
        retentate, permeate, unresolved = self.outs
        volumetric_permeate_L_hr = max(0.0, float(permeate.F_vol)) * 1000.0
        unresolved_volume_L_hr = max(0.0, float(unresolved.F_vol)) * 1000.0
        minimum_area = volumetric_permeate_L_hr / self.flux_L_m2_h
        unresolved_mass = float(unresolved.F_mass)
        maximum_area = (
            None
            if unresolved_mass > 1e-12
            else (volumetric_permeate_L_hr + unresolved_volume_L_hr) / self.flux_L_m2_h
        )
        area = None if unresolved.F_mass > 1e-12 else minimum_area
        self.design_results["Permeate flux"] = self.flux_L_m2_h
        self.design_results["Membrane area"] = area
        self.design_results["Minimum membrane area"] = minimum_area
        self.design_results["Maximum membrane area"] = maximum_area
        self.design_results["Retentate flow"] = float(retentate.F_mass)
        self.design_results["Permeate flow"] = float(permeate.F_mass)
        total_feed_volume = float(feed.F_vol) + float(analyte_feed.F_vol)
        self.design_results["Feed volumetric flow"] = total_feed_volume
        self.design_results["Retentate volumetric flow"] = float(retentate.F_vol)
        self.design_results["Permeate volumetric flow"] = float(permeate.F_vol)
        self.design_results["Unresolved volumetric flow"] = float(unresolved.F_vol)
        self.design_results["Target concentration factor"] = self.concentration_factor
        self.design_results["Actual volume concentration factor"] = (
            total_feed_volume / float(retentate.F_vol) if retentate.F_vol > 0 else None
        ) if unresolved.F_mass <= 1e-12 else None
        self.design_results["Unresolved component mass"] = float(unresolved.F_mass)
        if maximum_area is None:
            self.warnings.append(
                "PR7 upper membrane-area bound is unavailable while component fate is unresolved; pseudo-component volume estimates are not used to size membrane area. The reported minimum area covers mapped permeate only."
            )
        self.design_results["Mass closure error"] = float(
            feed.F_mass + analyte_feed.F_mass - retentate.F_mass - permeate.F_mass - unresolved.F_mass
        )
        self.design_results["Pressure work"] = (
            float(self.pressure_work_kw)
            if self.transmembrane_pressure_bar is not None and self.pump_efficiency_fraction is not None
            else None
        )
        self.design_results["Crossflow electricity"] = (
            float(self.crossflow_electricity_kw)
            if self.crossflow_electricity_kwh_m3_feed is not None else None
        )
        self.design_results["Total electricity demand"] = float(self.power_utility.consumption)
        self.design_results["Crossflow specific electricity"] = self.crossflow_electricity_kwh_m3_feed
        if self.transmembrane_pressure_bar is not None:
            self.design_results["Transmembrane pressure"] = float(self.transmembrane_pressure_bar)
        if self.pump_efficiency_fraction is not None:
            self.design_results["Pump efficiency"] = float(self.pump_efficiency_fraction)


_NEUTRALIZATION_REACTION_NAMES = {
    ("HydrochloricAcid", "SodiumHydroxide"): "hcl_naoh_neutralization",
    ("HydrochloricAcid", "CalciumHydroxide"): "hcl_calcium_hydroxide_neutralization",
    ("SulfuricAcid", "SodiumHydroxide"): "sulfuric_naoh_neutralization",
    ("SulfuricAcid", "CalciumHydroxide"): "sulfuric_calcium_hydroxide_neutralization",
}


def _reaction_definition(name: str):
    return next(definition for definition in REACTION_DEFINITIONS if definition.name == name)


class NeutralizationMixer(bst.Unit):
    """Dose commercial base and form a validated molecular salt inventory."""

    _N_ins = 2
    _N_outs = 1
    line = "Residual-liquid neutralization"
    _units = {
        "Liquid throughput": "m3/hr",
        "Residual acid entering": "kg/hr",
        "Neutralized acid": "kg/hr",
        "Pure base flow": "kg/hr",
        "Base solution flow": "kg/hr",
        "Reagent water": "kg/hr",
        "Salt generated": "kg/hr",
        "Initial pH": "-",
        "Target pH": "-",
        "Mixing time": "min",
        "Mixing volume": "m3",
        "Specific mixing power": "kW/m3",
    }

    def _init(self, parameters: NeutralizationParameters):
        parameters.validate()
        self.parameters = parameters
        self.base_demand: BaseDemandResult | None = None
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.neutralized_acid_kg_hr = 0.0
        self.salt_generated_kg_hr = 0.0
        self.inlet_pH = parameters.inlet_pH
        self.outlet_pH = parameters.target_pH
        self.warnings = [
            "Neutralized-liquid pH is metadata; electrolyte activity and buffering are not solved."
        ]

    def _run(self):
        liquid, base_solution = self.ins
        conditioned = self.outs[0]
        base_solution.empty()
        acid_mass = float(liquid.imass[self.parameters.acid_type])
        method = self.parameters.base_demand_method.casefold()
        stoichiometric = calculate_stoichiometric_base_demand(
            acid_type=self.parameters.acid_type,
            base_type=self.parameters.base_type,
            acid_kg_hr=acid_mass,
            base_solution_mass_fraction=self.parameters.base_solution_mass_fraction,
            base_purity=self.parameters.base_purity,
        )
        if method in {"stoichiometric", "acid_equivalent"}:
            pure_base = stoichiometric.pure_base_kg_hr
            solution = stoichiometric.base_solution_kg_hr
        elif method == "empirical_dose":
            if self.parameters.empirical_base_dose_kg_per_m3 is None:
                raise ValueError("Empirical base-demand mode requires base_dose_kg_per_m3.")
            volume = liquid.F_mass / self.parameters.feed_density_kg_m3
            pure_base = self.parameters.empirical_base_dose_kg_per_m3 * volume
            solution = pure_base / (
                self.parameters.base_solution_mass_fraction * self.parameters.base_purity
            ) if pure_base else 0.0
        else:
            raise ValueError(
                "base_demand_method must be 'stoichiometric', 'acid_equivalent', or 'empirical_dose'."
            )
        reagent_water = solution - pure_base
        self.base_demand = BaseDemandResult(
            stoichiometric.acid_type,
            stoichiometric.base_type,
            stoichiometric.salt_type,
            acid_mass,
            pure_base,
            solution,
            reagent_water,
        )
        base_solution.imass[self.parameters.base_type] = pure_base
        base_solution.imass["Water"] = reagent_water
        base_solution.T = self.parameters.reagent_temperature_C + 273.15
        base_solution.P = liquid.P
        base_solution.phase = "l"
        _mix_material(conditioned, self.ins)

        reaction_name = _NEUTRALIZATION_REACTION_NAMES[
            (self.parameters.acid_type, self.parameters.base_type)
        ]
        required_base = stoichiometric.pure_base_kg_hr
        conversion = min(1.0, pure_base / required_base) if required_base > 0.0 else 0.0
        before = {ID: float(conditioned.imass[ID]) for ID in chemicals.IDs}
        if conversion > 0.0:
            _reaction_definition(reaction_name).create(conversion)(conditioned)
        after = {ID: float(conditioned.imass[ID]) for ID in chemicals.IDs}
        self.reaction_delta_kg_hr = {ID: after[ID] - before[ID] for ID in chemicals.IDs}
        self.neutralized_acid_kg_hr = acid_mass * conversion
        self.salt_generated_kg_hr = max(
            0.0,
            self.reaction_delta_kg_hr.get(stoichiometric.salt_type, 0.0),
        )

    def _design(self):
        liquid = self.ins[0]
        volume = liquid.F_mass / self.parameters.feed_density_kg_m3
        mixing_volume = volume * self.parameters.mixing_time_min / 60.0
        demand = self.base_demand
        self.design_results["Liquid throughput"] = volume
        self.design_results["Residual acid entering"] = demand.acid_kg_hr if demand else 0.0
        self.design_results["Neutralized acid"] = self.neutralized_acid_kg_hr
        self.design_results["Pure base flow"] = demand.pure_base_kg_hr if demand else 0.0
        self.design_results["Base solution flow"] = demand.base_solution_kg_hr if demand else 0.0
        self.design_results["Reagent water"] = demand.reagent_water_kg_hr if demand else 0.0
        self.design_results["Salt generated"] = self.salt_generated_kg_hr
        self.design_results["Initial pH"] = self.inlet_pH
        self.design_results["Target pH"] = self.outlet_pH
        self.design_results["Mixing time"] = self.parameters.mixing_time_min
        self.design_results["Mixing volume"] = mixing_volume
        self.design_results["Specific mixing power"] = self.parameters.mixing_power_kw_per_m3
        self.power_utility.consumption = mixing_volume * self.parameters.mixing_power_kw_per_m3
