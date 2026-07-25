"""Custom BioSTEAM units for GreenHub Phase 5 anaerobic digestion.

The reactor is a steady-state staged-fate model. It preserves explicit mass,
COD, carbon, nitrogen, phosphorus, and sulfur inventories, but it is not ADM1
and does not claim full H/O atom balance for formula-free pseudo-components.
Gas-liquid separation uses documented empirical fractions because GreenHub
Henry-law and mass-transfer measurements are not yet available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import biosteam as bst

from Greenhub.analytical import calculate_analytical_indicators, calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.equilibria import (
    ammonia_equilibrium,
    inorganic_carbon_speciation,
    sulfide_speciation,
)
from Greenhub.phase5_specifications import (
    DigesterGeometryResult,
    DigesterHeatResult,
    DigesterSizingResult,
    ammonia_inhibition_factor,
    bounded_fraction,
    calculate_digester_geometry,
    calculate_digester_heat,
    calculate_digester_sizing,
    calculate_mixing_power,
    nonnegative,
    normal_volume_m3,
    pH_inhibition_factor,
    positive,
    validate_pH,
)


def _required_float(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if value is None:
        raise ValueError(f"Missing required Phase 5 parameter '{name}'.")
    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Phase 5 parameter '{name}' must be numeric.") from error


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


def _boolean(values: Mapping[str, object], name: str, default: bool) -> bool:
    value = values.get(name, default)
    if isinstance(value, str):
        text = value.strip().casefold()
        if text in {"true", "yes", "1", "on"}:
            return True
        if text in {"false", "no", "0", "off"}:
            return False
        raise ValueError(f"Phase 5 parameter '{name}' must be boolean.")
    return bool(value)


def _set_conditions(
    stream,
    source,
    *,
    temperature_k: float | None = None,
    phase: str | None = None,
) -> None:
    stream.T = source.T if temperature_k is None else temperature_k
    stream.P = source.P
    stream.phase = source.phase if phase is None else phase


def _mix_material(output, streams: Iterable[bst.Stream]) -> None:
    sources = tuple(streams)
    output.empty()
    for component_id in chemicals.IDs:
        output.imass[component_id] = sum(
            float(stream.imass[component_id]) for stream in sources
        )
    total_mass = sum(stream.F_mass for stream in sources)
    if total_mass:
        output.T = sum(stream.F_mass * stream.T for stream in sources) / total_mass
        output.P = min(stream.P for stream in sources if stream.F_mass)
        output.phase = "l"


def _stream_flows(stream) -> dict[str, float]:
    return {component_id: float(stream.imass[component_id]) for component_id in chemicals.IDs}


def _cod(flows: Mapping[str, float]) -> float:
    return sum(
        float(flow) * (COMPONENT_METADATA[component_id].cod_factor or 0.0)
        for component_id, flow in flows.items()
    )


def _element(flow: float, component_id: str, element: str) -> float:
    return float(flow) * getattr(COMPONENT_METADATA[component_id], f"{element}_mass_fraction")


@dataclass(frozen=True)
class ConditioningParameters:
    """Empirical digester-feed pH conditioning and dilution inputs."""

    enabled: bool
    method: str
    base_type: str
    base_solution_mass_fraction: float
    base_purity: float
    base_dose_kg_m3: float | None
    dilution_water_kg_per_kg_feed: float
    inlet_pH: float
    target_pH: float
    feed_density_kg_m3: float
    reagent_temperature_c: float
    mixing_time_min: float
    mixing_power_kw_m3: float

    def validate(self) -> None:
        if self.method not in {"none", "empirical_dose", "acid_equivalent"}:
            raise ValueError(
                "Digester conditioning method must be none, empirical_dose, or acid_equivalent."
            )
        if self.base_type not in {"SodiumHydroxide", "CalciumHydroxide"}:
            raise ValueError("Digester conditioning base must be SodiumHydroxide or CalciumHydroxide.")
        bounded_fraction(
            self.base_solution_mass_fraction,
            "Conditioning base solution mass fraction",
            positive_lower=True,
        )
        bounded_fraction(self.base_purity, "Conditioning base purity", positive_lower=True)
        validate_pH(self.inlet_pH, "Unconditioned digester-feed pH")
        validate_pH(self.target_pH, "Conditioned digester-feed pH")
        if self.enabled and self.target_pH < self.inlet_pH:
            raise ValueError("Base conditioning target pH cannot be below inlet pH.")
        positive(self.feed_density_kg_m3, "Conditioning feed density")
        nonnegative(
            self.dilution_water_kg_per_kg_feed,
            "Digester dilution-water ratio",
        )
        nonnegative(self.mixing_time_min, "Conditioning mixing time")
        nonnegative(self.mixing_power_kw_m3, "Conditioning mixing power")
        if self.base_dose_kg_m3 is not None:
            nonnegative(self.base_dose_kg_m3, "Conditioning base dose")
        if self.enabled and self.method == "empirical_dose" and self.base_dose_kg_m3 is None:
            raise ValueError("Empirical digester conditioning requires base_dose_kg_m3.")


@dataclass(frozen=True)
class DigestionParameters:
    """Steady-state CSTR design and staged empirical digestion inputs."""

    enabled: bool
    calculation_mode: str
    feed_density_kg_m3: float
    digester_temperature_c: float
    digester_pH: float
    hrt_days: float
    srt_days: float
    target_cod_olr_kg_m3_day: float
    target_vs_olr_kg_m3_day: float
    sizing_mode: str
    working_volume_fraction: float
    headspace_fraction: float
    maximum_single_tank_volume_m3: float | None
    height_to_diameter_ratio: float
    freeboard_m: float
    carbohydrate_biodegradable_fraction: float
    protein_biodegradable_fraction: float
    lipid_biodegradable_fraction: float
    other_cod_biodegradable_fraction: float
    cellulose_hydrolysis_fraction: float
    hemicellulose_hydrolysis_fraction: float
    starch_hydrolysis_fraction: float
    pectin_hydrolysis_fraction: float
    suspended_solids_hydrolysis_fraction: float
    protein_hydrolysis_fraction: float
    peptide_conversion_fraction: float
    amino_acid_conversion_fraction: float
    lipid_hydrolysis_fraction: float
    sugar_acidogenesis_conversion: float
    protein_acidogenesis_conversion: float
    lipid_acidogenesis_conversion: float
    other_cod_conversion: float
    acetate_conversion: float
    propionate_conversion: float
    butyrate_conversion: float
    lactate_conversion: float
    methanogenesis_conversion: float
    biodegradable_cod_fraction: float
    cod_conversion_fraction: float
    methane_yield_nm3_kg_cod_converted: float
    biomass_cod_yield_fraction: float
    organic_n_mineralization_fraction: float
    organic_p_mineralization_fraction: float
    particulate_p_release_fraction: float
    sulfate_reduction_enabled: bool
    sulfate_reduction_fraction: float
    pH_inhibition_enabled: bool
    minimum_pH: float
    optimum_pH_low: float
    optimum_pH_high: float
    maximum_pH: float
    free_ammonia_inhibition_enabled: bool
    ammonia_inhibition_constant_kg_n_m3: float | None
    heat_capacity_kj_kg_k: float
    feed_heating_efficiency: float
    ambient_temperature_c: float
    heat_loss_u_w_m2_k: float
    specific_mixing_power_kw_m3: float
    mixing_schedule_fraction: float
    motor_efficiency: float
    operating_pressure_bar: float

    def validate(self) -> None:
        if self.calculation_mode not in {
            "component_stoichiometric",
            "COD_yield",
            "hybrid",
        }:
            raise ValueError(
                "Digestion calculation mode must be component_stoichiometric, COD_yield, or hybrid."
            )
        positive(self.feed_density_kg_m3, "Digester feed density")
        if not 0.0 <= self.digester_temperature_c <= 80.0:
            raise ValueError("Digester temperature must be within 0-80 degC.")
        validate_pH(self.digester_pH, "Digester pH")
        positive(self.hrt_days, "Digester HRT")
        positive(self.srt_days, "Digester SRT")
        positive(self.target_cod_olr_kg_m3_day, "Target COD OLR")
        positive(self.target_vs_olr_kg_m3_day, "Target VS OLR")
        bounded_fraction(
            self.working_volume_fraction,
            "Digester working-volume fraction",
            positive_lower=True,
        )
        bounded_fraction(
            self.headspace_fraction,
            "Digester headspace fraction",
            open_upper=True,
        )
        positive(self.height_to_diameter_ratio, "Digester height-to-diameter ratio")
        nonnegative(self.freeboard_m, "Digester freeboard")
        fraction_fields = (
            "carbohydrate_biodegradable_fraction",
            "protein_biodegradable_fraction",
            "lipid_biodegradable_fraction",
            "other_cod_biodegradable_fraction",
            "cellulose_hydrolysis_fraction",
            "hemicellulose_hydrolysis_fraction",
            "starch_hydrolysis_fraction",
            "pectin_hydrolysis_fraction",
            "suspended_solids_hydrolysis_fraction",
            "protein_hydrolysis_fraction",
            "peptide_conversion_fraction",
            "amino_acid_conversion_fraction",
            "lipid_hydrolysis_fraction",
            "sugar_acidogenesis_conversion",
            "protein_acidogenesis_conversion",
            "lipid_acidogenesis_conversion",
            "other_cod_conversion",
            "acetate_conversion",
            "propionate_conversion",
            "butyrate_conversion",
            "lactate_conversion",
            "methanogenesis_conversion",
            "biodegradable_cod_fraction",
            "cod_conversion_fraction",
            "biomass_cod_yield_fraction",
            "organic_n_mineralization_fraction",
            "organic_p_mineralization_fraction",
            "particulate_p_release_fraction",
            "sulfate_reduction_fraction",
            "mixing_schedule_fraction",
        )
        for field_name in fraction_fields:
            bounded_fraction(getattr(self, field_name), field_name)
        nonnegative(
            self.methane_yield_nm3_kg_cod_converted,
            "COD-mode methane yield",
        )
        positive(self.heat_capacity_kj_kg_k, "Digester feed heat capacity")
        bounded_fraction(
            self.feed_heating_efficiency,
            "Feed heating efficiency",
            positive_lower=True,
        )
        nonnegative(self.heat_loss_u_w_m2_k, "Digester heat-loss U-value")
        nonnegative(self.specific_mixing_power_kw_m3, "Digester mixing power")
        bounded_fraction(self.motor_efficiency, "Mixer motor efficiency", positive_lower=True)
        positive(self.operating_pressure_bar, "Digester operating pressure")
        pH_inhibition_factor(
            self.digester_pH,
            minimum_pH=self.minimum_pH,
            optimum_pH_low=self.optimum_pH_low,
            optimum_pH_high=self.optimum_pH_high,
            maximum_pH=self.maximum_pH,
        )
        if self.free_ammonia_inhibition_enabled and self.ammonia_inhibition_constant_kg_n_m3 is None:
            raise ValueError("Enabled free-ammonia inhibition requires its inhibition constant.")


@dataclass(frozen=True)
class GasPartitionParameters:
    """Empirical Level-1 gas capture, dissolved-gas, and moisture inputs."""

    gas_capture_efficiency: float
    dissolved_methane_fraction: float
    dissolved_co2_fraction: float
    dissolved_hydrogen_fraction: float
    h2s_gas_transfer_fraction: float
    ammonia_gas_transfer_fraction: float
    raw_biogas_water_vapor_mol_fraction: float
    separator_temperature_c: float
    separator_pressure_pa: float

    def validate(self) -> None:
        for field_name in (
            "gas_capture_efficiency",
            "dissolved_methane_fraction",
            "dissolved_co2_fraction",
            "dissolved_hydrogen_fraction",
            "h2s_gas_transfer_fraction",
            "ammonia_gas_transfer_fraction",
        ):
            bounded_fraction(getattr(self, field_name), field_name)
        bounded_fraction(
            self.raw_biogas_water_vapor_mol_fraction,
            "Raw-biogas water-vapor fraction",
            open_upper=True,
        )
        if not 0.0 <= self.separator_temperature_c <= 100.0:
            raise ValueError("Gas-separator temperature must be within 0-100 degC.")
        positive(self.separator_pressure_pa, "Gas-separator pressure")


def conditioning_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    enabled: bool,
) -> ConditioningParameters:
    parameters = ConditioningParameters(
        enabled=enabled and _boolean(values, "conditioning_enabled", True),
        method=_text(values, "conditioning_method", "empirical_dose"),
        base_type=_text(values, "conditioning_base_type", "SodiumHydroxide"),
        base_solution_mass_fraction=_required_float(
            values,
            "conditioning_base_solution_mass_fraction",
        ),
        base_purity=_required_float(values, "conditioning_base_purity"),
        base_dose_kg_m3=_optional_float(values, "conditioning_base_dose_kg_m3"),
        dilution_water_kg_per_kg_feed=_required_float(
            values,
            "dilution_water_kg_per_kg_feed",
        ),
        inlet_pH=_required_float(values, "digester_feed_pH"),
        target_pH=_required_float(values, "target_digester_feed_pH"),
        feed_density_kg_m3=_required_float(values, "phase5_feed_density_kg_m3"),
        reagent_temperature_c=_required_float(values, "conditioning_reagent_temperature_c"),
        mixing_time_min=_required_float(values, "conditioning_mixing_time_min"),
        mixing_power_kw_m3=_required_float(values, "conditioning_mixing_power_kw_m3"),
    )
    parameters.validate()
    return parameters


def digestion_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    enabled: bool,
) -> DigestionParameters:
    parameters = DigestionParameters(
        enabled=enabled,
        calculation_mode=_text(values, "digestion_calculation_mode", "hybrid"),
        feed_density_kg_m3=_required_float(values, "phase5_feed_density_kg_m3"),
        digester_temperature_c=_required_float(values, "digester_temperature_c"),
        digester_pH=_required_float(values, "digester_pH"),
        hrt_days=_required_float(values, "digester_hrt_days"),
        srt_days=_required_float(values, "digester_srt_days"),
        target_cod_olr_kg_m3_day=_required_float(values, "target_cod_olr_kg_m3_day"),
        target_vs_olr_kg_m3_day=_required_float(values, "target_vs_olr_kg_m3_day"),
        sizing_mode=_text(values, "digester_sizing_mode", "maximum_required_volume"),
        working_volume_fraction=_required_float(values, "digester_working_volume_fraction"),
        headspace_fraction=_required_float(values, "digester_headspace_fraction"),
        maximum_single_tank_volume_m3=_optional_float(
            values,
            "maximum_single_digester_volume_m3",
        ),
        height_to_diameter_ratio=_required_float(values, "digester_height_to_diameter_ratio"),
        freeboard_m=_required_float(values, "digester_freeboard_m"),
        carbohydrate_biodegradable_fraction=_required_float(values, "carbohydrate_biodegradable_fraction"),
        protein_biodegradable_fraction=_required_float(values, "protein_biodegradable_fraction"),
        lipid_biodegradable_fraction=_required_float(values, "lipid_biodegradable_fraction"),
        other_cod_biodegradable_fraction=_required_float(values, "other_cod_biodegradable_fraction"),
        cellulose_hydrolysis_fraction=_required_float(values, "cellulose_hydrolysis_fraction"),
        hemicellulose_hydrolysis_fraction=_required_float(values, "hemicellulose_hydrolysis_fraction"),
        starch_hydrolysis_fraction=_required_float(values, "starch_hydrolysis_fraction"),
        pectin_hydrolysis_fraction=_required_float(values, "pectin_hydrolysis_fraction"),
        suspended_solids_hydrolysis_fraction=_required_float(values, "suspended_solids_hydrolysis_fraction"),
        protein_hydrolysis_fraction=_required_float(values, "protein_hydrolysis_fraction"),
        peptide_conversion_fraction=_required_float(values, "peptide_conversion_fraction"),
        amino_acid_conversion_fraction=_required_float(values, "amino_acid_conversion_fraction"),
        lipid_hydrolysis_fraction=_required_float(values, "lipid_hydrolysis_fraction"),
        sugar_acidogenesis_conversion=_required_float(values, "sugar_acidogenesis_conversion"),
        protein_acidogenesis_conversion=_required_float(values, "protein_acidogenesis_conversion"),
        lipid_acidogenesis_conversion=_required_float(values, "lipid_acidogenesis_conversion"),
        other_cod_conversion=_required_float(values, "other_cod_conversion"),
        acetate_conversion=_required_float(values, "acetate_conversion"),
        propionate_conversion=_required_float(values, "propionate_conversion"),
        butyrate_conversion=_required_float(values, "butyrate_conversion"),
        lactate_conversion=_required_float(values, "lactate_conversion"),
        methanogenesis_conversion=_required_float(values, "methanogenesis_conversion"),
        biodegradable_cod_fraction=_required_float(values, "biodegradable_cod_fraction"),
        cod_conversion_fraction=_required_float(values, "cod_conversion_fraction"),
        methane_yield_nm3_kg_cod_converted=_required_float(
            values,
            "methane_yield_nm3_kg_cod_converted",
        ),
        biomass_cod_yield_fraction=_required_float(values, "biomass_cod_yield_fraction"),
        organic_n_mineralization_fraction=_required_float(values, "organic_n_mineralization_fraction"),
        organic_p_mineralization_fraction=_required_float(values, "organic_p_mineralization_fraction"),
        particulate_p_release_fraction=_required_float(values, "particulate_p_release_fraction"),
        sulfate_reduction_enabled=_boolean(values, "sulfate_reduction_enabled", False),
        sulfate_reduction_fraction=_required_float(values, "sulfate_reduction_fraction"),
        pH_inhibition_enabled=_boolean(values, "pH_inhibition_enabled", True),
        minimum_pH=_required_float(values, "digester_minimum_pH"),
        optimum_pH_low=_required_float(values, "digester_optimum_pH_low"),
        optimum_pH_high=_required_float(values, "digester_optimum_pH_high"),
        maximum_pH=_required_float(values, "digester_maximum_pH"),
        free_ammonia_inhibition_enabled=_boolean(
            values,
            "free_ammonia_inhibition_enabled",
            False,
        ),
        ammonia_inhibition_constant_kg_n_m3=_optional_float(
            values,
            "ammonia_inhibition_constant_kg_n_m3",
        ),
        heat_capacity_kj_kg_k=_required_float(values, "digester_feed_heat_capacity_kj_kg_k"),
        feed_heating_efficiency=_required_float(values, "digester_feed_heating_efficiency"),
        ambient_temperature_c=_required_float(values, "ambient_temperature_c"),
        heat_loss_u_w_m2_k=_required_float(values, "digester_heat_loss_u_w_m2_k"),
        specific_mixing_power_kw_m3=_required_float(values, "specific_mixing_power_kw_m3"),
        mixing_schedule_fraction=_required_float(values, "mixing_schedule_fraction"),
        motor_efficiency=_required_float(values, "mixing_motor_efficiency"),
        operating_pressure_bar=_required_float(values, "digester_operating_pressure_bar"),
    )
    parameters.validate()
    return parameters


def gas_partition_parameters_from_mapping(values: Mapping[str, object]) -> GasPartitionParameters:
    parameters = GasPartitionParameters(
        gas_capture_efficiency=_required_float(values, "gas_capture_efficiency"),
        dissolved_methane_fraction=_required_float(values, "dissolved_methane_fraction"),
        dissolved_co2_fraction=_required_float(values, "dissolved_co2_fraction"),
        dissolved_hydrogen_fraction=_required_float(values, "dissolved_hydrogen_fraction"),
        h2s_gas_transfer_fraction=_required_float(values, "h2s_gas_transfer_fraction"),
        ammonia_gas_transfer_fraction=_required_float(values, "ammonia_gas_transfer_fraction"),
        raw_biogas_water_vapor_mol_fraction=_required_float(
            values,
            "raw_biogas_water_vapor_mol_fraction",
        ),
        separator_temperature_c=_required_float(values, "raw_biogas_temperature_c"),
        separator_pressure_pa=_required_float(values, "raw_biogas_pressure_pa"),
    )
    parameters.validate()
    return parameters


class DigesterFeedConditioner(bst.Unit):
    """Add empirical base solution and optional dilution water before digestion."""

    _N_ins = 4
    _N_outs = 1
    line = "Digester-feed conditioning"
    _units = {
        "Liquid throughput": "m3/hr",
        "Pure base flow": "kg/hr",
        "Base solution flow": "kg/hr",
        "Dilution water": "kg/hr",
        "Trace-nutrient solution": "kg/hr",
        "Inlet pH": "-",
        "Target pH": "-",
        "Mixing time": "min",
        "Mixing volume": "m3",
        "Specific mixing power": "kW/m3",
    }

    def _init(self, parameters: ConditioningParameters):
        parameters.validate()
        self.parameters = parameters
        self.pure_base_kg_hr = 0.0
        self.base_solution_kg_hr = 0.0
        self.reagent_water_kg_hr = 0.0
        self.dilution_water_kg_hr = 0.0
        self.inlet_pH = parameters.inlet_pH
        self.outlet_pH = parameters.target_pH if parameters.enabled else parameters.inlet_pH
        self.warnings = [
            "M501 pH is metadata; the empirical base dose does not solve buffering or electrolyte activity.",
            "Trace nutrients remain disabled because no deficiency-based dosing data are available.",
        ]
        self.limitation_ids = ("LIM-P5-001", "LIM-P2-002")

    def _run(self):
        feed, base_solution, dilution_water, trace_nutrients = self.ins
        conditioned = self.outs[0]
        base_solution.empty()
        dilution_water.empty()
        trace_nutrients.empty()
        self.pure_base_kg_hr = 0.0
        self.base_solution_kg_hr = 0.0
        self.reagent_water_kg_hr = 0.0
        self.dilution_water_kg_hr = 0.0
        if self.parameters.enabled and self.parameters.method == "empirical_dose":
            volume = feed.F_mass / self.parameters.feed_density_kg_m3
            self.pure_base_kg_hr = (self.parameters.base_dose_kg_m3 or 0.0) * volume
            active_fraction = (
                self.parameters.base_solution_mass_fraction * self.parameters.base_purity
            )
            self.base_solution_kg_hr = self.pure_base_kg_hr / active_fraction
            self.reagent_water_kg_hr = self.base_solution_kg_hr - self.pure_base_kg_hr
        elif self.parameters.enabled and self.parameters.method == "acid_equivalent":
            raise NotImplementedError(
                "Phase 5 acid-equivalent conditioning requires alkalinity and titration data; "
                "use empirical_dose only in explicit structural-test mode."
            )
        base_solution.imass[self.parameters.base_type] = self.pure_base_kg_hr
        base_solution.imass["Water"] = self.reagent_water_kg_hr
        base_solution.T = self.parameters.reagent_temperature_c + 273.15
        base_solution.P = feed.P
        base_solution.phase = "l"
        self.dilution_water_kg_hr = (
            feed.F_mass * self.parameters.dilution_water_kg_per_kg_feed
        )
        dilution_water.imass["Water"] = self.dilution_water_kg_hr
        dilution_water.T = feed.T
        dilution_water.P = feed.P
        dilution_water.phase = "l"
        trace_nutrients.T = feed.T
        trace_nutrients.P = feed.P
        trace_nutrients.phase = "l"
        _mix_material(conditioned, self.ins)

    def _design(self):
        feed = self.ins[0]
        conditioned = self.outs[0]
        throughput = feed.F_mass / self.parameters.feed_density_kg_m3
        mixing_volume = throughput * self.parameters.mixing_time_min / 60.0
        self.design_results["Liquid throughput"] = throughput
        self.design_results["Pure base flow"] = self.pure_base_kg_hr
        self.design_results["Base solution flow"] = self.base_solution_kg_hr
        self.design_results["Dilution water"] = self.dilution_water_kg_hr
        self.design_results["Trace-nutrient solution"] = self.ins[3].F_mass
        self.design_results["Inlet pH"] = self.inlet_pH
        self.design_results["Target pH"] = self.outlet_pH
        self.design_results["Mixing time"] = self.parameters.mixing_time_min
        self.design_results["Mixing volume"] = mixing_volume
        self.design_results["Specific mixing power"] = self.parameters.mixing_power_kw_m3
        self.power_utility.consumption = mixing_volume * self.parameters.mixing_power_kw_m3
        conditioned.P = feed.P


class AnaerobicDigester(bst.Unit):
    """Steady-state staged COD-fate CSTR with explicit nutrient mineralization."""

    _N_ins = 1
    _N_outs = 1
    line = "Anaerobic digester"
    _units = {
        "Liquid throughput": "m3/hr",
        "Feed COD": "kg O2/hr",
        "Feed VS": "kg/hr",
        "Converted substrate COD": "kg O2/hr",
        "Methane production": "kg/hr",
        "Carbon dioxide production": "kg/hr",
        "Biomass production": "kg/hr",
        "Ammonium-N generated": "kg N/hr",
        "Orthophosphate-P generated": "kg P/hr",
        "Hydrogen sulfide generated": "kg/hr",
        "Working volume": "m3",
        "Total volume": "m3",
        "Headspace volume": "m3",
        "Number of digesters": "-",
        "Actual HRT": "d",
        "Actual SRT": "d",
        "COD loading": "kg COD/m3/d",
        "VS loading": "kg VS/m3/d",
        "Gas production": "Nm3/hr",
        "Heat loss": "kW",
        "Mixing shaft power": "kW",
        "Mixing electrical power": "kW",
        "Surface area": "m2",
        "Diameter": "m",
        "Liquid height": "m",
    }

    def _init(self, parameters: DigestionParameters):
        parameters.validate()
        self.parameters = parameters
        self.component_fates: list[dict[str, float | str]] = []
        self.hydrolysis_rows: list[dict[str, float | str]] = []
        self.acidogenesis_rows: list[dict[str, float | str]] = []
        self.acetogenesis_rows: list[dict[str, float | str]] = []
        self.methanogenesis_rows: list[dict[str, float | str]] = []
        self.mineralization_rows: list[dict[str, float | str]] = []
        self.generated_kg_hr: dict[str, float] = {}
        self.consumed_kg_hr: dict[str, float] = {}
        self.nutrient_withdrawals_kg_hr: dict[str, float] = {}
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.sizing_result: DigesterSizingResult | None = None
        self.geometry_result: DigesterGeometryResult | None = None
        self.heat_result: DigesterHeatResult | None = None
        self.ammonia_speciation = None
        self.pH_factor = 1.0
        self.ammonia_factor = 1.0
        self.converted_cod_kg_hr = 0.0
        self.methane_cod_kg_hr = 0.0
        self.biomass_cod_kg_hr = 0.0
        self.residual_intermediate_cod_kg_hr = 0.0
        self.water_balance_adjustment_kg_hr = 0.0
        self.warnings = [
            "R501 is a steady-state staged empirical model, not ADM1 or a dynamic microbial model.",
            "Formula-free pseudo-components are balanced on mass, COD, C, N, P, and S; full H/O stoichiometry is not claimed.",
            "VFA and population dynamics are reported as stage ledgers rather than explicit transient intermediates.",
        ]
        self.limitation_ids = (
            "LIM-P5-002",
            "LIM-P5-003",
            "LIM-P5-004",
            "LIM-P5-005",
            "LIM-P5-006",
        )

    def _hydrolysis_and_stage_fractions(self, component_id: str) -> tuple[str, float, float, float]:
        p = self.parameters
        sugars = COMPONENT_GROUPS["soluble_sugars"] | {"EntrappedSugars"}
        proteins = COMPONENT_GROUPS["digester_protein_substrates"]
        if component_id in sugars:
            return "carbohydrate", p.carbohydrate_biodegradable_fraction, 1.0, p.sugar_acidogenesis_conversion
        if component_id in {"Cellulose"}:
            return "carbohydrate", p.carbohydrate_biodegradable_fraction, p.cellulose_hydrolysis_fraction, p.sugar_acidogenesis_conversion
        if component_id in {"Hemicellulose"}:
            return "carbohydrate", p.carbohydrate_biodegradable_fraction, p.hemicellulose_hydrolysis_fraction, p.sugar_acidogenesis_conversion
        if component_id == "Starch":
            return "carbohydrate", p.carbohydrate_biodegradable_fraction, p.starch_hydrolysis_fraction, p.sugar_acidogenesis_conversion
        if component_id == "Pectin":
            return "carbohydrate", p.carbohydrate_biodegradable_fraction, p.pectin_hydrolysis_fraction, p.sugar_acidogenesis_conversion
        if component_id in {"SuspendedSolids", "ParticulateBiodegradableOrganics"}:
            return "carbohydrate", p.carbohydrate_biodegradable_fraction, p.suspended_solids_hydrolysis_fraction, p.other_cod_conversion
        if component_id in proteins:
            if component_id == "Peptides":
                hydrolysis = p.peptide_conversion_fraction
            elif component_id == "AminoAcids":
                hydrolysis = p.amino_acid_conversion_fraction
            else:
                hydrolysis = p.protein_hydrolysis_fraction
            return "protein", p.protein_biodegradable_fraction, hydrolysis, p.protein_acidogenesis_conversion
        if component_id == "Lipids":
            return "lipid", p.lipid_biodegradable_fraction, p.lipid_hydrolysis_fraction, p.lipid_acidogenesis_conversion
        if component_id == "OtherBiodegradableOrganics":
            return "other_cod", p.other_cod_biodegradable_fraction, 1.0, p.other_cod_conversion
        if component_id in COMPONENT_GROUPS["digester_vfa_substrates"]:
            conversions = {
                "AceticAcid": p.acetate_conversion,
                "PropionicAcid": p.propionate_conversion,
                "ButyricAcid": p.butyrate_conversion,
                "LacticAcid": p.lactate_conversion,
                "FormicAcid": p.acetate_conversion,
            }
            return "vfa", 1.0, 1.0, conversions[component_id]
        return "excluded", 0.0, 0.0, 0.0

    def _withdraw_element(
        self,
        stream,
        element: str,
        required_kg_hr: float,
        component_ids: tuple[str, ...],
    ) -> float:
        remaining = max(0.0, required_kg_hr)
        withdrawn = 0.0
        for component_id in component_ids:
            fraction = getattr(
                COMPONENT_METADATA[component_id],
                f"{element}_mass_fraction",
            )
            if fraction <= 0.0 or remaining <= 1e-15:
                continue
            available_mass = float(stream.imass[component_id])
            available_element = available_mass * fraction
            take_element = min(remaining, available_element)
            take_mass = take_element / fraction
            stream.imass[component_id] -= take_mass
            self.nutrient_withdrawals_kg_hr[component_id] = (
                self.nutrient_withdrawals_kg_hr.get(component_id, 0.0) + take_mass
            )
            withdrawn += take_element
            remaining -= take_element
        if remaining > 1e-9:
            raise ValueError(
                f"Insufficient {element} inventory to support the selected biomass yield; "
                f"shortfall is {remaining:.6g} kg/hr."
            )
        return withdrawn

    def _run(self):
        feed = self.ins[0]
        broth = self.outs[0]
        broth.copy_like(feed)
        broth.T = self.parameters.digester_temperature_c + 273.15
        broth.P = self.parameters.operating_pressure_bar * 100_000.0
        broth.phase = "l"
        self.component_fates = []
        self.hydrolysis_rows = []
        self.acidogenesis_rows = []
        self.acetogenesis_rows = []
        self.methanogenesis_rows = []
        self.mineralization_rows = []
        self.generated_kg_hr = {}
        self.consumed_kg_hr = {}
        self.nutrient_withdrawals_kg_hr = {}
        self.converted_cod_kg_hr = 0.0
        self.methane_cod_kg_hr = 0.0
        self.biomass_cod_kg_hr = 0.0
        self.residual_intermediate_cod_kg_hr = 0.0
        self.water_balance_adjustment_kg_hr = 0.0
        if not self.parameters.enabled or feed.F_mass <= 0.0:
            self.reaction_delta_kg_hr = {
                component_id: 0.0 for component_id in chemicals.IDs
            }
            return

        feed_flows = _stream_flows(feed)
        feed_cod = _cod(feed_flows)
        preliminary: dict[str, tuple[str, float, float, float, float]] = {}
        available_cod = 0.0
        for component_id in COMPONENT_GROUPS["anaerobic_substrates"]:
            inlet = feed_flows.get(component_id, 0.0)
            cod_factor = COMPONENT_METADATA[component_id].cod_factor or 0.0
            category, biodegradable, hydrolysis, stage_conversion = (
                self._hydrolysis_and_stage_fractions(component_id)
            )
            accessible_fraction = biodegradable * hydrolysis
            preliminary[component_id] = (
                category,
                biodegradable,
                hydrolysis,
                stage_conversion,
                accessible_fraction,
            )
            available_cod += inlet * cod_factor * accessible_fraction

        cod_mode_scale = 1.0
        if self.parameters.calculation_mode == "COD_yield":
            target_cod = (
                feed_cod
                * self.parameters.biodegradable_cod_fraction
                * self.parameters.cod_conversion_fraction
            )
            if target_cod > available_cod + 1e-9:
                raise ValueError(
                    "COD-yield target conversion exceeds component-derived biodegradable COD."
                )
            cod_mode_scale = target_cod / available_cod if available_cod else 0.0

        consumed_carbon = 0.0
        nitrogen_budget = 0.0
        phosphorus_budget = 0.0
        sulfur_budget = 0.0
        for component_id, (
            category,
            biodegradable,
            hydrolysis,
            stage_conversion,
            accessible_fraction,
        ) in preliminary.items():
            inlet = feed_flows.get(component_id, 0.0)
            if self.parameters.calculation_mode == "COD_yield":
                total_conversion = accessible_fraction * cod_mode_scale
            else:
                total_conversion = accessible_fraction * stage_conversion
            total_conversion = min(1.0, max(0.0, total_conversion))
            consumed = inlet * total_conversion
            broth.imass[component_id] -= consumed
            self.consumed_kg_hr[component_id] = consumed
            cod_factor = COMPONENT_METADATA[component_id].cod_factor or 0.0
            cod_converted = consumed * cod_factor
            self.converted_cod_kg_hr += cod_converted
            consumed_carbon += _element(consumed, component_id, "carbon")
            nitrogen_budget += _element(consumed, component_id, "nitrogen")
            phosphorus_budget += _element(consumed, component_id, "phosphorus")
            sulfur_budget += _element(consumed, component_id, "sulfur")
            hydrolyzed = inlet * biodegradable * hydrolysis
            self.hydrolysis_rows.append(
                {
                    "component_id": component_id,
                    "category": category,
                    "inlet_kg_hr": inlet,
                    "biodegradable_fraction": biodegradable,
                    "hydrolysis_fraction": hydrolysis,
                    "hydrolyzed_or_accessible_kg_hr": hydrolyzed,
                    "method": "fixed_conversion",
                }
            )
            stage_row = {
                "component_id": component_id,
                "category": category,
                "accessible_kg_hr": hydrolyzed,
                "stage_conversion_fraction": stage_conversion,
                "ultimately_converted_kg_hr": consumed,
                "converted_cod_kg_hr": cod_converted,
            }
            if category == "vfa":
                self.acetogenesis_rows.append(stage_row)
            else:
                self.acidogenesis_rows.append(stage_row)
            self.component_fates.append(
                {
                    "component_id": component_id,
                    "category": category,
                    "inlet_kg_hr": inlet,
                    "converted_kg_hr": consumed,
                    "residual_kg_hr": inlet - consumed,
                    "converted_cod_kg_hr": cod_converted,
                }
            )

        for component_id, conversion in (
            ("OrganicNitrogen", self.parameters.organic_n_mineralization_fraction),
            ("ParticulateNitrogen", self.parameters.organic_n_mineralization_fraction),
        ):
            converted = float(broth.imass[component_id]) * conversion
            broth.imass[component_id] -= converted
            nitrogen_budget += _element(converted, component_id, "nitrogen")
            self.consumed_kg_hr[component_id] = self.consumed_kg_hr.get(component_id, 0.0) + converted
            self.mineralization_rows.append(
                {
                    "pool": component_id,
                    "element": "nitrogen",
                    "converted_pool_kg_hr": converted,
                    "conversion_fraction": conversion,
                }
            )
        for component_id, conversion in (
            ("OrganicPhosphorus", self.parameters.organic_p_mineralization_fraction),
            ("ParticulatePhosphorus", self.parameters.particulate_p_release_fraction),
        ):
            converted = float(broth.imass[component_id]) * conversion
            broth.imass[component_id] -= converted
            phosphorus_budget += _element(converted, component_id, "phosphorus")
            self.consumed_kg_hr[component_id] = self.consumed_kg_hr.get(component_id, 0.0) + converted
            self.mineralization_rows.append(
                {
                    "pool": component_id,
                    "element": "phosphorus",
                    "converted_pool_kg_hr": converted,
                    "conversion_fraction": conversion,
                }
            )
        if self.parameters.sulfate_reduction_enabled:
            converted = (
                float(broth.imass["SulfateIon"])
                * self.parameters.sulfate_reduction_fraction
            )
            broth.imass["SulfateIon"] -= converted
            sulfur_budget += _element(converted, "SulfateIon", "sulfur")
            self.consumed_kg_hr["SulfateIon"] = converted
            self.mineralization_rows.append(
                {
                    "pool": "SulfateIon",
                    "element": "sulfur",
                    "converted_pool_kg_hr": converted,
                    "conversion_fraction": self.parameters.sulfate_reduction_fraction,
                }
            )

        biomass_metadata = COMPONENT_METADATA["MicrobialBiomass"]
        biomass_cod_target = (
            self.converted_cod_kg_hr * self.parameters.biomass_cod_yield_fraction
        )
        biomass_target = biomass_cod_target / (biomass_metadata.cod_factor or 1.0)
        nutrient_sources = {
            "nitrogen": ("Ammonium", "Ammonia"),
            "phosphorus": ("Orthophosphate", "DissolvedPhosphorus"),
            "sulfur": ("SulfateIon",),
        }
        biomass_caps = [
            biomass_target,
            consumed_carbon / biomass_metadata.carbon_mass_fraction
            if biomass_metadata.carbon_mass_fraction
            else biomass_target,
        ]
        budgets = {
            "nitrogen": nitrogen_budget,
            "phosphorus": phosphorus_budget,
            "sulfur": sulfur_budget,
        }
        for element, sources in nutrient_sources.items():
            available = budgets[element] + sum(
                _element(float(broth.imass[component_id]), component_id, element)
                for component_id in sources
            )
            required_fraction = getattr(biomass_metadata, f"{element}_mass_fraction")
            if required_fraction:
                biomass_caps.append(available / required_fraction)
        biomass_mass = max(0.0, min(biomass_caps))
        for element, sources in nutrient_sources.items():
            required = biomass_mass * getattr(
                biomass_metadata,
                f"{element}_mass_fraction",
            )
            if required > budgets[element]:
                budgets[element] += self._withdraw_element(
                    broth,
                    element,
                    required - budgets[element],
                    sources,
                )
        nitrogen_budget = budgets["nitrogen"]
        phosphorus_budget = budgets["phosphorus"]
        sulfur_budget = budgets["sulfur"]
        broth.imass["MicrobialBiomass"] += biomass_mass
        self.generated_kg_hr["MicrobialBiomass"] = biomass_mass
        self.biomass_cod_kg_hr = biomass_mass * (biomass_metadata.cod_factor or 0.0)

        nitrogen_remaining = max(
            0.0,
            nitrogen_budget - biomass_mass * biomass_metadata.nitrogen_mass_fraction,
        )
        phosphorus_remaining = max(
            0.0,
            phosphorus_budget - biomass_mass * biomass_metadata.phosphorus_mass_fraction,
        )
        sulfur_remaining = max(
            0.0,
            sulfur_budget - biomass_mass * biomass_metadata.sulfur_mass_fraction,
        )
        ammonium_fraction = COMPONENT_METADATA["Ammonium"].nitrogen_mass_fraction
        phosphate_fraction = COMPONENT_METADATA["Orthophosphate"].phosphorus_mass_fraction
        sulfide_fraction = COMPONENT_METADATA["HydrogenSulfide"].sulfur_mass_fraction
        ammonium_generated = nitrogen_remaining / ammonium_fraction if nitrogen_remaining else 0.0
        phosphate_generated = phosphorus_remaining / phosphate_fraction if phosphorus_remaining else 0.0
        h2s_generated = sulfur_remaining / sulfide_fraction if sulfur_remaining else 0.0
        broth.imass["Ammonium"] += ammonium_generated
        broth.imass["Orthophosphate"] += phosphate_generated
        broth.imass["HydrogenSulfide"] += h2s_generated
        self.generated_kg_hr.update(
            Ammonium=ammonium_generated,
            Orthophosphate=phosphate_generated,
            HydrogenSulfide=h2s_generated,
        )

        h2s_cod = h2s_generated * (COMPONENT_METADATA["HydrogenSulfide"].cod_factor or 0.0)
        available_methanogenic_cod = (
            self.converted_cod_kg_hr - self.biomass_cod_kg_hr - h2s_cod
        )
        if available_methanogenic_cod < -1e-8:
            raise ValueError(
                "Selected biomass and sulfur conversions require more COD than the converted substrate provides."
            )
        available_methanogenic_cod = max(0.0, available_methanogenic_cod)
        total_tan_n = (
            float(broth.imass["Ammonium"])
            * COMPONENT_METADATA["Ammonium"].nitrogen_mass_fraction
            + float(broth.imass["Ammonia"])
            * COMPONENT_METADATA["Ammonia"].nitrogen_mass_fraction
        )
        liquid_volume = feed.F_mass / self.parameters.feed_density_kg_m3
        self.ammonia_speciation = ammonia_equilibrium(
            total_tan_n,
            self.parameters.digester_pH,
            self.parameters.digester_temperature_c + 273.15,
        )
        free_ammonia_concentration = (
            self.ammonia_speciation.ammonia_n / liquid_volume
            if liquid_volume
            else 0.0
        )
        self.pH_factor = (
            pH_inhibition_factor(
                self.parameters.digester_pH,
                minimum_pH=self.parameters.minimum_pH,
                optimum_pH_low=self.parameters.optimum_pH_low,
                optimum_pH_high=self.parameters.optimum_pH_high,
                maximum_pH=self.parameters.maximum_pH,
            )
            if self.parameters.pH_inhibition_enabled
            else 1.0
        )
        self.ammonia_factor = ammonia_inhibition_factor(
            free_ammonia_concentration,
            enabled=self.parameters.free_ammonia_inhibition_enabled,
            inhibition_constant_kg_n_m3=self.parameters.ammonia_inhibition_constant_kg_n_m3,
        )
        if self.parameters.calculation_mode == "COD_yield":
            requested_methane_nm3 = (
                self.converted_cod_kg_hr
                * self.parameters.methane_yield_nm3_kg_cod_converted
            )
            requested_methane_kmol = requested_methane_nm3 / normal_volume_m3(1.0)
            methane_mass = requested_methane_kmol * chemicals.Methane.MW
            requested_cod = methane_mass * (COMPONENT_METADATA["Methane"].cod_factor or 0.0)
            requested_cod *= self.pH_factor * self.ammonia_factor
            if requested_cod > available_methanogenic_cod + 1e-8:
                raise ValueError(
                    "COD-mode methane yield exceeds the theoretical converted-COD potential."
                )
            self.methane_cod_kg_hr = requested_cod
        else:
            self.methane_cod_kg_hr = (
                available_methanogenic_cod
                * self.parameters.methanogenesis_conversion
                * self.pH_factor
                * self.ammonia_factor
            )
        methane_cod_factor = COMPONENT_METADATA["Methane"].cod_factor or 0.0
        methane_generated = (
            self.methane_cod_kg_hr / methane_cod_factor
            if methane_cod_factor
            else 0.0
        )
        self.residual_intermediate_cod_kg_hr = max(
            0.0,
            available_methanogenic_cod - self.methane_cod_kg_hr,
        )
        residual_cod_factor = COMPONENT_METADATA["OtherBiodegradableOrganics"].cod_factor or 0.0
        residual_mass = (
            self.residual_intermediate_cod_kg_hr / residual_cod_factor
            if residual_cod_factor
            else 0.0
        )
        broth.imass["Methane"] += methane_generated
        broth.imass["OtherBiodegradableOrganics"] += residual_mass
        self.generated_kg_hr.update(
            Methane=methane_generated,
            OtherBiodegradableOrganics=residual_mass,
        )
        generated_carbon = (
            _element(biomass_mass, "MicrobialBiomass", "carbon")
            + _element(methane_generated, "Methane", "carbon")
            + _element(residual_mass, "OtherBiodegradableOrganics", "carbon")
        )
        carbon_to_co2 = consumed_carbon - generated_carbon
        if carbon_to_co2 < -1e-8:
            raise ValueError(
                "Selected COD yields create more product carbon than converted substrates contain."
            )
        co2_fraction = COMPONENT_METADATA["CarbonDioxide"].carbon_mass_fraction
        co2_generated = max(0.0, carbon_to_co2) / co2_fraction if co2_fraction else 0.0
        broth.imass["CarbonDioxide"] += co2_generated
        self.generated_kg_hr["CarbonDioxide"] = co2_generated

        previous_tan_mass = float(broth.imass["Ammonium"] + broth.imass["Ammonia"])
        broth.imass["Ammonium"] = self.ammonia_speciation.ammonium_mass
        broth.imass["Ammonia"] = self.ammonia_speciation.ammonia_mass
        new_tan_mass = float(broth.imass["Ammonium"] + broth.imass["Ammonia"])
        broth.imass["Water"] += previous_tan_mass - new_tan_mass
        mass_difference = feed.F_mass - broth.F_mass
        if float(broth.imass["Water"]) + mass_difference < -1e-9:
            raise ValueError("Empirical digestion requires more reaction water than the feed contains.")
        broth.imass["Water"] += mass_difference
        self.water_balance_adjustment_kg_hr = mass_difference + previous_tan_mass - new_tan_mass
        self.methanogenesis_rows.append(
            {
                "available_methanogenic_cod_kg_hr": available_methanogenic_cod,
                "methanogenesis_conversion": self.parameters.methanogenesis_conversion,
                "pH_factor": self.pH_factor,
                "ammonia_factor": self.ammonia_factor,
                "methane_cod_kg_hr": self.methane_cod_kg_hr,
                "methane_kg_hr": methane_generated,
                "residual_intermediate_cod_kg_hr": self.residual_intermediate_cod_kg_hr,
            }
        )
        before = feed_flows
        after = _stream_flows(broth)
        self.reaction_delta_kg_hr = {
            component_id: after[component_id] - before[component_id]
            for component_id in chemicals.IDs
        }

    def _design(self):
        feed = self.ins[0]
        broth = self.outs[0]
        flows = _stream_flows(feed)
        volume = feed.F_mass / self.parameters.feed_density_kg_m3
        indicators = calculate_analytical_indicators(
            flows,
            volumetric_flow_m3_hr=volume,
        )
        cod = float(indicators["cod_kg_hr"] or 0.0)
        vs = float(indicators["volatile_solids_kg_hr"] or 0.0)
        sizing_flow = volume if self.parameters.enabled else 0.0
        sizing_cod = cod if self.parameters.enabled else 0.0
        sizing_vs = vs if self.parameters.enabled else 0.0
        self.sizing_result = calculate_digester_sizing(
            liquid_flow_m3_hr=sizing_flow,
            cod_load_kg_hr=sizing_cod,
            vs_load_kg_hr=sizing_vs,
            hrt_days=self.parameters.hrt_days,
            target_cod_olr_kg_m3_day=self.parameters.target_cod_olr_kg_m3_day,
            target_vs_olr_kg_m3_day=self.parameters.target_vs_olr_kg_m3_day,
            sizing_mode=self.parameters.sizing_mode,
            working_volume_fraction=self.parameters.working_volume_fraction,
            headspace_fraction=self.parameters.headspace_fraction,
            maximum_single_tank_volume_m3=self.parameters.maximum_single_tank_volume_m3,
        )
        self.geometry_result = calculate_digester_geometry(
            sizing=self.sizing_result,
            height_to_diameter_ratio=self.parameters.height_to_diameter_ratio,
            freeboard_m=self.parameters.freeboard_m,
        )
        if self.sizing_result.maximum_sizing_disagreement_fraction > 0.25:
            warning = (
                "HRT, COD-OLR, and VS-OLR sizing bases differ by more than 25%; "
                "the selected sizing rule is visible and requires project reconciliation."
            )
            if warning not in self.warnings:
                self.warnings.append(warning)
        self.heat_result = calculate_digester_heat(
            feed_mass_kg_hr=feed.F_mass if self.parameters.enabled else 0.0,
            heat_capacity_kj_kg_k=self.parameters.heat_capacity_kj_kg_k,
            feed_temperature_k=feed.T,
            digester_temperature_k=self.parameters.digester_temperature_c + 273.15,
            ambient_temperature_k=self.parameters.ambient_temperature_c + 273.15,
            insulation_u_value_w_m2_k=self.parameters.heat_loss_u_w_m2_k,
            insulation_area_m2=self.geometry_result.insulation_area_m2,
            feed_heating_efficiency=self.parameters.feed_heating_efficiency,
        )
        shaft, electrical = calculate_mixing_power(
            working_volume_m3=self.sizing_result.selected_working_volume_m3,
            specific_mixing_power_kw_m3=self.parameters.specific_mixing_power_kw_m3,
            mixing_schedule_fraction=self.parameters.mixing_schedule_fraction,
            motor_efficiency=self.parameters.motor_efficiency,
        )
        if self.heat_result.vessel_heat_loss_kw > 0.0:
            self.add_heat_utility(
                self.heat_result.vessel_heat_loss_kw * 3600.0,
                self.parameters.ambient_temperature_c + 273.15,
                self.parameters.digester_temperature_c + 273.15,
            )
        gas_kmol = sum(
            float(broth.imol[component_id])
            for component_id in COMPONENT_GROUPS["biogas_components"]
        )
        self.design_results["Liquid throughput"] = volume
        self.design_results["Feed COD"] = cod
        self.design_results["Feed VS"] = vs
        self.design_results["Converted substrate COD"] = self.converted_cod_kg_hr
        self.design_results["Methane production"] = self.generated_kg_hr.get("Methane", 0.0)
        self.design_results["Carbon dioxide production"] = self.generated_kg_hr.get("CarbonDioxide", 0.0)
        self.design_results["Biomass production"] = self.generated_kg_hr.get("MicrobialBiomass", 0.0)
        self.design_results["Ammonium-N generated"] = self.generated_kg_hr.get("Ammonium", 0.0) * COMPONENT_METADATA["Ammonium"].nitrogen_mass_fraction
        self.design_results["Orthophosphate-P generated"] = self.generated_kg_hr.get("Orthophosphate", 0.0) * COMPONENT_METADATA["Orthophosphate"].phosphorus_mass_fraction
        self.design_results["Hydrogen sulfide generated"] = self.generated_kg_hr.get("HydrogenSulfide", 0.0)
        self.design_results["Working volume"] = self.sizing_result.selected_working_volume_m3
        self.design_results["Total volume"] = self.sizing_result.total_volume_m3
        self.design_results["Headspace volume"] = self.sizing_result.headspace_volume_m3
        self.design_results["Number of digesters"] = self.sizing_result.number_of_digesters
        self.design_results["Actual HRT"] = self.sizing_result.actual_hrt_days
        self.design_results["Actual SRT"] = (
            self.parameters.srt_days if self.parameters.enabled else 0.0
        )
        self.design_results["COD loading"] = self.sizing_result.actual_cod_olr_kg_m3_day
        self.design_results["VS loading"] = self.sizing_result.actual_vs_olr_kg_m3_day
        self.design_results["Gas production"] = normal_volume_m3(gas_kmol)
        self.design_results["Heat loss"] = self.heat_result.vessel_heat_loss_kw
        self.design_results["Mixing shaft power"] = shaft
        self.design_results["Mixing electrical power"] = electrical
        self.design_results["Surface area"] = self.geometry_result.surface_area_m2
        self.design_results["Diameter"] = self.geometry_result.diameter_m
        self.design_results["Liquid height"] = self.geometry_result.liquid_height_m
        self.power_utility.consumption = electrical


class BiogasDisengagement(bst.Unit):
    """Partition produced gases into raw gas, digestate, and uncaptured gas."""

    _N_ins = 1
    _N_outs = 3
    line = "Raw-biogas disengagement"
    _units = {
        "Wet raw biogas": "Nm3/hr",
        "Dry raw biogas": "Nm3/hr",
        "Methane in raw biogas": "Nm3/hr",
        "Methane in digestate": "kg/hr",
        "Uncaptured methane": "kg/hr",
        "Methane dry fraction": "mol fraction",
        "Carbon dioxide dry fraction": "mol fraction",
        "Hydrogen sulfide": "ppmv dry",
        "Ammonia": "ppmv dry",
        "Water vapor": "mol fraction wet",
        "Gas capture efficiency": "fraction",
    }

    def _init(self, parameters: GasPartitionParameters, *, digester_pH: float):
        parameters.validate()
        self.parameters = parameters
        self.digester_pH = validate_pH(digester_pH, "Digester pH")
        self.partition_rows: list[dict[str, float | str]] = []
        self.inorganic_carbon_fractions: dict[str, float] = {}
        self.sulfide_fractions: dict[str, float] = {}
        self.warnings = [
            "V501 uses empirical Level-1 gas partitioning; Henry-law and kLa calculations are not active.",
            "Dissolved H2S/HS-/S-2 are carried by one HydrogenSulfide component; speciation is reporting metadata.",
            "Raw-biogas moisture is a specified wet-mole fraction, not a saturation calculation.",
        ]
        self.limitation_ids = ("LIM-P5-007", "LIM-P5-008", "LIM-P5-009")

    def _run(self):
        broth = self.ins[0]
        raw_biogas, digestate, uncaptured = self.outs
        raw_biogas.empty()
        digestate.copy_like(broth)
        uncaptured.empty()
        temperature_k = self.parameters.separator_temperature_c + 273.15
        self.inorganic_carbon_fractions = inorganic_carbon_speciation(
            self.digester_pH,
            temperature_k,
        )
        self.sulfide_fractions = sulfide_speciation(self.digester_pH, temperature_k)
        dissolved_fractions = {
            "Methane": self.parameters.dissolved_methane_fraction,
            "CarbonDioxide": self.parameters.dissolved_co2_fraction,
            "Hydrogen": self.parameters.dissolved_hydrogen_fraction,
            "HydrogenSulfide": 1.0
            - self.parameters.h2s_gas_transfer_fraction
            * self.sulfide_fractions["H2S"],
            "Ammonia": 1.0 - self.parameters.ammonia_gas_transfer_fraction,
            "Nitrogen": 0.0,
            "Oxygen": 0.0,
        }
        self.partition_rows = []
        for component_id, dissolved_fraction in dissolved_fractions.items():
            total = float(broth.imass[component_id])
            dissolved = total * dissolved_fraction
            releasable = total - dissolved
            captured = releasable * self.parameters.gas_capture_efficiency
            loss = releasable - captured
            digestate.imass[component_id] = dissolved
            raw_biogas.imass[component_id] = captured
            uncaptured.imass[component_id] = loss
            self.partition_rows.append(
                {
                    "component_id": component_id,
                    "produced_or_entering_kg_hr": total,
                    "dissolved_fraction": dissolved_fraction,
                    "raw_biogas_kg_hr": captured,
                    "digestate_kg_hr": dissolved,
                    "uncaptured_kg_hr": loss,
                }
            )
        dry_gas_kmol = sum(
            float(raw_biogas.imol[component_id])
            for component_id in dissolved_fractions
        )
        moisture = self.parameters.raw_biogas_water_vapor_mol_fraction
        water_kmol = dry_gas_kmol * moisture / (1.0 - moisture) if dry_gas_kmol else 0.0
        water_mass = water_kmol * chemicals.Water.MW
        if water_mass > float(digestate.imass["Water"]) + 1e-9:
            raise ValueError("Raw-biogas moisture requires more water than digestate contains.")
        digestate.imass["Water"] -= water_mass
        raw_biogas.imass["Water"] = water_mass
        for stream, phase in (
            (raw_biogas, "g"),
            (digestate, "l"),
            (uncaptured, "g"),
        ):
            stream.T = temperature_k
            stream.P = self.parameters.separator_pressure_pa
            stream.phase = phase

    def _design(self):
        raw_biogas, digestate, uncaptured = self.outs
        dry_ids = tuple(COMPONENT_GROUPS["biogas_components"])
        dry_kmol = sum(float(raw_biogas.imol[component_id]) for component_id in dry_ids)
        wet_kmol = dry_kmol + float(raw_biogas.imol["Water"])
        methane_kmol = float(raw_biogas.imol["Methane"])
        co2_kmol = float(raw_biogas.imol["CarbonDioxide"])
        h2s_kmol = float(raw_biogas.imol["HydrogenSulfide"])
        ammonia_kmol = float(raw_biogas.imol["Ammonia"])
        self.design_results["Wet raw biogas"] = normal_volume_m3(wet_kmol)
        self.design_results["Dry raw biogas"] = normal_volume_m3(dry_kmol)
        self.design_results["Methane in raw biogas"] = normal_volume_m3(methane_kmol)
        self.design_results["Methane in digestate"] = float(digestate.imass["Methane"])
        self.design_results["Uncaptured methane"] = float(uncaptured.imass["Methane"])
        self.design_results["Methane dry fraction"] = methane_kmol / dry_kmol if dry_kmol else 0.0
        self.design_results["Carbon dioxide dry fraction"] = co2_kmol / dry_kmol if dry_kmol else 0.0
        self.design_results["Hydrogen sulfide"] = h2s_kmol / dry_kmol * 1e6 if dry_kmol else 0.0
        self.design_results["Ammonia"] = ammonia_kmol / dry_kmol * 1e6 if dry_kmol else 0.0
        self.design_results["Water vapor"] = (
            float(raw_biogas.imol["Water"]) / wet_kmol if wet_kmol else 0.0
        )
        self.design_results["Gas capture efficiency"] = self.parameters.gas_capture_efficiency
        self.power_utility.consumption = 0.0
