"""BioSTEAM units for Phase 7 digestate processing and nutrient recovery."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable, Mapping

import biosteam as bst

from Greenhub.analytical import calculate_elemental_flows
from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.phase5_specifications import NORMAL_M3_PER_KMOL
from Greenhub.phase7_specifications import (
    acid_capture_extent,
    ammonia_stripping_fraction,
    bounded_fraction,
    calcium_phosphate_extent,
    gas_mover_power_kw,
    ion_exchange_design,
    membrane_water_recovery,
    nonnegative,
    packed_column_diameter_m,
    positive,
    solve_liquid_entrainment,
    struvite_extent,
)


def _required_float(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if value is None or isinstance(value, bool):
        raise ValueError(f"Required Phase 7 parameter '{name}' is missing or non-numeric.")
    return float(value)


def _required_text(values: Mapping[str, object], name: str) -> str:
    value = values.get(name)
    if value is None or isinstance(value, bool) or not str(value).strip():
        raise ValueError(f"Required Phase 7 parameter '{name}' is missing or blank.")
    return str(value).strip()


def _required_bool(values: Mapping[str, object], name: str) -> bool:
    value = values.get(name)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str) and value.strip().casefold() in {"true", "false", "yes", "no", "1", "0"}:
        return value.strip().casefold() in {"true", "yes", "1"}
    raise ValueError(f"Required Phase 7 boolean parameter '{name}' is missing or invalid.")


def _sum_streams(streams: Iterable[bst.Stream]) -> dict[str, float]:
    return {
        component_id: sum(float(stream.imass[component_id]) for stream in streams)
        for component_id in chemicals.IDs
    }


def _mix_into(output: bst.Stream, streams: Iterable[bst.Stream]) -> None:
    streams = tuple(streams)
    output.empty()
    for component_id, flow in _sum_streams(streams).items():
        output.imass[component_id] = flow
    material = [stream for stream in streams if stream.F_mass > 0.0]
    if material:
        output.T = sum(stream.T * stream.F_mass for stream in material) / sum(
            stream.F_mass for stream in material
        )
        output.P = min(stream.P for stream in material)


def _set_reaction_delta(unit: bst.Unit) -> None:
    before = _sum_streams(unit.ins)
    after = _sum_streams(unit.outs)
    delta = {
        component_id: after[component_id] - before[component_id]
        for component_id in chemicals.IDs
        if abs(after[component_id] - before[component_id]) > 1e-14
    }
    unit.reaction_delta_kg_hr = delta
    unit.reaction_mass_residual_kg_hr = sum(delta.values())
    before_elements = calculate_elemental_flows(before)
    after_elements = calculate_elemental_flows(after)
    unit.reaction_element_residuals_kg_hr = {
        element: after_elements[element] - before_elements[element]
        for element in before_elements
    }


def _solution(stream: bst.Stream, component_id: str, pure_mass_kg_hr: float, mass_fraction: float) -> None:
    stream.empty()
    pure = nonnegative(pure_mass_kg_hr, f"{component_id} demand")
    fraction = bounded_fraction(mass_fraction, f"{component_id} solution mass fraction")
    if pure and fraction <= 0.0:
        raise ValueError(f"{component_id} solution mass fraction must be above zero.")
    stream.imass[component_id] = pure
    stream.imass["Water"] = pure * (1.0 / fraction - 1.0) if pure else 0.0
    stream.phase = "l"


def _dissolve_base(stream: bst.Stream, base_id: str, efficiency: float = 1.0) -> float:
    """Convert a molecular base to explicit ions and return OH kmol formed."""

    efficiency = bounded_fraction(efficiency, "Base dissolution efficiency")
    available = float(stream.imol[base_id])
    reacted = available * efficiency
    if reacted <= 0.0:
        return 0.0
    stream.imol[base_id] -= reacted
    if base_id == "SodiumHydroxide":
        stream.imol["SodiumIon"] += reacted
        stream.imol["HydroxideIon"] += reacted
        return reacted
    if base_id == "PotassiumHydroxide":
        stream.imol["PotassiumIon"] += reacted
        stream.imol["HydroxideIon"] += reacted
        return reacted
    if base_id == "CalciumHydroxide":
        stream.imol["CalciumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
        return 2.0 * reacted
    if base_id == "MagnesiumHydroxide":
        stream.imol["MagnesiumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
        return 2.0 * reacted
    if base_id == "MagnesiumOxide":
        if float(stream.imol["Water"]) + 1e-12 < reacted:
            reacted = float(stream.imol["Water"])
        stream.imol[base_id] = available - reacted
        stream.imol["Water"] -= reacted
        stream.imol["MagnesiumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
        return 2.0 * reacted
    raise ValueError(f"Unsupported Phase 7 base '{base_id}'.")


def _dissolve_magnesium(stream: bst.Stream, source_id: str, efficiency: float) -> float:
    efficiency = bounded_fraction(efficiency, "Magnesium dissolution efficiency")
    available = float(stream.imol[source_id])
    reacted = available * efficiency
    if reacted <= 0.0:
        return 0.0
    stream.imol[source_id] -= reacted
    if source_id == "MagnesiumChloride":
        stream.imol["MagnesiumIon"] += reacted
        stream.imol["ChlorideIon"] += 2.0 * reacted
    elif source_id == "MagnesiumSulfate":
        stream.imol["MagnesiumIon"] += reacted
        stream.imol["SulfateIon"] += reacted
    elif source_id == "MagnesiumHydroxide":
        stream.imol["MagnesiumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
    elif source_id == "MagnesiumOxide":
        reacted = min(reacted, float(stream.imol["Water"]))
        stream.imol[source_id] = available - reacted
        stream.imol["Water"] -= reacted
        stream.imol["MagnesiumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
    else:
        raise ValueError(f"Unsupported magnesium source '{source_id}'.")
    return reacted


def _dissolve_calcium(stream: bst.Stream, source_id: str, efficiency: float) -> float:
    efficiency = bounded_fraction(efficiency, "Calcium dissolution efficiency")
    available = float(stream.imol[source_id])
    reacted = available * efficiency
    if reacted <= 0.0:
        return 0.0
    stream.imol[source_id] -= reacted
    if source_id == "CalciumChloride":
        stream.imol["CalciumIon"] += reacted
        stream.imol["ChlorideIon"] += 2.0 * reacted
    elif source_id == "CalciumHydroxide":
        stream.imol["CalciumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
    elif source_id == "CalciumOxide":
        reacted = min(reacted, float(stream.imol["Water"]))
        stream.imol[source_id] = available - reacted
        stream.imol["Water"] -= reacted
        stream.imol["CalciumIon"] += reacted
        stream.imol["HydroxideIon"] += 2.0 * reacted
    else:
        raise ValueError(f"Unsupported calcium source '{source_id}'.")
    return reacted


@dataclass(frozen=True)
class EqualizationParameters:
    enabled: bool
    density_kg_m3: float
    residence_time_h: float
    working_fraction: float
    mixing_power_kw_m3: float
    motor_efficiency: float
    height_to_diameter_ratio: float
    ambient_temperature_c: float
    heat_transfer_coefficient_w_m2_k: float
    methane_release_fraction: float
    carbon_dioxide_release_fraction: float
    ammonia_release_fraction: float
    hydrogen_sulfide_release_fraction: float


@dataclass(frozen=True)
class DigestateSeparationParameters:
    technology: str
    density_kg_m3: float
    cake_moisture_fraction: float
    particulate_capture_fraction: float
    biomass_capture_fraction: float
    particulate_p_capture_fraction: float
    inert_capture_fraction: float
    contaminant_capture_fraction: float
    electricity_kwh_m3: float


@dataclass(frozen=True)
class StruviteParameters:
    density_kg_m3: float
    target_pH: float
    magnesium_source: str
    magnesium_solution_mass_fraction: float
    magnesium_to_p_molar_ratio: float
    magnesium_dissolution_efficiency: float
    phosphate_recovery_fraction: float
    ammonium_availability_fraction: float
    residence_time_min: float
    mixing_power_kw_m3: float
    base_type: str
    base_solution_mass_fraction: float
    base_dose_kg_m3: float
    calcium_phosphate_competition_fraction: float
    magnesium_hydroxide_fraction: float
    calcium_carbonate_fraction: float
    seed_kg_per_kg_p: float


@dataclass(frozen=True)
class CalciumRecoveryParameters:
    density_kg_m3: float
    target_pH: float
    product_id: str
    calcium_source: str
    calcium_solution_mass_fraction: float
    calcium_to_p_molar_ratio: float
    calcium_dissolution_efficiency: float
    phosphate_recovery_fraction: float
    residence_time_min: float
    mixing_power_kw_m3: float
    base_type: str
    base_solution_mass_fraction: float
    base_dose_kg_m3: float
    calcium_carbonate_fraction: float


@dataclass(frozen=True)
class CrystalSeparationParameters:
    target_product_ids: tuple[str, ...]
    product_capture_fraction: float
    impurity_capture_fraction: float
    product_moisture_fraction: float
    electricity_kwh_kg_dry_product: float


@dataclass(frozen=True)
class StrippingParameters:
    density_kg_m3: float
    pH: float
    temperature_c: float
    pressure_pa: float
    medium: str
    gas_to_liquid_ratio_nm3_m3: float
    steam_kg_kg_liquid: float
    packing_height_m: float
    superficial_velocity_m_s: float
    transfer_coefficient: float
    pressure_drop_pa: float
    gas_mover_efficiency: float
    co2_removal_fraction: float
    water_evaporation_fraction: float
    steam_latent_heat_kj_kg: float


@dataclass(frozen=True)
class AcidAbsorptionParameters:
    acid_id: str
    acid_solution_mass_fraction: float
    acid_excess_fraction: float
    absorber_efficiency: float
    water_makeup_kg_per_kg_nh3: float
    co2_absorption_fraction: float
    neutralization_heat_kj_mol_nh3: float
    pressure_drop_pa: float


@dataclass(frozen=True)
class IonExchangeParameters:
    recovery_fraction: float
    capacity_kg_nh4_per_kg_media: float
    breakthrough_fraction: float
    service_time_h: float
    bed_bulk_density_kg_m3: float
    nacl_molar_ratio: float
    brine_mass_fraction: float
    rinse_water_kg_per_kg_media: float
    pressure_drop_pa: float
    pump_efficiency: float


@dataclass(frozen=True)
class PotassiumConcentrationParameters:
    method: str
    density_kg_m3: float
    evaporation_water_removal_fraction: float
    evaporation_temperature_c: float
    latent_heat_kj_kg: float
    thermal_efficiency: float
    evaporator_electricity_kwh_kg_water: float
    membrane_pressure_bar: float
    membrane_osmotic_pressure_bar: float
    membrane_reference_net_pressure_bar: float
    membrane_reference_water_recovery_fraction: float
    membrane_water_flux_l_m2_hr: float
    potassium_rejection_fraction: float
    monovalent_rejection_fraction: float
    divalent_rejection_fraction: float
    organic_rejection_fraction: float
    contaminant_rejection_fraction: float
    membrane_electricity_kwh_m3_permeate: float
    cleaning_water_kg_m2_hr: float


@dataclass(frozen=True)
class ProductFinishingParameters:
    washing_enabled: bool
    wash_water_kg_per_kg_dry_product: float
    wash_impurity_removal_fraction: float
    wash_product_loss_fraction: float
    wash_electricity_kwh_kg_product: float
    drying_enabled: bool
    target_moisture_fraction: float
    drying_temperature_c: float
    stability_limit_c: float
    heat_capacity_kj_kg_k: float
    latent_heat_kj_kg: float
    thermal_efficiency: float
    fan_electricity_kwh_kg_water: float


def equalization_parameters_from_mapping(values: Mapping[str, object]) -> EqualizationParameters:
    return EqualizationParameters(
        _required_bool(values, "digestate_equalization_enabled"),
        positive(_required_float(values, "phase7_digestate_density_kg_m3"), "Digestate density"),
        nonnegative(_required_float(values, "equalization_residence_time_h"), "Equalization residence time"),
        bounded_fraction(_required_float(values, "equalization_working_fraction"), "Equalization working fraction"),
        nonnegative(_required_float(values, "equalization_mixing_power_kw_m3"), "Equalization mixing power"),
        bounded_fraction(_required_float(values, "phase7_motor_efficiency"), "Phase 7 motor efficiency"),
        positive(_required_float(values, "equalization_height_to_diameter_ratio"), "Equalization H:D ratio"),
        _required_float(values, "equalization_ambient_temperature_c"),
        nonnegative(
            _required_float(values, "equalization_heat_transfer_coefficient_w_m2_k"),
            "Equalization heat-transfer coefficient",
        ),
        bounded_fraction(_required_float(values, "equalization_methane_release_fraction"), "Equalization methane release"),
        bounded_fraction(_required_float(values, "equalization_co2_release_fraction"), "Equalization CO2 release"),
        bounded_fraction(_required_float(values, "equalization_ammonia_release_fraction"), "Equalization ammonia release"),
        bounded_fraction(_required_float(values, "equalization_h2s_release_fraction"), "Equalization H2S release"),
    )


def separation_parameters_from_mapping(values: Mapping[str, object]) -> DigestateSeparationParameters:
    technology = _required_text(values, "digestate_separator_technology").casefold().replace(" ", "_")
    supported = {"screw_press", "decanter_centrifuge", "belt_filter"}
    if technology not in supported:
        raise ValueError(
            "Digestate separator technology must be one of: "
            + ", ".join(sorted(supported))
            + f"; received '{technology}'."
        )
    return DigestateSeparationParameters(
        technology,
        positive(_required_float(values, "phase7_digestate_density_kg_m3"), "Digestate density"),
        bounded_fraction(_required_float(values, "digestate_cake_moisture_fraction"), "Cake moisture"),
        bounded_fraction(_required_float(values, "digestate_particulate_capture_fraction"), "Particulate capture"),
        bounded_fraction(_required_float(values, "digestate_biomass_capture_fraction"), "Biomass capture"),
        bounded_fraction(_required_float(values, "digestate_particulate_p_capture_fraction"), "Particulate-P capture"),
        bounded_fraction(_required_float(values, "digestate_inert_capture_fraction"), "Inert capture"),
        bounded_fraction(_required_float(values, "digestate_contaminant_capture_fraction"), "Contaminant capture"),
        nonnegative(_required_float(values, "digestate_separator_electricity_kwh_m3"), "Separator electricity"),
    )


def struvite_parameters_from_mapping(values: Mapping[str, object]) -> StruviteParameters:
    return StruviteParameters(
        positive(_required_float(values, "phase7_digestate_density_kg_m3"), "Digestate density"),
        _required_float(values, "struvite_target_pH"),
        _required_text(values, "struvite_magnesium_source"),
        bounded_fraction(_required_float(values, "struvite_magnesium_solution_mass_fraction"), "Mg solution fraction"),
        positive(_required_float(values, "struvite_magnesium_to_p_molar_ratio"), "Mg:P ratio"),
        bounded_fraction(_required_float(values, "struvite_magnesium_dissolution_efficiency"), "Mg dissolution"),
        bounded_fraction(_required_float(values, "struvite_phosphate_recovery_fraction"), "Struvite P recovery"),
        bounded_fraction(_required_float(values, "struvite_ammonium_availability_fraction"), "Struvite ammonium availability"),
        nonnegative(_required_float(values, "struvite_residence_time_min"), "Struvite residence time"),
        nonnegative(_required_float(values, "struvite_mixing_power_kw_m3"), "Struvite mixing power"),
        _required_text(values, "struvite_base_type"),
        bounded_fraction(_required_float(values, "struvite_base_solution_mass_fraction"), "Struvite base fraction"),
        nonnegative(_required_float(values, "struvite_base_dose_kg_m3"), "Struvite base dose"),
        bounded_fraction(_required_float(values, "struvite_calcium_phosphate_competition_fraction"), "Ca-P competition"),
        bounded_fraction(_required_float(values, "struvite_magnesium_hydroxide_fraction"), "Mg hydroxide fraction"),
        bounded_fraction(_required_float(values, "struvite_calcium_carbonate_fraction"), "Ca carbonate fraction"),
        nonnegative(_required_float(values, "struvite_seed_kg_per_kg_p"), "Struvite seed dose"),
    )


def calcium_parameters_from_mapping(values: Mapping[str, object]) -> CalciumRecoveryParameters:
    return CalciumRecoveryParameters(
        positive(_required_float(values, "phase7_digestate_density_kg_m3"), "Digestate density"),
        _required_float(values, "calcium_phosphate_target_pH"),
        _required_text(values, "calcium_phosphate_product_id"),
        _required_text(values, "calcium_phosphate_calcium_source"),
        bounded_fraction(_required_float(values, "calcium_phosphate_solution_mass_fraction"), "Calcium solution fraction"),
        positive(_required_float(values, "calcium_phosphate_ca_to_p_molar_ratio"), "Ca:P ratio"),
        bounded_fraction(_required_float(values, "calcium_phosphate_dissolution_efficiency"), "Calcium dissolution"),
        bounded_fraction(_required_float(values, "calcium_phosphate_recovery_fraction"), "Calcium-P recovery"),
        nonnegative(_required_float(values, "calcium_phosphate_residence_time_min"), "Calcium-P residence time"),
        nonnegative(_required_float(values, "calcium_phosphate_mixing_power_kw_m3"), "Calcium-P mixing power"),
        _required_text(values, "calcium_phosphate_base_type"),
        bounded_fraction(_required_float(values, "calcium_phosphate_base_solution_mass_fraction"), "Calcium-P base fraction"),
        nonnegative(_required_float(values, "calcium_phosphate_base_dose_kg_m3"), "Calcium-P base dose"),
        bounded_fraction(_required_float(values, "calcium_phosphate_carbonate_fraction"), "Calcium carbonate fraction"),
    )


def crystal_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    route: str,
) -> CrystalSeparationParameters:
    prefix = "struvite" if route == "struvite" else "calcium_phosphate"
    products = ("Struvite",) if route == "struvite" else (
        "CalciumPhosphate", "DicalciumPhosphate", "Hydroxyapatite"
    )
    return CrystalSeparationParameters(
        products,
        bounded_fraction(_required_float(values, f"{prefix}_crystal_capture_fraction"), "Crystal capture"),
        bounded_fraction(_required_float(values, f"{prefix}_impurity_capture_fraction"), "Impurity capture"),
        bounded_fraction(_required_float(values, f"{prefix}_product_moisture_fraction"), "Product moisture"),
        nonnegative(_required_float(values, f"{prefix}_separator_electricity_kwh_kg"), "Crystal separator electricity"),
    )


def stripping_parameters_from_mapping(values: Mapping[str, object]) -> StrippingParameters:
    return StrippingParameters(
        positive(_required_float(values, "phase7_digestate_density_kg_m3"), "Digestate density"),
        _required_float(values, "ammonia_stripper_pH"),
        _required_float(values, "ammonia_stripper_temperature_c"),
        positive(_required_float(values, "ammonia_stripper_pressure_bar"), "Stripper pressure") * 1e5,
        _required_text(values, "ammonia_stripping_medium").casefold(),
        nonnegative(_required_float(values, "ammonia_gas_to_liquid_ratio_nm3_m3"), "Gas-to-liquid ratio"),
        nonnegative(_required_float(values, "ammonia_steam_kg_kg_liquid"), "Steam ratio"),
        nonnegative(_required_float(values, "ammonia_packing_height_m"), "Packing height"),
        positive(_required_float(values, "ammonia_superficial_velocity_m_s"), "Superficial velocity"),
        nonnegative(_required_float(values, "ammonia_transfer_coefficient"), "Transfer coefficient"),
        nonnegative(_required_float(values, "ammonia_stripper_pressure_drop_pa"), "Stripper pressure drop"),
        bounded_fraction(_required_float(values, "ammonia_gas_mover_efficiency"), "Gas-mover efficiency"),
        bounded_fraction(_required_float(values, "ammonia_co2_removal_fraction"), "CO2 removal"),
        bounded_fraction(_required_float(values, "ammonia_water_evaporation_fraction"), "Water evaporation"),
        positive(_required_float(values, "ammonia_steam_latent_heat_kj_kg"), "Steam latent heat"),
    )


def acid_parameters_from_mapping(values: Mapping[str, object]) -> AcidAbsorptionParameters:
    return AcidAbsorptionParameters(
        _required_text(values, "ammonia_absorber_acid_type"),
        bounded_fraction(_required_float(values, "ammonia_absorber_acid_solution_mass_fraction"), "Acid solution fraction"),
        nonnegative(_required_float(values, "ammonia_absorber_acid_excess_fraction"), "Acid excess"),
        bounded_fraction(_required_float(values, "ammonia_absorber_capture_efficiency"), "Absorber capture"),
        nonnegative(_required_float(values, "ammonia_absorber_water_kg_per_kg_nh3"), "Absorber water"),
        bounded_fraction(_required_float(values, "ammonia_absorber_co2_absorption_fraction"), "CO2 absorption"),
        nonnegative(_required_float(values, "ammonia_neutralization_heat_kj_mol"), "Neutralization heat"),
        nonnegative(_required_float(values, "ammonia_absorber_pressure_drop_pa"), "Absorber pressure drop"),
    )


def ion_exchange_parameters_from_mapping(values: Mapping[str, object]) -> IonExchangeParameters:
    return IonExchangeParameters(
        bounded_fraction(_required_float(values, "ion_exchange_ammonium_recovery_fraction"), "Ion exchange recovery"),
        positive(_required_float(values, "ion_exchange_capacity_kg_nh4_kg_media"), "Ion exchange capacity"),
        bounded_fraction(_required_float(values, "ion_exchange_breakthrough_fraction"), "Breakthrough fraction"),
        positive(_required_float(values, "ion_exchange_service_time_h"), "Service time"),
        positive(_required_float(values, "ion_exchange_bed_density_kg_m3"), "Bed density"),
        positive(_required_float(values, "ion_exchange_nacl_molar_ratio"), "NaCl ratio"),
        bounded_fraction(_required_float(values, "ion_exchange_brine_mass_fraction"), "Brine mass fraction"),
        nonnegative(_required_float(values, "ion_exchange_rinse_water_kg_kg_media"), "Rinse water"),
        nonnegative(_required_float(values, "ion_exchange_pressure_drop_pa"), "Ion exchange pressure drop"),
        bounded_fraction(_required_float(values, "phase7_pump_efficiency"), "Pump efficiency"),
    )


def potassium_parameters_from_mapping(values: Mapping[str, object]) -> PotassiumConcentrationParameters:
    return PotassiumConcentrationParameters(
        _required_text(values, "potassium_concentration_method").casefold(),
        positive(_required_float(values, "phase7_digestate_density_kg_m3"), "Digestate density"),
        bounded_fraction(_required_float(values, "potassium_evaporation_water_removal_fraction"), "Evaporation water removal"),
        _required_float(values, "potassium_evaporation_temperature_c"),
        positive(_required_float(values, "potassium_evaporation_latent_heat_kj_kg"), "Evaporation latent heat"),
        bounded_fraction(_required_float(values, "potassium_evaporation_thermal_efficiency"), "Evaporation efficiency"),
        nonnegative(_required_float(values, "potassium_evaporator_electricity_kwh_kg_water"), "Evaporator electricity"),
        positive(_required_float(values, "potassium_membrane_pressure_bar"), "Membrane pressure"),
        nonnegative(_required_float(values, "potassium_membrane_osmotic_pressure_bar"), "Osmotic pressure"),
        positive(_required_float(values, "potassium_membrane_reference_net_pressure_bar"), "Reference net pressure"),
        bounded_fraction(_required_float(values, "potassium_membrane_reference_water_recovery_fraction"), "Membrane water recovery"),
        positive(_required_float(values, "potassium_membrane_water_flux_l_m2_hr"), "Membrane flux"),
        bounded_fraction(_required_float(values, "potassium_membrane_k_rejection_fraction"), "K rejection"),
        bounded_fraction(_required_float(values, "potassium_membrane_monovalent_rejection_fraction"), "Monovalent rejection"),
        bounded_fraction(_required_float(values, "potassium_membrane_divalent_rejection_fraction"), "Divalent rejection"),
        bounded_fraction(_required_float(values, "potassium_membrane_organic_rejection_fraction"), "Organic rejection"),
        bounded_fraction(_required_float(values, "potassium_membrane_contaminant_rejection_fraction"), "Contaminant rejection"),
        nonnegative(_required_float(values, "potassium_membrane_electricity_kwh_m3_permeate"), "Membrane electricity"),
        nonnegative(_required_float(values, "potassium_membrane_cleaning_water_kg_m2_hr"), "Cleaning water"),
    )


def finishing_parameters_from_mapping(values: Mapping[str, object]) -> ProductFinishingParameters:
    """Return optional wet-product washing and low-temperature drying inputs."""

    return ProductFinishingParameters(
        _required_bool(values, "phase7_product_washing_enabled"),
        nonnegative(_required_float(values, "phase7_wash_water_kg_per_kg_dry_product"), "Wash-water ratio"),
        bounded_fraction(_required_float(values, "phase7_wash_impurity_removal_fraction"), "Wash impurity removal"),
        bounded_fraction(_required_float(values, "phase7_wash_product_loss_fraction"), "Wash product loss"),
        nonnegative(_required_float(values, "phase7_wash_electricity_kwh_kg_product"), "Wash electricity"),
        _required_bool(values, "phase7_product_drying_enabled"),
        bounded_fraction(_required_float(values, "phase7_product_target_moisture_fraction"), "Finished-product moisture"),
        _required_float(values, "phase7_product_drying_temperature_c"),
        _required_float(values, "phase7_product_stability_limit_c"),
        positive(_required_float(values, "phase7_product_heat_capacity_kj_kg_k"), "Product heat capacity"),
        positive(_required_float(values, "phase7_product_latent_heat_kj_kg"), "Dryer latent heat"),
        positive(_required_float(values, "phase7_product_dryer_thermal_efficiency"), "Dryer thermal efficiency"),
        nonnegative(_required_float(values, "phase7_product_fan_electricity_kwh_kg_water"), "Dryer fan electricity"),
    )


class DigestateEqualization(bst.Unit):
    """T701 mixed equalization with optional measured residual-gas release."""

    _N_ins = 1
    _N_outs = 2
    line = "Digestate equalization"
    _units = {
        "Liquid throughput": "m3/hr",
        "Working volume": "m3",
        "Total volume": "m3",
        "Residence time": "hr",
        "Tank diameter": "m",
        "Tank height": "m",
        "Heat-transfer area": "m2",
        "Heat loss at feed temperature": "kW",
        "Mixer electricity": "kW",
        "Released gas": "kg/hr",
    }

    def _init(self, parameters: EqualizationParameters):
        self.parameters = parameters
        self.warnings = (
            "T701 is a steady-state homogenization vessel; storage dynamics and settling are not modelled.",
        )
        self.limitation_ids = ("LIM-P7-001",)

    def _run(self):
        feed = self.ins[0]
        liquid, released = self.outs
        liquid.copy_like(feed)
        released.empty()
        if self.parameters.enabled:
            fractions = {
                "Methane": self.parameters.methane_release_fraction,
                "CarbonDioxide": self.parameters.carbon_dioxide_release_fraction,
                "Ammonia": self.parameters.ammonia_release_fraction,
                "HydrogenSulfide": self.parameters.hydrogen_sulfide_release_fraction,
            }
            for component_id, fraction in fractions.items():
                moved = float(liquid.imass[component_id]) * fraction
                liquid.imass[component_id] -= moved
                released.imass[component_id] += moved
        liquid.phase = "l"
        released.phase = "g"
        liquid.T = released.T = feed.T
        liquid.P = released.P = feed.P

    def _design(self):
        import math

        liquid, released = self.outs
        flow = liquid.F_mass / self.parameters.density_kg_m3
        working = flow * self.parameters.residence_time_h if self.parameters.enabled else 0.0
        total = working / self.parameters.working_fraction if working else 0.0
        electricity = (
            working * self.parameters.mixing_power_kw_m3 / self.parameters.motor_efficiency
            if self.parameters.enabled
            else 0.0
        )
        ratio = self.parameters.height_to_diameter_ratio
        diameter = (4.0 * total / (math.pi * ratio)) ** (1.0 / 3.0) if total else 0.0
        height = ratio * diameter
        area = math.pi * diameter * height + 0.5 * math.pi * diameter**2
        temperature_difference = max(
            0.0,
            float(liquid.T) - 273.15 - self.parameters.ambient_temperature_c,
        )
        heat_loss = (
            self.parameters.heat_transfer_coefficient_w_m2_k
            * area
            * temperature_difference
            / 1000.0
            if self.parameters.enabled
            else 0.0
        )
        self.design_results.update(
            {
                "Liquid throughput": flow,
                "Working volume": working,
                "Total volume": total,
                "Residence time": self.parameters.residence_time_h,
                "Tank diameter": diameter,
                "Tank height": height,
                "Heat-transfer area": area,
                "Heat loss at feed temperature": heat_loss,
                "Mixer electricity": electricity,
                "Released gas": released.F_mass,
            }
        )
        self.power_utility.consumption = electricity


class DigestateSolidLiquidSeparator(bst.Unit):
    """S701 physical capture plus common entrained-liquor allocation."""

    _N_ins = 1
    _N_outs = 2
    line = "Digestate solid-liquid separation"
    _units = {
        "Feed throughput": "m3/hr",
        "Captured dry particulate": "kg/hr",
        "Liquid entrainment": "fraction",
        "Cake moisture": "fraction",
        "Dry-solids capture": "fraction",
        "Electricity": "kW",
    }

    def _init(self, parameters: DigestateSeparationParameters):
        self.parameters = parameters
        self.technology = parameters.technology
        self.component_capture_to_solids: dict[str, float] = {}
        self.entrainment_result = None
        self.warnings = (
            f"S701 uses the '{parameters.technology}' option with a component-class allocation calibrated by cake moisture; no vendor curve is claimed.",
        )
        self.limitation_ids = ("LIM-P7-002",)

    def _capture(self, component_id: str) -> float:
        if component_id == "MicrobialBiomass":
            return self.parameters.biomass_capture_fraction
        if component_id == "ParticulatePhosphorus":
            return self.parameters.particulate_p_capture_fraction
        if component_id in COMPONENT_GROUPS["contaminants"]:
            return self.parameters.contaminant_capture_fraction
        if component_id in COMPONENT_GROUPS["fixed_solids"]:
            return self.parameters.inert_capture_fraction
        return self.parameters.particulate_capture_fraction

    def _run(self):
        feed = self.ins[0]
        solids, centrate = self.outs
        solids.empty()
        centrate.empty()
        suspended = COMPONENT_GROUPS["suspended_solids"]
        captured = 0.0
        self.component_capture_to_solids = {}
        for component_id in suspended:
            fraction = self._capture(component_id)
            moved = float(feed.imass[component_id]) * fraction
            solids.imass[component_id] = moved
            centrate.imass[component_id] = float(feed.imass[component_id]) - moved
            captured += moved
            self.component_capture_to_solids[component_id] = fraction
        dissolved_ids = set(chemicals.IDs) - set(suspended) - {"Water"}
        dissolved = sum(float(feed.imass[component_id]) for component_id in dissolved_ids)
        self.entrainment_result = solve_liquid_entrainment(
            captured_particulate_kg_hr=captured,
            liquid_water_kg_hr=float(feed.imass["Water"]),
            dissolved_nonwater_kg_hr=dissolved,
            target_moisture_fraction=self.parameters.cake_moisture_fraction,
        )
        entrainment = self.entrainment_result.entrained_liquid_fraction
        for component_id in dissolved_ids | {"Water"}:
            moved = float(feed.imass[component_id]) * entrainment
            solids.imass[component_id] = moved
            centrate.imass[component_id] = float(feed.imass[component_id]) - moved
            self.component_capture_to_solids[component_id] = entrainment
        for stream in (solids, centrate):
            stream.T = feed.T
            stream.P = feed.P
        solids.phase = "l"
        centrate.phase = "l"

    def _design(self):
        feed = self.ins[0]
        solids = self.outs[0]
        flow = feed.F_mass / self.parameters.density_kg_m3
        water = float(solids.imass["Water"])
        dry = solids.F_mass - water
        moisture = water / solids.F_mass if solids.F_mass else 0.0
        feed_dry = feed.F_mass - float(feed.imass["Water"])
        capture = dry / feed_dry if feed_dry else 0.0
        power = flow * self.parameters.electricity_kwh_m3
        self.design_results.update(
            {
                "Feed throughput": flow,
                "Captured dry particulate": dry,
                "Liquid entrainment": self.entrainment_result.entrained_liquid_fraction,
                "Cake moisture": moisture,
                "Dry-solids capture": capture,
                "Electricity": power,
            }
        )
        self.power_utility.consumption = power


class StruviteCrystallizer(bst.Unit):
    """R711 formula-balanced MgNH4PO4.6H2O Level-1 crystallizer."""

    _N_ins = 4
    _N_outs = 1
    line = "Struvite crystallization"
    _units = {
        "Liquid throughput": "m3/hr",
        "Working volume": "m3",
        "Target pH": "pH",
        "Phosphate feed": "kmol/hr",
        "Struvite formed": "kg/hr",
        "Recovered P": "kg P/hr",
        "Recovered N": "kg N/hr",
        "Magnesium reagent": "kg/hr",
        "Base reagent": "kg/hr",
        "Mixer electricity": "kW",
    }

    def _init(self, parameters: StruviteParameters):
        self.parameters = parameters
        self.extent = None
        self.formed_struvite_kmol_hr = 0.0
        self.competing_calcium_phosphate_kmol_hr = 0.0
        self.magnesium_hydroxide_kmol_hr = 0.0
        self.calcium_carbonate_kmol_hr = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "R711 uses a stoichiometrically bounded empirical recovery, not electrolyte activities or population-balance kinetics.",
            "Only physical Orthophosphate is precipitable; unspeciated P-equivalent pools remain in liquor.",
        )
        self.limitation_ids = ("LIM-P7-003", "LIM-P7-004")

    def _run(self):
        liquor, magnesium_solution, base_solution, seed = self.ins
        slurry = self.outs[0]
        p_kmol = float(liquor.imol["Orthophosphate"])
        magnesium_required = p_kmol * self.parameters.magnesium_to_p_molar_ratio
        source = self.parameters.magnesium_source
        pure_magnesium_reagent = magnesium_required * chemicals[source].MW
        _solution(
            magnesium_solution,
            source,
            pure_magnesium_reagent,
            self.parameters.magnesium_solution_mass_fraction,
        )
        liquid_volume = liquor.F_mass / self.parameters.density_kg_m3
        _solution(
            base_solution,
            self.parameters.base_type,
            liquid_volume * self.parameters.base_dose_kg_m3,
            self.parameters.base_solution_mass_fraction,
        )
        seed.empty()
        seed.imass["Struvite"] = (
            p_kmol * COMPONENT_METADATA["Orthophosphate"].phosphorus_mass_fraction
            * chemicals.Orthophosphate.MW
            * self.parameters.seed_kg_per_kg_p
        )
        seed.phase = "s"
        _mix_into(slurry, self.ins)
        _dissolve_magnesium(
            slurry,
            source,
            self.parameters.magnesium_dissolution_efficiency,
        )
        _dissolve_base(slurry, self.parameters.base_type)
        available_nh4 = (
            float(slurry.imol["Ammonium"])
            * self.parameters.ammonium_availability_fraction
        )
        self.extent = struvite_extent(
            magnesium_kmol_hr=float(slurry.imol["MagnesiumIon"]),
            ammonium_kmol_hr=available_nh4,
            phosphate_kmol_hr=float(slurry.imol["Orthophosphate"]),
            target_phosphate_recovery_fraction=self.parameters.phosphate_recovery_fraction,
        )
        extent = min(self.extent.product_kmol_hr, float(slurry.imol["Water"]) / 6.0)
        self.formed_struvite_kmol_hr = extent
        slurry.imol["MagnesiumIon"] -= extent
        slurry.imol["Ammonium"] -= extent
        slurry.imol["Orthophosphate"] -= extent
        slurry.imol["Water"] -= 6.0 * extent
        slurry.imol["Struvite"] += extent

        remaining_p = float(slurry.imol["Orthophosphate"])
        calcium_extent = calcium_phosphate_extent(
            product_id="CalciumPhosphate",
            calcium_kmol_hr=float(slurry.imol["CalciumIon"]),
            phosphate_kmol_hr=remaining_p,
            hydroxide_kmol_hr=float(slurry.imol["HydroxideIon"]),
            target_phosphate_recovery_fraction=self.parameters.calcium_phosphate_competition_fraction,
        )
        self.competing_calcium_phosphate_kmol_hr = calcium_extent.product_kmol_hr
        slurry.imol["CalciumIon"] -= calcium_extent.calcium_consumed_kmol_hr
        slurry.imol["Orthophosphate"] -= calcium_extent.phosphate_consumed_kmol_hr
        slurry.imol["CalciumPhosphate"] += calcium_extent.product_kmol_hr

        mgoh2_extent = min(
            float(slurry.imol["MagnesiumIon"]),
            float(slurry.imol["HydroxideIon"]) / 2.0,
        ) * self.parameters.magnesium_hydroxide_fraction
        self.magnesium_hydroxide_kmol_hr = mgoh2_extent
        slurry.imol["MagnesiumIon"] -= mgoh2_extent
        slurry.imol["HydroxideIon"] -= 2.0 * mgoh2_extent
        slurry.imol["MagnesiumHydroxide"] += mgoh2_extent

        caco3_extent = min(
            float(slurry.imol["CalciumIon"]),
            float(slurry.imol["CarbonateIon"]),
        ) * self.parameters.calcium_carbonate_fraction
        self.calcium_carbonate_kmol_hr = caco3_extent
        slurry.imol["CalciumIon"] -= caco3_extent
        slurry.imol["CarbonateIon"] -= caco3_extent
        slurry.imol["CalciumCarbonate"] += caco3_extent
        slurry.T = liquor.T
        slurry.P = liquor.P
        slurry.phase = "l"
        _set_reaction_delta(self)

    def _design(self):
        slurry = self.outs[0]
        flow = slurry.F_mass / self.parameters.density_kg_m3
        volume = flow * self.parameters.residence_time_min / 60.0
        product = self.formed_struvite_kmol_hr * chemicals.Struvite.MW
        p = product * COMPONENT_METADATA["Struvite"].phosphorus_mass_fraction
        n = product * COMPONENT_METADATA["Struvite"].nitrogen_mass_fraction
        power = volume * self.parameters.mixing_power_kw_m3
        self.design_results.update(
            {
                "Liquid throughput": flow,
                "Working volume": volume,
                "Target pH": self.parameters.target_pH,
                "Phosphate feed": float(self.ins[0].imol["Orthophosphate"]),
                "Struvite formed": product,
                "Recovered P": p,
                "Recovered N": n,
                "Magnesium reagent": float(self.ins[1].imass[self.parameters.magnesium_source]),
                "Base reagent": float(self.ins[2].imass[self.parameters.base_type]),
                "Mixer electricity": power,
            }
        )
        self.power_utility.consumption = power


class CalciumPhosphateReactor(bst.Unit):
    """R712 configurable formula-balanced calcium-phosphate precipitation."""

    _N_ins = 3
    _N_outs = 1
    line = "Calcium-phosphate precipitation"
    _units = {
        "Liquid throughput": "m3/hr",
        "Working volume": "m3",
        "Target pH": "pH",
        "Product formed": "kg/hr",
        "Recovered P": "kg P/hr",
        "Calcium reagent": "kg/hr",
        "Base reagent": "kg/hr",
        "Calcium carbonate": "kg/hr",
        "Mixer electricity": "kW",
    }

    def _init(self, parameters: CalciumRecoveryParameters):
        self.parameters = parameters
        self.extent = None
        self.formed_product_kmol_hr = 0.0
        self.calcium_carbonate_kmol_hr = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "R712 applies one selected mineral stoichiometry; it does not solve simultaneous mineral equilibria or claim phase purity.",
        )
        self.limitation_ids = ("LIM-P7-005",)

    def _run(self):
        liquor, calcium_solution, base_solution = self.ins
        slurry = self.outs[0]
        p_kmol = float(liquor.imol["Orthophosphate"])
        calcium_required = p_kmol * self.parameters.calcium_to_p_molar_ratio
        source = self.parameters.calcium_source
        _solution(
            calcium_solution,
            source,
            calcium_required * chemicals[source].MW,
            self.parameters.calcium_solution_mass_fraction,
        )
        volume = liquor.F_mass / self.parameters.density_kg_m3
        _solution(
            base_solution,
            self.parameters.base_type,
            volume * self.parameters.base_dose_kg_m3,
            self.parameters.base_solution_mass_fraction,
        )
        _mix_into(slurry, self.ins)
        _dissolve_calcium(slurry, source, self.parameters.calcium_dissolution_efficiency)
        _dissolve_base(slurry, self.parameters.base_type)
        self.extent = calcium_phosphate_extent(
            product_id=self.parameters.product_id,
            calcium_kmol_hr=float(slurry.imol["CalciumIon"]),
            phosphate_kmol_hr=float(slurry.imol["Orthophosphate"]),
            hydroxide_kmol_hr=float(slurry.imol["HydroxideIon"]),
            target_phosphate_recovery_fraction=self.parameters.phosphate_recovery_fraction,
        )
        extent = self.extent
        extent_value = min(
            extent.product_kmol_hr,
            float(slurry.imol["Water"]) / extent.water_consumed_kmol_hr
            if extent.water_consumed_kmol_hr
            else extent.product_kmol_hr,
        )
        scale = extent_value / extent.product_kmol_hr if extent.product_kmol_hr else 0.0
        self.formed_product_kmol_hr = extent_value
        slurry.imol["CalciumIon"] -= extent.calcium_consumed_kmol_hr * scale
        slurry.imol["Orthophosphate"] -= extent.phosphate_consumed_kmol_hr * scale
        slurry.imol["Water"] -= extent.water_consumed_kmol_hr * scale
        slurry.imol["HydroxideIon"] -= extent.hydroxide_consumed_kmol_hr * scale
        slurry.imol["HydroxideIon"] += extent.hydroxide_generated_kmol_hr * scale
        slurry.imol[self.parameters.product_id] += extent_value
        caco3_extent = min(
            float(slurry.imol["CalciumIon"]),
            float(slurry.imol["CarbonateIon"]),
        ) * self.parameters.calcium_carbonate_fraction
        self.calcium_carbonate_kmol_hr = caco3_extent
        slurry.imol["CalciumIon"] -= caco3_extent
        slurry.imol["CarbonateIon"] -= caco3_extent
        slurry.imol["CalciumCarbonate"] += caco3_extent
        slurry.T = liquor.T
        slurry.P = liquor.P
        slurry.phase = "l"
        _set_reaction_delta(self)

    def _design(self):
        slurry = self.outs[0]
        flow = slurry.F_mass / self.parameters.density_kg_m3
        volume = flow * self.parameters.residence_time_min / 60.0
        product = self.formed_product_kmol_hr * chemicals[self.parameters.product_id].MW
        power = volume * self.parameters.mixing_power_kw_m3
        self.design_results.update(
            {
                "Liquid throughput": flow,
                "Working volume": volume,
                "Target pH": self.parameters.target_pH,
                "Product formed": product,
                "Recovered P": product * COMPONENT_METADATA[self.parameters.product_id].phosphorus_mass_fraction,
                "Calcium reagent": float(self.ins[1].imass[self.parameters.calcium_source]),
                "Base reagent": float(self.ins[2].imass[self.parameters.base_type]),
                "Calcium carbonate": self.calcium_carbonate_kmol_hr * chemicals.CalciumCarbonate.MW,
                "Mixer electricity": power,
            }
        )
        self.power_utility.consumption = power


class CrystalSeparator(bst.Unit):
    """S711/S712 physical crystal recovery with entrained mother liquor."""

    _N_ins = 1
    _N_outs = 2
    line = "Nutrient crystal separation"
    _units = {
        "Dry product": "kg/hr",
        "Product moisture": "fraction",
        "Target-mineral purity": "fraction dry basis",
        "Crystal recovery": "fraction",
        "Liquid entrainment": "fraction",
        "Electricity": "kW",
    }

    def _init(self, parameters: CrystalSeparationParameters):
        self.parameters = parameters
        self.entrainment_result = None
        self.component_capture_to_product: dict[str, float] = {}
        self.limitation_ids = ("LIM-P7-006",)

    def _run(self):
        slurry = self.ins[0]
        wet_product, mother_liquor = self.outs
        wet_product.empty()
        mother_liquor.empty()
        target_ids = set(self.parameters.target_product_ids)
        solid_ids = {
            component_id
            for component_id in chemicals.IDs
            if chemicals[component_id].locked_state == "s"
        }
        captured = 0.0
        self.component_capture_to_product = {}
        for component_id in solid_ids:
            fraction = (
                self.parameters.product_capture_fraction
                if component_id in target_ids
                else self.parameters.impurity_capture_fraction
            )
            moved = float(slurry.imass[component_id]) * fraction
            wet_product.imass[component_id] = moved
            mother_liquor.imass[component_id] = float(slurry.imass[component_id]) - moved
            captured += moved
            self.component_capture_to_product[component_id] = fraction
        dissolved_ids = set(chemicals.IDs) - solid_ids - {"Water"}
        dissolved = sum(float(slurry.imass[component_id]) for component_id in dissolved_ids)
        self.entrainment_result = solve_liquid_entrainment(
            captured_particulate_kg_hr=captured,
            liquid_water_kg_hr=float(slurry.imass["Water"]),
            dissolved_nonwater_kg_hr=dissolved,
            target_moisture_fraction=self.parameters.product_moisture_fraction,
        )
        e = self.entrainment_result.entrained_liquid_fraction
        for component_id in dissolved_ids | {"Water"}:
            moved = float(slurry.imass[component_id]) * e
            wet_product.imass[component_id] = moved
            mother_liquor.imass[component_id] = float(slurry.imass[component_id]) - moved
            self.component_capture_to_product[component_id] = e
        for stream in (wet_product, mother_liquor):
            stream.T = slurry.T
            stream.P = slurry.P
        wet_product.phase = "l"
        mother_liquor.phase = "l"

    def _design(self):
        product = self.outs[0]
        water = float(product.imass["Water"])
        dry = product.F_mass - water
        target = sum(float(product.imass[i]) for i in self.parameters.target_product_ids)
        power = dry * self.parameters.electricity_kwh_kg_dry_product
        self.design_results.update(
            {
                "Dry product": dry,
                "Product moisture": water / product.F_mass if product.F_mass else 0.0,
                "Target-mineral purity": target / dry if dry else 0.0,
                "Crystal recovery": self.parameters.product_capture_fraction,
                "Liquid entrainment": self.entrainment_result.entrained_liquid_fraction,
                "Electricity": power,
            }
        )
        self.power_utility.consumption = power


class AlkalineConditioner(bst.Unit):
    """M721 mass-explicit base dosing before ammonia stripping."""

    _N_ins = 2
    _N_outs = 1
    line = "Alkaline dosing and pH conditioning"
    _units = {
        "Liquid throughput": "m3/hr",
        "Target pH": "pH",
        "Pure base": "kg/hr",
        "Solution water": "kg/hr",
        "Mixer electricity": "kW",
    }

    def _init(
        self,
        *,
        base_id: str,
        solution_mass_fraction: float,
        pure_base_dose_kg_m3: float,
        target_pH: float,
        density_kg_m3: float,
        mixing_power_kw_m3: float,
    ):
        self.base_id = base_id
        self.solution_mass_fraction = bounded_fraction(solution_mass_fraction, "Base solution fraction")
        self.pure_base_dose_kg_m3 = nonnegative(pure_base_dose_kg_m3, "Base dose")
        self.target_pH = float(target_pH)
        self.density_kg_m3 = positive(density_kg_m3, "Liquid density")
        self.mixing_power_kw_m3 = nonnegative(mixing_power_kw_m3, "Mixing power")
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "M721 target pH is retained as metadata; base dose is empirical because digestate titration data are unavailable.",
        )
        self.limitation_ids = ("LIM-P7-007",)

    def _run(self):
        liquor, base = self.ins
        conditioned = self.outs[0]
        volume = liquor.F_mass / self.density_kg_m3
        _solution(
            base,
            self.base_id,
            volume * self.pure_base_dose_kg_m3,
            self.solution_mass_fraction,
        )
        _mix_into(conditioned, self.ins)
        _dissolve_base(conditioned, self.base_id)
        conditioned.T = liquor.T
        conditioned.P = liquor.P
        conditioned.phase = "l"
        _set_reaction_delta(self)

    def _design(self):
        volume = self.ins[0].F_mass / self.density_kg_m3
        power = volume * self.mixing_power_kw_m3
        self.design_results.update(
            {
                "Liquid throughput": volume,
                "Target pH": self.target_pH,
                "Pure base": float(self.ins[1].imass[self.base_id]),
                "Solution water": float(self.ins[1].imass["Water"]),
                "Mixer electricity": power,
            }
        )
        self.power_utility.consumption = power


class ProcessHeater(bst.Unit):
    """H721 sensible heater with explicit gross duty and temperature level."""

    _N_ins = 1
    _N_outs = 1
    line = "Phase 7 process heater"
    _units = {
        "Gross heat duty": "kW",
        "Target temperature": "degC",
        "Temperature lift": "K",
    }

    def _init(self, *, target_temperature_c: float, heat_capacity_kj_kg_k: float):
        self.target_temperature_c = float(target_temperature_c)
        self.heat_capacity_kj_kg_k = positive(heat_capacity_kj_kg_k, "Liquid heat capacity")
        self.gross_heat_kw = 0.0
        self.limitation_ids = ("LIM-P7-008",)

    def _run(self):
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)
        product.T = self.target_temperature_c + 273.15
        product.P = feed.P

    def _design(self):
        feed = self.ins[0]
        delta_t = max(0.0, self.outs[0].T - feed.T)
        self.gross_heat_kw = feed.F_mass * self.heat_capacity_kj_kg_k * delta_t / 3600.0
        self.design_results.update(
            {
                "Gross heat duty": self.gross_heat_kw,
                "Target temperature": self.target_temperature_c,
                "Temperature lift": delta_t,
            }
        )
        if self.gross_heat_kw:
            self.add_heat_utility(self.gross_heat_kw * 3600.0, feed.T, self.outs[0].T)


class AmmoniaStripper(bst.Unit):
    """A721 pH/T/P/gas-responsive Level-1 ammonia mass-transfer model."""

    _N_ins = 2
    _N_outs = 2
    line = "Ammonia stripper"
    _units = {
        "Liquid throughput": "m3/hr",
        "Gas flow": "Nm3/hr",
        "Free ammonia fraction": "fraction",
        "Apparent transfer units": "NTU",
        "TAN removal": "fraction",
        "Ammonia stripped": "kg/hr",
        "Carbon dioxide stripped": "kg/hr",
        "Water vaporized": "kg/hr",
        "Packing height": "m",
        "Column diameter": "m",
        "Pressure": "bar",
        "Gas-mover electricity": "kW",
        "Steam heat": "kW",
    }

    def _init(self, parameters: StrippingParameters):
        if parameters.medium not in {"air", "steam", "vacuum"}:
            raise ValueError("Ammonia stripping medium must be air, steam, or vacuum.")
        self.parameters = parameters
        self.calculation = None
        self.ammonia_stripped_kg_hr = 0.0
        self.co2_stripped_kg_hr = 0.0
        self.water_vaporized_kg_hr = 0.0
        self.gas_flow_nm3_hr = 0.0
        self.gross_heat_kw = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "A721 uses an NTU-like empirical response, not rate-based film coefficients or validated packed-column transfer data.",
            "Only explicit CarbonDioxide is stripped; bicarbonate/carbonate re-equilibration is not rigorous.",
        )
        self.limitation_ids = ("LIM-P7-009", "LIM-P7-010")

    def _run(self):
        liquor, carrier = self.ins
        stripped_liquor, offgas = self.outs
        carrier.empty()
        liquid_volume = liquor.F_mass / self.parameters.density_kg_m3
        if self.parameters.medium == "steam":
            carrier.imass["Water"] = liquor.F_mass * self.parameters.steam_kg_kg_liquid
            carrier.phase = "g"
            carrier.T = self.parameters.temperature_c + 273.15
            carrier.P = self.parameters.pressure_pa
            gas_ratio = (
                float(carrier.imol["Water"]) * NORMAL_M3_PER_KMOL / liquid_volume
                if liquid_volume
                else 0.0
            )
        else:
            self.gas_flow_nm3_hr = liquid_volume * self.parameters.gas_to_liquid_ratio_nm3_m3
            carrier_kmol = self.gas_flow_nm3_hr / NORMAL_M3_PER_KMOL
            carrier.imol["Oxygen"] = carrier_kmol * (0.21 if self.parameters.medium == "air" else 0.0)
            carrier.imol["Nitrogen"] = carrier_kmol * (0.79 if self.parameters.medium == "air" else 1.0)
            carrier.phase = "g"
            carrier.T = self.parameters.temperature_c + 273.15
            carrier.P = self.parameters.pressure_pa
            gas_ratio = self.parameters.gas_to_liquid_ratio_nm3_m3
        self.gas_flow_nm3_hr = sum(float(carrier.imol[i]) for i in chemicals.IDs) * NORMAL_M3_PER_KMOL
        self.calculation = ammonia_stripping_fraction(
            pH=self.parameters.pH,
            temperature_k=self.parameters.temperature_c + 273.15,
            pressure_pa=self.parameters.pressure_pa,
            gas_to_liquid_ratio=gas_ratio,
            packing_height_m=self.parameters.packing_height_m,
            transfer_coefficient=self.parameters.transfer_coefficient,
        )
        stripped_liquor.copy_like(liquor)
        offgas.copy_like(carrier)
        nh3_kmol = float(stripped_liquor.imol["Ammonia"])
        nh4_kmol = float(stripped_liquor.imol["Ammonium"])
        target = (nh3_kmol + nh4_kmol) * self.calculation.removal_fraction
        direct = min(nh3_kmol, target)
        converted = min(nh4_kmol, target - direct)
        stripped_liquor.imol["Ammonia"] -= direct
        stripped_liquor.imol["Ammonium"] -= converted
        stripped_liquor.imol["HydrogenIon"] += converted
        offgas.imol["Ammonia"] += direct + converted
        self.ammonia_stripped_kg_hr = (direct + converted) * chemicals.Ammonia.MW
        co2 = float(stripped_liquor.imass["CarbonDioxide"]) * self.parameters.co2_removal_fraction
        stripped_liquor.imass["CarbonDioxide"] -= co2
        offgas.imass["CarbonDioxide"] += co2
        self.co2_stripped_kg_hr = co2
        evaporated = float(stripped_liquor.imass["Water"]) * self.parameters.water_evaporation_fraction
        stripped_liquor.imass["Water"] -= evaporated
        offgas.imass["Water"] += evaporated
        self.water_vaporized_kg_hr = evaporated
        stripped_liquor.T = self.parameters.temperature_c + 273.15
        stripped_liquor.P = self.parameters.pressure_pa
        stripped_liquor.phase = "l"
        offgas.T = self.parameters.temperature_c + 273.15
        offgas.P = self.parameters.pressure_pa
        offgas.phase = "g"
        _set_reaction_delta(self)

    def _design(self):
        liquid_volume = self.ins[0].F_mass / self.parameters.density_kg_m3
        gas_kmol = sum(float(self.outs[1].imol[i]) for i in chemicals.IDs)
        actual_gas = gas_kmol * 8.314462618 * self.outs[1].T / self.outs[1].P
        if self.parameters.medium == "vacuum":
            pressure_rise = max(0.0, 101325.0 - self.parameters.pressure_pa) + self.parameters.pressure_drop_pa
        elif self.parameters.medium == "air":
            pressure_rise = self.parameters.pressure_drop_pa
        else:
            pressure_rise = 0.0
        power = gas_mover_power_kw(
            actual_gas_m3_hr=actual_gas,
            pressure_rise_pa=pressure_rise,
            efficiency=self.parameters.gas_mover_efficiency,
        ) if pressure_rise else 0.0
        steam = float(self.ins[1].imass["Water"]) if self.parameters.medium == "steam" else 0.0
        self.gross_heat_kw = steam * self.parameters.steam_latent_heat_kj_kg / 3600.0
        self.design_results.update(
            {
                "Liquid throughput": liquid_volume,
                "Gas flow": self.gas_flow_nm3_hr,
                "Free ammonia fraction": self.calculation.free_ammonia_fraction,
                "Apparent transfer units": self.calculation.transfer_units,
                "TAN removal": self.calculation.removal_fraction,
                "Ammonia stripped": self.ammonia_stripped_kg_hr,
                "Carbon dioxide stripped": self.co2_stripped_kg_hr,
                "Water vaporized": self.water_vaporized_kg_hr,
                "Packing height": self.parameters.packing_height_m,
                "Column diameter": packed_column_diameter_m(actual_gas, self.parameters.superficial_velocity_m_s),
                "Pressure": self.parameters.pressure_pa / 1e5,
                "Gas-mover electricity": power,
                "Steam heat": self.gross_heat_kw,
            }
        )
        self.power_utility.consumption = power
        if self.gross_heat_kw:
            self.add_heat_utility(
                self.gross_heat_kw * 3600.0,
                self.ins[0].T,
                self.parameters.temperature_c + 273.15,
            )


class AcidAbsorber(bst.Unit):
    """A722 stoichiometric H2SO4/HCl capture of stripped ammonia."""

    _N_ins = 3
    _N_outs = 2
    line = "Ammonia acid absorber"
    _units = {
        "Ammonia feed": "kg/hr",
        "Ammonia captured": "kg/hr",
        "Acid consumed": "kg/hr",
        "Ammonium salt": "kg/hr",
        "Product salt concentration": "fraction",
        "Residual ammonia": "kg/hr",
        "Neutralization heat": "kW",
        "Pressure drop": "Pa",
    }

    def _init(self, parameters: AcidAbsorptionParameters):
        self.parameters = parameters
        self.extent = None
        self.neutralization_heat_kw = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "A722 reports a liquid ammonium-salt solution; no crystallization or dry product is claimed.",
        )
        self.limitation_ids = ("LIM-P7-011",)

    def _run(self):
        gas, acid_solution, makeup_water = self.ins
        clean_gas, product = self.outs
        ammonia = float(gas.imol["Ammonia"])
        acid_per_nh3 = 0.5 if self.parameters.acid_id == "SulfuricAcid" else 1.0
        acid_kmol = ammonia * acid_per_nh3 * (1.0 + self.parameters.acid_excess_fraction)
        _solution(
            acid_solution,
            self.parameters.acid_id,
            acid_kmol * chemicals[self.parameters.acid_id].MW,
            self.parameters.acid_solution_mass_fraction,
        )
        makeup_water.empty()
        makeup_water.imass["Water"] = (
            ammonia * chemicals.Ammonia.MW * self.parameters.water_makeup_kg_per_kg_nh3
        )
        makeup_water.phase = "l"
        self.extent = acid_capture_extent(
            acid_id=self.parameters.acid_id,
            ammonia_kmol_hr=ammonia,
            acid_kmol_hr=float(acid_solution.imol[self.parameters.acid_id]),
            absorber_efficiency=self.parameters.absorber_efficiency,
        )
        clean_gas.copy_like(gas)
        product.empty()
        clean_gas.imol["Ammonia"] -= self.extent.ammonia_captured_kmol_hr
        product.imol[self.extent.product_id] = self.extent.product_kmol_hr
        product.imol[self.parameters.acid_id] = self.extent.residual_acid_kmol_hr
        product.imass["Water"] = (
            float(acid_solution.imass["Water"]) + float(makeup_water.imass["Water"])
        )
        co2 = float(clean_gas.imass["CarbonDioxide"]) * self.parameters.co2_absorption_fraction
        clean_gas.imass["CarbonDioxide"] -= co2
        product.imass["CarbonDioxide"] += co2
        clean_gas.P = max(1000.0, gas.P - self.parameters.pressure_drop_pa)
        clean_gas.T = gas.T
        clean_gas.phase = "g"
        product.P = clean_gas.P
        product.T = gas.T
        product.phase = "l"
        _set_reaction_delta(self)

    def _design(self):
        ammonia_feed = float(self.ins[0].imass["Ammonia"])
        captured = self.extent.ammonia_captured_kmol_hr * chemicals.Ammonia.MW
        acid_consumed = self.extent.acid_consumed_kmol_hr * chemicals[self.parameters.acid_id].MW
        salt = self.extent.product_kmol_hr * chemicals[self.extent.product_id].MW
        self.neutralization_heat_kw = (
            self.extent.ammonia_captured_kmol_hr
            * 1000.0
            * self.parameters.neutralization_heat_kj_mol_nh3
            / 3600.0
        )
        self.design_results.update(
            {
                "Ammonia feed": ammonia_feed,
                "Ammonia captured": captured,
                "Acid consumed": acid_consumed,
                "Ammonium salt": salt,
                "Product salt concentration": salt / self.outs[1].F_mass if self.outs[1].F_mass else 0.0,
                "Residual ammonia": float(self.outs[0].imass["Ammonia"]),
                "Neutralization heat": self.neutralization_heat_kw,
                "Pressure drop": self.parameters.pressure_drop_pa,
            }
        )
        if self.neutralization_heat_kw:
            self.add_heat_utility(-self.neutralization_heat_kw * 3600.0, self.outs[1].T)


class IonExchangeBed(bst.Unit):
    """A731 cycle-average NH4/Na exchange with explicit site-equivalent recycle."""

    _N_ins = 2
    _N_outs = 2
    line = "Ammonium ion exchange"
    _units = {
        "Ammonium feed": "kg/hr",
        "Ammonium captured": "kg/hr",
        "Bed media": "kg",
        "Bed volume": "m3",
        "Service time": "hr",
        "Regenerations": "1/day",
        "Pressure drop": "Pa",
        "Pump electricity": "kW",
    }

    def _init(self, parameters: IonExchangeParameters):
        self.parameters = parameters
        self.design = None
        self.actual_captured_ammonium_kg_hr = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "A731/R731 are a cycle-average site-equivalent recycle, not a dynamic breakthrough model.",
        )
        self.limitation_ids = ("LIM-P7-012",)

    def _run(self):
        liquor, regenerated = self.ins
        treated, loaded = self.outs
        treated.copy_like(liquor)
        loaded.empty()
        nh4_feed = float(liquor.imass["Ammonium"])
        self.design = ion_exchange_design(
            ammonium_feed_kg_hr=nh4_feed,
            recovery_fraction=self.parameters.recovery_fraction,
            capacity_kg_nh4_per_kg_media=self.parameters.capacity_kg_nh4_per_kg_media,
            breakthrough_fraction=self.parameters.breakthrough_fraction,
            service_time_h=self.parameters.service_time_h,
            bed_bulk_density_kg_m3=self.parameters.bed_bulk_density_kg_m3,
            nacl_molar_ratio=self.parameters.nacl_molar_ratio,
        )
        target_sites = self.design.recovered_ammonium_kg_hr / chemicals.Ammonium.MW
        available_sites = float(regenerated.imol["SodiumZeolite"])
        sites = min(target_sites, available_sites)
        treated.imol["Ammonium"] -= sites
        treated.imol["SodiumIon"] += sites
        loaded.imol["AmmoniumZeolite"] = sites
        loaded.imol["SodiumZeolite"] = available_sites - sites
        self.actual_captured_ammonium_kg_hr = sites * chemicals.Ammonium.MW
        treated.T = loaded.T = liquor.T
        treated.P = max(1000.0, liquor.P - self.parameters.pressure_drop_pa)
        loaded.P = treated.P
        treated.phase = "l"
        loaded.phase = "s"
        _set_reaction_delta(self)

    def _design(self):
        flow_m3_s = self.ins[0].F_mass / 1000.0 / 3600.0
        power = flow_m3_s * self.parameters.pressure_drop_pa / self.parameters.pump_efficiency / 1000.0
        self.design_results.update(
            {
                "Ammonium feed": float(self.ins[0].imass["Ammonium"]),
                "Ammonium captured": self.actual_captured_ammonium_kg_hr,
                "Bed media": self.design.bed_media_kg,
                "Bed volume": self.design.bed_volume_m3,
                "Service time": self.design.service_time_h,
                "Regenerations": self.design.regeneration_frequency_per_day,
                "Pressure drop": self.parameters.pressure_drop_pa,
                "Pump electricity": power,
            }
        )
        self.power_utility.consumption = power


class IonExchangeRegeneration(bst.Unit):
    """R731 NaCl regeneration of loaded zeolite site equivalents."""

    _N_ins = 3
    _N_outs = 2
    line = "Ion-exchange regeneration"
    _units = {
        "Loaded site flow": "kmol/hr",
        "NaCl demand": "kg/hr",
        "Rinse water": "kg/hr",
        "Ammonium regenerant": "kg/hr",
        "Regenerant concentration": "fraction NH4",
    }

    def _init(self, parameters: IonExchangeParameters):
        self.parameters = parameters
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.limitation_ids = ("LIM-P7-012",)

    def _run(self):
        loaded, brine, rinse = self.ins
        regenerated, regenerant = self.outs
        sites = float(loaded.imol["AmmoniumZeolite"])
        nacl_kmol = sites * self.parameters.nacl_molar_ratio
        _solution(
            brine,
            "SodiumChloride",
            nacl_kmol * chemicals.SodiumChloride.MW,
            self.parameters.brine_mass_fraction,
        )
        rinse.empty()
        media_equivalent = sites * chemicals.SodiumZeolite.MW
        rinse.imass["Water"] = media_equivalent * self.parameters.rinse_water_kg_per_kg_media
        rinse.phase = "l"
        reacted = min(sites, float(brine.imol["SodiumChloride"]))
        regenerated.empty()
        regenerant.empty()
        regenerated.imol["SodiumZeolite"] = (
            float(loaded.imol["SodiumZeolite"]) + reacted
        )
        regenerated.imol["AmmoniumZeolite"] = sites - reacted
        regenerant.imol["Ammonium"] = reacted
        regenerant.imol["ChlorideIon"] = reacted
        regenerant.imol["SodiumChloride"] = float(brine.imol["SodiumChloride"]) - reacted
        regenerant.imass["Water"] = float(brine.imass["Water"]) + float(rinse.imass["Water"])
        regenerated.T = regenerant.T = loaded.T
        regenerated.P = regenerant.P = loaded.P
        regenerated.phase = "s"
        regenerant.phase = "l"
        _set_reaction_delta(self)

    def _design(self):
        nh4 = float(self.outs[1].imass["Ammonium"])
        self.design_results.update(
            {
                "Loaded site flow": float(self.ins[0].imol["AmmoniumZeolite"]),
                "NaCl demand": float(self.ins[1].imass["SodiumChloride"]),
                "Rinse water": float(self.ins[2].imass["Water"]),
                "Ammonium regenerant": nh4,
                "Regenerant concentration": nh4 / self.outs[1].F_mass if self.outs[1].F_mass else 0.0,
            }
        )


class PotassiumEvaporator(bst.Unit):
    """E741 non-selective water evaporation to a K-rich residual concentrate."""

    _N_ins = 1
    _N_outs = 2
    line = "Potassium-liquor evaporation"
    _units = {
        "Feed": "kg/hr",
        "Water evaporated": "kg/hr",
        "Concentrate": "kg/hr",
        "Potassium concentration": "kg/m3",
        "Concentration factor": "ratio",
        "Gross heat duty": "kW",
        "Electricity": "kW",
        "Scaling index": "ratio",
    }

    def _init(self, parameters: PotassiumConcentrationParameters):
        self.parameters = parameters
        self.gross_heat_kw = 0.0
        self.warnings = (
            "E741 removes water non-selectively; all retained salts and contaminants co-concentrate.",
            "Scaling index is a structural concentration ratio, not a solubility calculation.",
        )
        self.limitation_ids = ("LIM-P7-013",)

    def _run(self):
        feed = self.ins[0]
        concentrate, vapor = self.outs
        concentrate.copy_like(feed)
        vapor.empty()
        water = float(concentrate.imass["Water"]) * self.parameters.evaporation_water_removal_fraction
        concentrate.imass["Water"] -= water
        vapor.imass["Water"] = water
        for component_id, fraction in (("Ammonia", 0.05), ("CarbonDioxide", 0.5)):
            moved = float(concentrate.imass[component_id]) * fraction
            concentrate.imass[component_id] -= moved
            vapor.imass[component_id] += moved
        concentrate.T = vapor.T = self.parameters.evaporation_temperature_c + 273.15
        concentrate.P = vapor.P = feed.P
        concentrate.phase = "l"
        vapor.phase = "g"

    def _design(self):
        feed, concentrate = self.ins[0], self.outs[0]
        water = float(self.outs[1].imass["Water"])
        self.gross_heat_kw = (
            water * self.parameters.latent_heat_kj_kg / self.parameters.thermal_efficiency / 3600.0
        )
        power = water * self.parameters.evaporator_electricity_kwh_kg_water
        feed_k = float(feed.imass["PotassiumIon"])
        feed_volume = feed.F_mass / self.parameters.density_kg_m3
        concentrate_volume = concentrate.F_mass / self.parameters.density_kg_m3
        initial = feed_k / feed_volume if feed_volume else 0.0
        final = float(concentrate.imass["PotassiumIon"]) / concentrate_volume if concentrate_volume else 0.0
        factor = final / initial if initial else 0.0
        self.design_results.update(
            {
                "Feed": feed.F_mass,
                "Water evaporated": water,
                "Concentrate": concentrate.F_mass,
                "Potassium concentration": final,
                "Concentration factor": factor,
                "Gross heat duty": self.gross_heat_kw,
                "Electricity": power,
                "Scaling index": factor,
            }
        )
        self.power_utility.consumption = power
        if self.gross_heat_kw:
            self.add_heat_utility(
                self.gross_heat_kw * 3600.0,
                feed.T,
                self.parameters.evaporation_temperature_c + 273.15,
            )


class PotassiumMembraneConcentrator(bst.Unit):
    """M741 pressure-responsive membrane concentration with species rejection."""

    _N_ins = 2
    _N_outs = 3
    line = "Potassium-liquor membrane concentration"
    _units = {
        "Feed": "kg/hr",
        "Net driving pressure": "bar",
        "Water recovery": "fraction",
        "Membrane area": "m2",
        "Potassium rejection": "fraction",
        "Potassium concentration": "kg/m3",
        "Electricity": "kW",
        "Cleaning water": "kg/hr",
    }

    def _init(self, parameters: PotassiumConcentrationParameters):
        self.parameters = parameters
        self.calculation = None
        self.component_rejections: dict[str, float] = {}
        self.warnings = (
            "M741 uses class-specific rejection coefficients and a net-pressure response; no ion-selective K purification is claimed.",
        )
        self.limitation_ids = ("LIM-P7-014",)

    def _rejection(self, component_id: str) -> float:
        if component_id in COMPONENT_GROUPS["suspended_solids"]:
            return 1.0
        if component_id in COMPONENT_GROUPS["contaminants"]:
            return self.parameters.contaminant_rejection_fraction
        if component_id == "PotassiumIon":
            return self.parameters.potassium_rejection_fraction
        if component_id in {"SodiumIon", "ChlorideIon", "Ammonium", "NitrateIon", "NitriteIon"}:
            return self.parameters.monovalent_rejection_fraction
        if component_id in {"MagnesiumIon", "CalciumIon", "SulfateIon", "Orthophosphate", "CarbonateIon"}:
            return self.parameters.divalent_rejection_fraction
        if COMPONENT_METADATA[component_id].category in {"organic", "protein"}:
            return self.parameters.organic_rejection_fraction
        return self.parameters.monovalent_rejection_fraction

    def _run(self):
        feed, cleaning = self.ins
        concentrate, permeate, wastewater = self.outs
        self.calculation = membrane_water_recovery(
            feed_water_kg_hr=float(feed.imass["Water"]),
            applied_pressure_bar=self.parameters.membrane_pressure_bar,
            osmotic_pressure_bar=self.parameters.membrane_osmotic_pressure_bar,
            reference_net_pressure_bar=self.parameters.membrane_reference_net_pressure_bar,
            reference_water_recovery_fraction=self.parameters.membrane_reference_water_recovery_fraction,
            water_flux_l_m2_hr=self.parameters.membrane_water_flux_l_m2_hr,
        )
        cleaning.empty()
        cleaning.imass["Water"] = self.calculation.membrane_area_m2 * self.parameters.cleaning_water_kg_m2_hr
        cleaning.phase = "l"
        concentrate.empty()
        permeate.empty()
        wastewater.copy_like(cleaning)
        water_permeate = float(feed.imass["Water"]) * self.calculation.water_recovery_fraction
        permeate.imass["Water"] = water_permeate
        concentrate.imass["Water"] = float(feed.imass["Water"]) - water_permeate
        self.component_rejections = {}
        for component_id in set(chemicals.IDs) - {"Water"}:
            rejection = self._rejection(component_id)
            retained = float(feed.imass[component_id]) * rejection
            concentrate.imass[component_id] = retained
            permeate.imass[component_id] = float(feed.imass[component_id]) - retained
            self.component_rejections[component_id] = rejection
        for stream in (concentrate, permeate, wastewater):
            stream.T = feed.T
            stream.P = feed.P
            stream.phase = "l"

    def _design(self):
        permeate_volume = self.outs[1].F_mass / self.parameters.density_kg_m3
        power = permeate_volume * self.parameters.membrane_electricity_kwh_m3_permeate
        concentrate_volume = self.outs[0].F_mass / self.parameters.density_kg_m3
        k_concentration = (
            float(self.outs[0].imass["PotassiumIon"]) / concentrate_volume
            if concentrate_volume
            else 0.0
        )
        self.design_results.update(
            {
                "Feed": self.ins[0].F_mass,
                "Net driving pressure": self.calculation.net_driving_pressure_bar,
                "Water recovery": self.calculation.water_recovery_fraction,
                "Membrane area": self.calculation.membrane_area_m2,
                "Potassium rejection": self.parameters.potassium_rejection_fraction,
                "Potassium concentration": k_concentration,
                "Electricity": power,
                "Cleaning water": float(self.ins[1].imass["Water"]),
            }
        )
        self.power_utility.consumption = power


class NutrientProductWasher(bst.Unit):
    """W711/W712 empirical displacement wash with explicit wash effluent."""

    _N_ins = 2
    _N_outs = 2
    line = "Nutrient-product washing"
    _units = {
        "Dry product feed": "kg/hr",
        "Wash water": "kg/hr",
        "Impurity removal": "fraction",
        "Target-mineral loss": "kg/hr",
        "Electricity": "kW",
    }

    def _init(
        self,
        *,
        target_product_ids: tuple[str, ...],
        parameters: ProductFinishingParameters,
    ):
        self.target_product_ids = frozenset(target_product_ids)
        self.parameters = parameters
        self.limitation_ids = ("LIM-P7-016",)
        self.warnings = (
            "Product washing uses an empirical mother-liquor displacement factor; crystal attrition and solubility require tests.",
        )

    def _run(self):
        cake, wash_water = self.ins
        washed, effluent = self.outs
        wash_water.empty()
        dry_feed = cake.F_mass - float(cake.imass["Water"])
        if self.parameters.washing_enabled:
            wash_water.imass["Water"] = (
                dry_feed * self.parameters.wash_water_kg_per_kg_dry_product
            )
        wash_water.phase = "l"
        washed.copy_like(cake)
        effluent.empty()
        effluent.imass["Water"] = float(wash_water.imass["Water"])
        if self.parameters.washing_enabled:
            for component_id in set(chemicals.IDs) - {"Water"}:
                fraction = (
                    self.parameters.wash_product_loss_fraction
                    if component_id in self.target_product_ids
                    else self.parameters.wash_impurity_removal_fraction
                )
                moved = float(washed.imass[component_id]) * fraction
                washed.imass[component_id] -= moved
                effluent.imass[component_id] += moved
        for stream in (washed, effluent):
            stream.T = cake.T
            stream.P = cake.P
            stream.phase = "l"

    def _design(self):
        cake = self.ins[0]
        dry_feed = cake.F_mass - float(cake.imass["Water"])
        lost = sum(float(self.outs[1].imass[i]) for i in self.target_product_ids)
        power = dry_feed * self.parameters.wash_electricity_kwh_kg_product
        if not self.parameters.washing_enabled:
            power = 0.0
        self.design_results.update(
            {
                "Dry product feed": dry_feed,
                "Wash water": float(self.ins[1].imass["Water"]),
                "Impurity removal": (
                    self.parameters.wash_impurity_removal_fraction
                    if self.parameters.washing_enabled else 0.0
                ),
                "Target-mineral loss": lost,
                "Electricity": power,
            }
        )
        self.power_utility.consumption = power


class NutrientProductDryer(bst.Unit):
    """D711/D712 low-temperature moisture removal without mineral conversion."""

    _N_ins = 1
    _N_outs = 2
    line = "Nutrient-product drying"
    _units = {
        "Wet feed": "kg/hr",
        "Water evaporated": "kg/hr",
        "Final moisture": "fraction",
        "Drying temperature": "degC",
        "Gross heat duty": "kW",
        "Fan electricity": "kW",
    }

    def _init(self, parameters: ProductFinishingParameters):
        self.parameters = parameters
        self.gross_heat_kw = 0.0
        self.limitation_ids = ("LIM-P7-016",)
        self.warnings = (
            "The dryer removes water only; product mineral stability and volatile losses require experimental verification.",
        )

    def _run(self):
        wet = self.ins[0]
        product, exhaust = self.outs
        product.copy_like(wet)
        exhaust.empty()
        if self.parameters.drying_enabled:
            if self.parameters.drying_temperature_c > self.parameters.stability_limit_c:
                raise ValueError(
                    "Selected Phase 7 product-drying temperature exceeds the configured stability limit."
                )
            dry = wet.F_mass - float(wet.imass["Water"])
            target_water = (
                dry * self.parameters.target_moisture_fraction
                / max(1e-12, 1.0 - self.parameters.target_moisture_fraction)
            )
            evaporated = max(0.0, float(wet.imass["Water"]) - target_water)
            product.imass["Water"] -= evaporated
            exhaust.imass["Water"] = evaporated
            product.T = exhaust.T = self.parameters.drying_temperature_c + 273.15
        else:
            product.T = wet.T
            exhaust.T = wet.T
        product.P = exhaust.P = wet.P
        product.phase = "l"
        exhaust.phase = "g"

    def _design(self):
        wet = self.ins[0]
        evaporated = float(self.outs[1].imass["Water"])
        temperature_lift = max(0.0, self.outs[0].T - wet.T)
        sensible = wet.F_mass * self.parameters.heat_capacity_kj_kg_k * temperature_lift
        latent = evaporated * self.parameters.latent_heat_kj_kg
        self.gross_heat_kw = (
            (sensible + latent) / self.parameters.thermal_efficiency / 3600.0
            if self.parameters.drying_enabled else 0.0
        )
        power = evaporated * self.parameters.fan_electricity_kwh_kg_water
        product = self.outs[0]
        final_moisture = (
            float(product.imass["Water"]) / product.F_mass if product.F_mass else 0.0
        )
        self.design_results.update(
            {
                "Wet feed": wet.F_mass,
                "Water evaporated": evaporated,
                "Final moisture": final_moisture,
                "Drying temperature": self.outs[0].T - 273.15,
                "Gross heat duty": self.gross_heat_kw,
                "Fan electricity": power,
            }
        )
        self.power_utility.consumption = power
        if self.gross_heat_kw:
            self.add_heat_utility(
                self.gross_heat_kw * 3600.0,
                wet.T,
                self.outs[0].T,
            )


class ProductStorage(bst.Unit):
    """V722/V741 uncosted product-hold sizing interface."""

    _N_ins = 1
    _N_outs = 1
    line = "Phase 7 product storage"
    _units = {"Throughput": "kg/hr", "Residence time": "hr", "Working mass": "kg"}

    def _init(self, *, residence_time_h: float):
        self.residence_time_h = nonnegative(residence_time_h, "Storage residence time")
        self.limitation_ids = ("LIM-P7-015",)

    def _run(self):
        self.outs[0].copy_like(self.ins[0])

    def _design(self):
        self.design_results.update(
            {
                "Throughput": self.ins[0].F_mass,
                "Residence time": self.residence_time_h,
                "Working mass": self.ins[0].F_mass * self.residence_time_h,
            }
        )


def equipment_count(load: float, capacity: float | None) -> int:
    """Return parallel equipment count when a positive capacity is supplied."""

    if not capacity:
        return 1 if load > 0.0 else 0
    return int(ceil(nonnegative(load, "Equipment load") / positive(capacity, "Equipment capacity")))
