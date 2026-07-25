"""Technology-specific biomethane-upgrading units for GreenHub Phase 6.

Water scrubbing, membrane separation, PSA, and MEA absorption are represented
as distinct mechanisms. Custom units are used only where the installed
BioSTEAM version has no suitable generic process model. Compressors, pumps,
mixers, splitters, and utility heat exchangers remain BioSTEAM built-ins in the
system factory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import biosteam as bst

from Greenhub.chemicals import chemicals
from Greenhub.phase5_specifications import bounded_fraction, nonnegative, positive
from Greenhub.phase6_specifications import (
    DRY_GAS_COMPONENTS,
    empirical_absorption_fraction,
    gas_vessel_volume_m3,
    liquid_vessel_volume_m3,
    module_count,
    normal_volume_nm3_hr,
    segmented_membrane_separation,
    size_gas_column,
)


def _required_float(values: Mapping[str, object], name: str) -> float:
    try:
        return float(values[name])
    except KeyError as error:
        raise ValueError(f"Missing required Phase 6 parameter '{name}'.") from error


def _required_int(values: Mapping[str, object], name: str) -> int:
    value = _required_float(values, name)
    result = int(value)
    if result != value:
        raise ValueError(f"Phase 6 parameter '{name}' must be an integer.")
    return result


def _required_text(values: Mapping[str, object], name: str) -> str:
    try:
        result = str(values[name]).strip()
    except KeyError as error:
        raise ValueError(f"Missing required Phase 6 parameter '{name}'.") from error
    if not result:
        raise ValueError(f"Phase 6 parameter '{name}' cannot be blank.")
    return result


def _required_bool(values: Mapping[str, object], name: str) -> bool:
    try:
        value = values[name]
    except KeyError as error:
        raise ValueError(f"Missing required Phase 6 parameter '{name}'.") from error
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().casefold()
    if normalized in {"true", "yes", "1", "on"}:
        return True
    if normalized in {"false", "no", "0", "off"}:
        return False
    raise ValueError(f"Phase 6 parameter '{name}' must be boolean.")


def _optional_float(values: Mapping[str, object], name: str) -> float | None:
    value = values.get(name)
    return None if value is None or str(value).strip() == "" else float(value)


def _gas_kmol(stream) -> float:
    return sum(float(stream.imol[ID]) for ID in (*DRY_GAS_COMPONENTS, "Water"))


@dataclass(frozen=True)
class FeedQualityLimits:
    """Maximum or minimum conditioned-gas limits before upgrading."""

    maximum_temperature_c: float
    minimum_pressure_bar: float
    maximum_water_mol_fraction_wet: float
    maximum_h2s_ppmv_dry: float
    maximum_ammonia_ppmv_dry: float
    maximum_oxygen_mol_fraction_dry: float
    maximum_particulate_kg_hr: float
    maximum_siloxane_kg_hr: float
    minimum_methane_mol_fraction_dry: float

    def validate(self) -> None:
        if not -45.0 <= self.maximum_temperature_c <= 100.0:
            raise ValueError("Feed-quality maximum temperature is outside the supported range.")
        positive(self.minimum_pressure_bar, "Minimum feed pressure")
        bounded_fraction(self.maximum_water_mol_fraction_wet, "Maximum feed water")
        nonnegative(self.maximum_h2s_ppmv_dry, "Maximum feed H2S")
        nonnegative(self.maximum_ammonia_ppmv_dry, "Maximum feed ammonia")
        bounded_fraction(self.maximum_oxygen_mol_fraction_dry, "Maximum feed oxygen")
        nonnegative(self.maximum_particulate_kg_hr, "Maximum feed particulates")
        nonnegative(self.maximum_siloxane_kg_hr, "Maximum feed siloxanes")
        bounded_fraction(self.minimum_methane_mol_fraction_dry, "Minimum feed methane")


def feed_quality_limits_from_mapping(values: Mapping[str, object]) -> FeedQualityLimits:
    limits = FeedQualityLimits(
        _required_float(values, "upgrading_maximum_feed_temperature_c"),
        _required_float(values, "upgrading_minimum_feed_pressure_bar"),
        _required_float(values, "upgrading_maximum_water_mol_fraction_wet"),
        _required_float(values, "upgrading_maximum_h2s_ppmv_dry"),
        _required_float(values, "upgrading_maximum_ammonia_ppmv_dry"),
        _required_float(values, "upgrading_maximum_oxygen_mol_fraction_dry"),
        _required_float(values, "upgrading_maximum_particulate_kg_hr"),
        _required_float(values, "upgrading_maximum_siloxane_kg_hr"),
        _required_float(values, "upgrading_minimum_methane_mol_fraction_dry"),
    )
    limits.validate()
    return limits


@dataclass(frozen=True)
class WaterScrubbingParameters:
    calculation_level: str
    absorber_pressure_bar: float
    compressor_efficiency: float
    absorber_temperature_c: float
    water_mode: str
    water_to_gas_kg_nm3: float
    reference_water_to_gas_kg_nm3: float
    reference_pressure_bar: float
    reference_temperature_c: float
    temperature_coefficient_per_c: float
    co2_absorption_fraction: float
    methane_absorption_fraction: float
    h2s_absorption_fraction: float
    ammonia_absorption_fraction: float
    water_absorber_pressure_drop_pa: float
    flash_pressure_bar: float
    flash_release_co2_fraction: float
    flash_release_methane_fraction: float
    flash_release_h2s_fraction: float
    flash_release_ammonia_fraction: float
    regeneration_pressure_bar: float
    regeneration_release_co2_fraction: float
    regeneration_release_methane_fraction: float
    regeneration_release_h2s_fraction: float
    regeneration_release_ammonia_fraction: float
    purge_water_fraction: float
    flash_gas_recycle_fraction: float
    regeneration_electricity_kwh_nm3_offgas: float
    absorber_superficial_velocity_m_s: float
    absorber_packing_height_m: float
    flash_residence_time_min: float
    water_density_kg_m3: float
    product_flash_water_removal_fraction: float
    product_dryer_water_removal_fraction: float
    dryer_pressure_drop_pa: float

    def validate(self) -> None:
        if self.calculation_level not in {"empirical_level_1", "henry_stage_interface"}:
            raise ValueError("Water-scrubbing level must be empirical_level_1 or henry_stage_interface.")
        if self.calculation_level == "henry_stage_interface":
            raise NotImplementedError(
                "Henry-stage water scrubbing is data-gated; use empirical_level_1 until Henry constants and stage efficiencies are supplied."
            )
        if self.water_mode not in {"once_through", "partial_recycle", "full_recycle"}:
            raise ValueError("Water mode must be once_through, partial_recycle, or full_recycle.")
        positive(self.absorber_pressure_bar, "Water-scrubber pressure")
        bounded_fraction(self.compressor_efficiency, "C611 efficiency", positive_lower=True)
        positive(self.water_to_gas_kg_nm3, "Water-to-gas ratio")
        positive(self.reference_water_to_gas_kg_nm3, "Reference water-to-gas ratio")
        positive(self.reference_pressure_bar, "Reference absorber pressure")
        for name, value in (
            ("CO2 absorption", self.co2_absorption_fraction),
            ("methane absorption", self.methane_absorption_fraction),
            ("H2S absorption", self.h2s_absorption_fraction),
            ("ammonia absorption", self.ammonia_absorption_fraction),
            ("flash CO2 release", self.flash_release_co2_fraction),
            ("flash methane release", self.flash_release_methane_fraction),
            ("flash H2S release", self.flash_release_h2s_fraction),
            ("flash ammonia release", self.flash_release_ammonia_fraction),
            ("regeneration CO2 release", self.regeneration_release_co2_fraction),
            ("regeneration methane release", self.regeneration_release_methane_fraction),
            ("regeneration H2S release", self.regeneration_release_h2s_fraction),
            ("regeneration ammonia release", self.regeneration_release_ammonia_fraction),
            ("water purge", self.purge_water_fraction),
            ("flash-gas recycle", self.flash_gas_recycle_fraction),
            ("product-flash water removal", self.product_flash_water_removal_fraction),
            ("product-dryer water removal", self.product_dryer_water_removal_fraction),
        ):
            bounded_fraction(value, name)
        if self.water_mode == "once_through" and self.purge_water_fraction < 1.0:
            raise ValueError("Once-through water mode requires purge_water_fraction=1.")
        if self.flash_pressure_bar >= self.absorber_pressure_bar:
            raise ValueError("V612 flash pressure must be below absorber pressure.")
        if self.regeneration_pressure_bar > self.flash_pressure_bar:
            raise ValueError("A612 regeneration pressure cannot exceed V612 flash pressure.")
        nonnegative(self.water_absorber_pressure_drop_pa, "A611 pressure drop")
        nonnegative(self.regeneration_electricity_kwh_nm3_offgas, "A612 electricity factor")
        positive(self.absorber_superficial_velocity_m_s, "A611 gas velocity")
        positive(self.absorber_packing_height_m, "A611 packing height")
        nonnegative(self.flash_residence_time_min, "V612 residence time")
        positive(self.water_density_kg_m3, "Scrubbing-water density")
        nonnegative(self.dryer_pressure_drop_pa, "D611 pressure drop")


def water_scrubbing_parameters_from_mapping(values: Mapping[str, object]) -> WaterScrubbingParameters:
    parameters = WaterScrubbingParameters(
        _required_text(values, "water_scrubbing_calculation_level"),
        _required_float(values, "water_scrubber_absorber_pressure_bar"),
        _required_float(values, "water_scrubber_compressor_efficiency"),
        _required_float(values, "water_scrubber_absorber_temperature_c"),
        _required_text(values, "water_scrubber_water_mode"),
        _required_float(values, "water_scrubber_water_to_gas_kg_nm3"),
        _required_float(values, "water_scrubber_reference_water_to_gas_kg_nm3"),
        _required_float(values, "water_scrubber_reference_pressure_bar"),
        _required_float(values, "water_scrubber_reference_temperature_c"),
        _required_float(values, "water_scrubber_temperature_coefficient_per_c"),
        _required_float(values, "water_scrubber_co2_absorption_fraction"),
        _required_float(values, "water_scrubber_methane_absorption_fraction"),
        _required_float(values, "water_scrubber_h2s_absorption_fraction"),
        _required_float(values, "water_scrubber_ammonia_absorption_fraction"),
        _required_float(values, "water_scrubber_absorber_pressure_drop_pa"),
        _required_float(values, "water_scrubber_flash_pressure_bar"),
        _required_float(values, "water_scrubber_flash_release_co2_fraction"),
        _required_float(values, "water_scrubber_flash_release_methane_fraction"),
        _required_float(values, "water_scrubber_flash_release_h2s_fraction"),
        _required_float(values, "water_scrubber_flash_release_ammonia_fraction"),
        _required_float(values, "water_scrubber_regeneration_pressure_bar"),
        _required_float(values, "water_scrubber_regeneration_release_co2_fraction"),
        _required_float(values, "water_scrubber_regeneration_release_methane_fraction"),
        _required_float(values, "water_scrubber_regeneration_release_h2s_fraction"),
        _required_float(values, "water_scrubber_regeneration_release_ammonia_fraction"),
        _required_float(values, "water_scrubber_purge_water_fraction"),
        _required_float(values, "water_scrubber_flash_gas_recycle_fraction"),
        _required_float(values, "water_scrubber_regeneration_electricity_kwh_nm3_offgas"),
        _required_float(values, "water_scrubber_absorber_velocity_m_s"),
        _required_float(values, "water_scrubber_absorber_packing_height_m"),
        _required_float(values, "water_scrubber_flash_residence_time_min"),
        _required_float(values, "water_scrubber_water_density_kg_m3"),
        _required_float(values, "water_scrubber_product_flash_water_removal_fraction"),
        _required_float(values, "water_scrubber_product_dryer_water_removal_fraction"),
        _required_float(values, "water_scrubber_dryer_pressure_drop_pa"),
    )
    parameters.validate()
    return parameters


class WaterAbsorber(bst.Unit):
    """Pressure/circulation-dependent physical gas absorption into water."""

    _N_ins = 3
    _N_outs = 2
    line = "High-pressure water absorber"
    _units = {
        "Gas feed": "Nm3/hr",
        "Gross circulating water": "kg/hr",
        "Fresh-water makeup": "kg/hr",
        "Water-to-gas ratio": "kg/Nm3",
        "CO2 absorbed": "kg/hr",
        "Methane co-absorbed": "kg/hr",
        "Column diameter": "m",
        "Packing height": "m",
        "Working volume": "m3",
        "Pressure drop": "Pa",
    }

    def _init(self, parameters: WaterScrubbingParameters):
        parameters.validate()
        self.parameters = parameters
        self.absorbed_kg_hr: dict[str, float] = {}
        self.warnings = (
            "A611 is a calibrated Level-1 apparent-partition model; no electrolyte speciation or Henry stages are active.",
        )
        self.limitation_ids = ("LIM-P6-007",)

    def _run(self):
        gas_feed, recycled_water, fresh_water = self.ins
        product_gas, rich_water = self.outs
        product_gas.copy_like(gas_feed)
        fresh_water.empty()
        rich_water.empty()
        gas_nm3 = normal_volume_nm3_hr(gas_feed, dry=True)
        target_water = gas_nm3 * self.parameters.water_to_gas_kg_nm3
        recycled_water_mass = float(recycled_water.imass["Water"])
        fresh_water.imass["Water"] = max(0.0, target_water - recycled_water_mass)
        for source in (recycled_water, fresh_water):
            for ID in chemicals.IDs:
                rich_water.imass[ID] += float(source.imass[ID])
        effective_water = float(rich_water.imass["Water"])
        ratio = effective_water / gas_nm3 if gas_nm3 else 0.0
        references = {
            "CarbonDioxide": self.parameters.co2_absorption_fraction,
            "Methane": self.parameters.methane_absorption_fraction,
            "HydrogenSulfide": self.parameters.h2s_absorption_fraction,
            "Ammonia": self.parameters.ammonia_absorption_fraction,
        }
        self.absorbed_kg_hr = {}
        for ID, reference in references.items():
            fraction = empirical_absorption_fraction(
                reference,
                pressure_bar=gas_feed.P / 1e5,
                reference_pressure_bar=self.parameters.reference_pressure_bar,
                water_to_gas_ratio=ratio,
                reference_water_to_gas_ratio=self.parameters.reference_water_to_gas_kg_nm3,
                temperature_c=gas_feed.T - 273.15,
                reference_temperature_c=self.parameters.reference_temperature_c,
                temperature_coefficient_per_c=self.parameters.temperature_coefficient_per_c,
            )
            transferred = float(product_gas.imass[ID]) * fraction
            product_gas.imass[ID] -= transferred
            rich_water.imass[ID] += transferred
            self.absorbed_kg_hr[ID] = transferred
        product_gas.T = gas_feed.T
        product_gas.P = max(1_000.0, gas_feed.P - self.parameters.water_absorber_pressure_drop_pa)
        product_gas.phase = "g"
        for stream in (recycled_water, fresh_water, rich_water):
            stream.T = gas_feed.T
            stream.P = product_gas.P
            stream.phase = "l"

    def _design(self):
        gas_feed, recycled_water, fresh_water = self.ins
        rich_water = self.outs[1]
        gas_nm3 = normal_volume_nm3_hr(gas_feed, dry=True)
        geometry = size_gas_column(
            gas_kmol_hr=_gas_kmol(gas_feed),
            temperature_k=gas_feed.T,
            pressure_pa=gas_feed.P,
            design_superficial_velocity_m_s=self.parameters.absorber_superficial_velocity_m_s,
            packing_height_m=self.parameters.absorber_packing_height_m,
        )
        self.design_results["Gas feed"] = gas_nm3
        self.design_results["Gross circulating water"] = float(rich_water.imass["Water"])
        self.design_results["Fresh-water makeup"] = fresh_water.F_mass
        self.design_results["Water-to-gas ratio"] = (
            float(rich_water.imass["Water"]) / gas_nm3 if gas_nm3 else 0.0
        )
        self.design_results["CO2 absorbed"] = self.absorbed_kg_hr.get("CarbonDioxide", 0.0)
        self.design_results["Methane co-absorbed"] = self.absorbed_kg_hr.get("Methane", 0.0)
        self.design_results["Column diameter"] = geometry.diameter_m
        self.design_results["Packing height"] = geometry.packing_height_m
        self.design_results["Working volume"] = geometry.total_volume_m3
        self.design_results["Pressure drop"] = gas_feed.P - self.outs[0].P
        self.power_utility.consumption = 0.0


class WaterFlashTank(bst.Unit):
    """Depressurize rich water and release a methane-enriched flash gas."""

    _N_ins = 1
    _N_outs = 2
    line = "Rich-water flash"
    _units = {
        "Rich water": "kg/hr",
        "Flash gas": "Nm3/hr",
        "Methane recovered": "kg/hr",
        "CO2 released": "kg/hr",
        "Working volume": "m3",
        "Flash pressure": "bar",
    }

    def _init(self, parameters: WaterScrubbingParameters):
        parameters.validate()
        self.parameters = parameters
        self.released_kg_hr: dict[str, float] = {}
        self.limitation_ids = ("LIM-P6-007",)

    def _run(self):
        rich = self.ins[0]
        flash_gas, flashed_water = self.outs
        flashed_water.copy_like(rich)
        flash_gas.empty()
        fractions = {
            "CarbonDioxide": self.parameters.flash_release_co2_fraction,
            "Methane": self.parameters.flash_release_methane_fraction,
            "HydrogenSulfide": self.parameters.flash_release_h2s_fraction,
            "Ammonia": self.parameters.flash_release_ammonia_fraction,
        }
        self.released_kg_hr = {}
        for ID, fraction in fractions.items():
            released = float(flashed_water.imass[ID]) * fraction
            flashed_water.imass[ID] -= released
            flash_gas.imass[ID] = released
            self.released_kg_hr[ID] = released
        pressure = self.parameters.flash_pressure_bar * 1e5
        flash_gas.T = flashed_water.T = rich.T
        flash_gas.P = flashed_water.P = pressure
        flash_gas.phase = "g"
        flashed_water.phase = "l"

    def _design(self):
        rich = self.ins[0]
        flash_gas, flashed_water = self.outs
        volume = liquid_vessel_volume_m3(
            liquid_flow_kg_hr=rich.F_mass,
            density_kg_m3=self.parameters.water_density_kg_m3,
            residence_time_min=self.parameters.flash_residence_time_min,
        )
        self.design_results["Rich water"] = rich.F_mass
        self.design_results["Flash gas"] = normal_volume_nm3_hr(flash_gas)
        self.design_results["Methane recovered"] = self.released_kg_hr.get("Methane", 0.0)
        self.design_results["CO2 released"] = self.released_kg_hr.get("CarbonDioxide", 0.0)
        self.design_results["Working volume"] = volume
        self.design_results["Flash pressure"] = flashed_water.P / 1e5
        self.power_utility.consumption = 0.0


class WaterRegenerator(bst.Unit):
    """Release residual dissolved gas and split regenerated water purge/recycle."""

    _N_ins = 1
    _N_outs = 3
    line = "Scrubbing-water regeneration"
    _units = {
        "Regeneration off-gas": "Nm3/hr",
        "Recycled water": "kg/hr",
        "Purge water": "kg/hr",
        "CO2 released": "kg/hr",
        "Methane released": "kg/hr",
        "Regeneration electricity": "kW",
    }

    def _init(self, parameters: WaterScrubbingParameters):
        parameters.validate()
        self.parameters = parameters
        self.released_kg_hr: dict[str, float] = {}
        self.limitation_ids = ("LIM-P6-007",)

    def _run(self):
        flashed_water = self.ins[0]
        offgas, recycle_water, purge_water = self.outs
        recycle_water.copy_like(flashed_water)
        offgas.empty()
        purge_water.empty()
        fractions = {
            "CarbonDioxide": self.parameters.regeneration_release_co2_fraction,
            "Methane": self.parameters.regeneration_release_methane_fraction,
            "HydrogenSulfide": self.parameters.regeneration_release_h2s_fraction,
            "Ammonia": self.parameters.regeneration_release_ammonia_fraction,
        }
        self.released_kg_hr = {}
        for ID, fraction in fractions.items():
            released = float(recycle_water.imass[ID]) * fraction
            recycle_water.imass[ID] -= released
            offgas.imass[ID] = released
            self.released_kg_hr[ID] = released
        purge_fraction = self.parameters.purge_water_fraction
        for ID in chemicals.IDs:
            purged = float(recycle_water.imass[ID]) * purge_fraction
            recycle_water.imass[ID] -= purged
            purge_water.imass[ID] = purged
        pressure = self.parameters.regeneration_pressure_bar * 1e5
        for stream, phase in ((offgas, "g"), (recycle_water, "l"), (purge_water, "l")):
            stream.T = flashed_water.T
            stream.P = pressure
            stream.phase = phase

    def _design(self):
        offgas, recycle_water, purge_water = self.outs
        electricity = (
            normal_volume_nm3_hr(offgas)
            * self.parameters.regeneration_electricity_kwh_nm3_offgas
        )
        self.design_results["Regeneration off-gas"] = normal_volume_nm3_hr(offgas)
        self.design_results["Recycled water"] = recycle_water.F_mass
        self.design_results["Purge water"] = purge_water.F_mass
        self.design_results["CO2 released"] = self.released_kg_hr.get("CarbonDioxide", 0.0)
        self.design_results["Methane released"] = self.released_kg_hr.get("Methane", 0.0)
        self.design_results["Regeneration electricity"] = electricity
        self.power_utility.consumption = electricity


class GasWaterSeparator(bst.Unit):
    """Remove a specified fraction of gas-stream water without gas conversion."""

    _N_ins = 1
    _N_outs = 2
    line = "Gas moisture guard"
    _units = {
        "Gas flow": "Nm3/hr",
        "Water entering": "kg/hr",
        "Water removed": "kg/hr",
        "Water removal": "fraction",
        "Pressure drop": "Pa",
        "Working volume": "m3",
    }

    def _init(
        self,
        *,
        water_removal_fraction: float,
        pressure_drop_pa: float,
        residence_time_min: float = 0.5,
        limitation_id: str = "LIM-P6-008",
    ):
        self.water_removal_fraction = bounded_fraction(
            water_removal_fraction,
            "Gas-water-separator removal",
        )
        self.pressure_drop_pa = nonnegative(pressure_drop_pa, "Gas-water-separator pressure drop")
        self.residence_time_min = nonnegative(residence_time_min, "Gas-water-separator residence")
        self.water_removed_kg_hr = 0.0
        self.limitation_ids = (limitation_id,)

    def _run(self):
        feed = self.ins[0]
        gas, liquid = self.outs
        gas.copy_like(feed)
        liquid.empty()
        self.water_removed_kg_hr = (
            float(gas.imass["Water"]) * self.water_removal_fraction
        )
        gas.imass["Water"] -= self.water_removed_kg_hr
        liquid.imass["Water"] = self.water_removed_kg_hr
        gas.T = liquid.T = feed.T
        gas.P = liquid.P = max(1_000.0, feed.P - self.pressure_drop_pa)
        gas.phase = "g"
        liquid.phase = "l"

    def _design(self):
        feed = self.ins[0]
        gas = self.outs[0]
        volume = gas_vessel_volume_m3(
            gas_kmol_hr=_gas_kmol(feed),
            temperature_k=feed.T,
            pressure_pa=feed.P,
            residence_time_min=self.residence_time_min,
        )
        water_in = float(feed.imass["Water"])
        self.design_results["Gas flow"] = normal_volume_nm3_hr(feed)
        self.design_results["Water entering"] = water_in
        self.design_results["Water removed"] = self.water_removed_kg_hr
        self.design_results["Water removal"] = self.water_removed_kg_hr / water_in if water_in else 0.0
        self.design_results["Pressure drop"] = feed.P - gas.P
        self.design_results["Working volume"] = volume
        self.power_utility.consumption = 0.0


@dataclass(frozen=True)
class MembraneParameters:
    material_id: str
    feed_pressure_bar: float
    permeate_pressure_bar: float
    compressor_efficiency: float
    aftercooler_temperature_c: float
    dryer_water_removal_fraction: float
    dryer_pressure_drop_pa: float
    number_of_stages: int
    membrane_area_stage1_m2: float
    membrane_area_stage2_m2: float
    membrane_area_stage3_m2: float
    segments_per_stage: int
    stage_pressure_drop_bar: float
    recycle_fraction: float
    nominal_module_area_m2: float
    membrane_lifetime_years: float
    annual_replacement_fraction: float
    target_stage_cut: float | None
    permeances_gpu: dict[str, float]

    def validate(self) -> None:
        positive(self.feed_pressure_bar, "Membrane feed pressure")
        positive(self.permeate_pressure_bar, "Membrane permeate pressure")
        if self.feed_pressure_bar <= self.permeate_pressure_bar:
            raise ValueError("Membrane feed pressure must exceed permeate pressure.")
        bounded_fraction(self.compressor_efficiency, "C621 efficiency", positive_lower=True)
        bounded_fraction(self.dryer_water_removal_fraction, "D621 water removal")
        nonnegative(self.dryer_pressure_drop_pa, "D621 pressure drop")
        if self.number_of_stages not in {1, 2, 3}:
            raise ValueError("Membrane number_of_stages must be 1, 2, or 3.")
        for index, area in enumerate(
            (self.membrane_area_stage1_m2, self.membrane_area_stage2_m2, self.membrane_area_stage3_m2),
            start=1,
        ):
            if index <= self.number_of_stages:
                positive(area, f"Membrane stage {index} area")
            else:
                nonnegative(area, f"Inactive membrane stage {index} area")
        if self.segments_per_stage < 1:
            raise ValueError("Membrane segments_per_stage must be at least 1.")
        nonnegative(self.stage_pressure_drop_bar, "Membrane stage pressure drop")
        bounded_fraction(self.recycle_fraction, "Membrane recycle fraction")
        positive(self.nominal_module_area_m2, "Nominal membrane-module area")
        positive(self.membrane_lifetime_years, "Membrane lifetime")
        bounded_fraction(self.annual_replacement_fraction, "Annual membrane replacement")
        if self.target_stage_cut is not None:
            bounded_fraction(self.target_stage_cut, "Target stage cut")
        for ID, value in self.permeances_gpu.items():
            nonnegative(value, f"{ID} permeance")


def membrane_parameters_from_mapping(values: Mapping[str, object]) -> MembraneParameters:
    permeances = {
        ID: _required_float(values, f"membrane_{ID.lower()}_permeance_gpu")
        for ID in DRY_GAS_COMPONENTS
    }
    permeances["Water"] = _required_float(values, "membrane_water_permeance_gpu")
    parameters = MembraneParameters(
        _required_text(values, "membrane_material_id"),
        _required_float(values, "membrane_feed_pressure_bar"),
        _required_float(values, "membrane_permeate_pressure_bar"),
        _required_float(values, "membrane_compressor_efficiency"),
        _required_float(values, "membrane_aftercooler_temperature_c"),
        _required_float(values, "membrane_dryer_water_removal_fraction"),
        _required_float(values, "membrane_dryer_pressure_drop_pa"),
        _required_int(values, "membrane_number_of_stages"),
        _required_float(values, "membrane_area_stage1_m2"),
        _required_float(values, "membrane_area_stage2_m2"),
        _required_float(values, "membrane_area_stage3_m2"),
        _required_int(values, "membrane_segments_per_stage"),
        _required_float(values, "membrane_stage_pressure_drop_bar"),
        _required_float(values, "membrane_recycle_fraction"),
        _required_float(values, "membrane_nominal_module_area_m2"),
        _required_float(values, "membrane_lifetime_years"),
        _required_float(values, "membrane_annual_replacement_fraction"),
        _optional_float(values, "membrane_target_stage_cut"),
        permeances,
    )
    parameters.validate()
    return parameters


class MembraneStage(bst.Unit):
    """Segmented partial-pressure-driven gas membrane stage."""

    _N_ins = 1
    _N_outs = 2
    line = "Gas membrane stage"
    _units = {
        "Feed gas": "Nm3/hr",
        "Retentate": "Nm3/hr",
        "Permeate": "Nm3/hr",
        "Membrane area": "m2",
        "Module count": "-",
        "Stage cut": "fraction",
        "CH4 transfer": "kg/hr",
        "CO2 transfer": "kg/hr",
        "Feed pressure": "bar",
        "Permeate pressure": "bar",
    }

    def _init(self, parameters: MembraneParameters, *, stage_number: int, area_m2: float):
        parameters.validate()
        if stage_number not in {1, 2, 3}:
            raise ValueError("Membrane stage number must be 1, 2, or 3.")
        self.parameters = parameters
        self.stage_number = stage_number
        self.area_m2 = positive(area_m2, "Membrane stage area")
        self.calculation = None
        self.warnings = (
            "Membrane permeances are class-E structural inputs and the stage is isothermal with plug-flow area segments.",
        )
        self.limitation_ids = ("LIM-P6-009",)

    def _run(self):
        feed = self.ins[0]
        retentate, permeate = self.outs
        feed_moles = {ID: float(feed.imol[ID]) for ID in chemicals.IDs}
        self.calculation = segmented_membrane_separation(
            feed_moles,
            permeance_gpu=self.parameters.permeances_gpu,
            membrane_area_m2=self.area_m2,
            feed_pressure_bar=feed.P / 1e5,
            permeate_pressure_bar=self.parameters.permeate_pressure_bar,
            pressure_drop_bar=self.parameters.stage_pressure_drop_bar,
            segments=self.parameters.segments_per_stage,
        )
        retentate.empty()
        permeate.empty()
        for ID in chemicals.IDs:
            retentate.imol[ID] = self.calculation.retentate_kmol_hr[ID]
            permeate.imol[ID] = self.calculation.permeate_kmol_hr[ID]
        retentate.T = permeate.T = feed.T
        retentate.P = max(
            self.parameters.permeate_pressure_bar * 1e5 + 1.0,
            feed.P - self.parameters.stage_pressure_drop_bar * 1e5,
        )
        permeate.P = self.parameters.permeate_pressure_bar * 1e5
        retentate.phase = permeate.phase = "g"

    def _design(self):
        feed = self.ins[0]
        retentate, permeate = self.outs
        calculation = self.calculation
        self.design_results["Feed gas"] = normal_volume_nm3_hr(feed)
        self.design_results["Retentate"] = normal_volume_nm3_hr(retentate)
        self.design_results["Permeate"] = normal_volume_nm3_hr(permeate)
        self.design_results["Membrane area"] = self.area_m2
        self.design_results["Module count"] = module_count(
            self.area_m2,
            self.parameters.nominal_module_area_m2,
        )
        self.design_results["Stage cut"] = calculation.stage_cut
        self.design_results["CH4 transfer"] = float(permeate.imass["Methane"])
        self.design_results["CO2 transfer"] = float(permeate.imass["CarbonDioxide"])
        self.design_results["Feed pressure"] = feed.P / 1e5
        self.design_results["Permeate pressure"] = permeate.P / 1e5
        self.power_utility.consumption = 0.0


@dataclass(frozen=True)
class PSAParameters:
    adsorption_pressure_bar: float
    blowdown_pressure_bar: float
    compressor_efficiency: float
    dryer_water_removal_fraction: float
    dryer_pressure_drop_pa: float
    reference_pressure_bar: float
    adsorption_fractions: dict[str, float]
    purge_fraction: float
    purge_recycle_fraction: float
    working_capacity_kg_co2_per_kg_adsorbent: float
    bulk_density_kg_m3: float
    number_of_beds: int
    adsorption_time_min: float
    regeneration_time_min: float
    pressure_drop_pa: float
    annual_attrition_fraction: float
    operating_hours_per_year: float
    vacuum_electricity_kwh_nm3_offgas: float

    def validate(self) -> None:
        positive(self.adsorption_pressure_bar, "PSA adsorption pressure")
        positive(self.blowdown_pressure_bar, "PSA blowdown pressure")
        if self.adsorption_pressure_bar <= self.blowdown_pressure_bar:
            raise ValueError("PSA adsorption pressure must exceed blowdown pressure.")
        bounded_fraction(self.compressor_efficiency, "C631 efficiency", positive_lower=True)
        bounded_fraction(self.dryer_water_removal_fraction, "D631 water removal")
        nonnegative(self.dryer_pressure_drop_pa, "D631 pressure drop")
        positive(self.reference_pressure_bar, "PSA reference pressure")
        for ID, value in self.adsorption_fractions.items():
            bounded_fraction(value, f"PSA {ID} adsorption")
        bounded_fraction(self.purge_fraction, "PSA purge fraction")
        bounded_fraction(self.purge_recycle_fraction, "PSA purge recycle")
        positive(self.working_capacity_kg_co2_per_kg_adsorbent, "PSA working capacity")
        positive(self.bulk_density_kg_m3, "PSA bulk density")
        if self.number_of_beds < 2:
            raise ValueError("PSA requires at least two beds for cycle-average continuity.")
        positive(self.adsorption_time_min, "PSA adsorption time")
        positive(self.regeneration_time_min, "PSA regeneration time")
        nonnegative(self.pressure_drop_pa, "PSA pressure drop")
        bounded_fraction(self.annual_attrition_fraction, "PSA annual attrition")
        positive(self.operating_hours_per_year, "PSA operating hours")
        nonnegative(self.vacuum_electricity_kwh_nm3_offgas, "PSA vacuum electricity")


def psa_parameters_from_mapping(values: Mapping[str, object]) -> PSAParameters:
    fractions = {
        ID: _required_float(values, f"psa_{ID.lower()}_adsorption_fraction")
        for ID in (*DRY_GAS_COMPONENTS, "Water")
    }
    parameters = PSAParameters(
        _required_float(values, "psa_adsorption_pressure_bar"),
        _required_float(values, "psa_blowdown_pressure_bar"),
        _required_float(values, "psa_compressor_efficiency"),
        _required_float(values, "psa_dryer_water_removal_fraction"),
        _required_float(values, "psa_dryer_pressure_drop_pa"),
        _required_float(values, "psa_reference_pressure_bar"),
        fractions,
        _required_float(values, "psa_purge_fraction"),
        _required_float(values, "psa_purge_recycle_fraction"),
        _required_float(values, "psa_working_capacity_kg_co2_per_kg_adsorbent"),
        _required_float(values, "psa_adsorbent_bulk_density_kg_m3"),
        _required_int(values, "psa_number_of_beds"),
        _required_float(values, "psa_adsorption_time_min"),
        _required_float(values, "psa_regeneration_time_min"),
        _required_float(values, "psa_pressure_drop_pa"),
        _required_float(values, "psa_annual_attrition_fraction"),
        _required_float(values, "psa_operating_hours_per_year"),
        _required_float(values, "psa_vacuum_electricity_kwh_nm3_offgas"),
    )
    parameters.validate()
    return parameters


class PressureSwingAdsorber(bst.Unit):
    """Mass-conserving Level-1 cycle-average PSA separation."""

    _N_ins = 2
    _N_outs = 4
    line = "Pressure-swing adsorption"
    _units = {
        "Feed gas": "Nm3/hr",
        "Product gas": "Nm3/hr",
        "Blowdown gas": "Nm3/hr",
        "Purge gas": "Nm3/hr",
        "CO2 captured per cycle": "kg/cycle",
        "Adsorbent inventory": "kg",
        "Bed volume": "m3",
        "Cycle time": "min",
        "Methane loss": "kg/hr",
        "Vacuum electricity": "kW",
    }

    def _init(self, parameters: PSAParameters):
        parameters.validate()
        self.parameters = parameters
        self.adsorbent_inventory_kg = 0.0
        self.captured_kg_hr: dict[str, float] = {}
        self.warnings = (
            "A631 is a calibrated Level-1 cycle-average model; no unmeasured Langmuir isotherm is invented.",
        )
        self.limitation_ids = ("LIM-P6-010",)

    def _run(self):
        feed, fresh_adsorbent = self.ins
        product, blowdown, purge, spent_adsorbent = self.outs
        product.copy_like(feed)
        blowdown.empty()
        purge.empty()
        fresh_adsorbent.empty()
        spent_adsorbent.empty()
        pressure_factor = feed.P / 1e5 / self.parameters.reference_pressure_bar
        self.captured_kg_hr = {}
        for ID, base_fraction in self.parameters.adsorption_fractions.items():
            fraction = (
                1.0
                if base_fraction >= 1.0
                else max(0.0, min(1.0, 1.0 - (1.0 - base_fraction) ** pressure_factor))
            )
            captured = float(product.imass[ID]) * fraction
            product.imass[ID] -= captured
            blowdown.imass[ID] = captured
            self.captured_kg_hr[ID] = captured
        for ID in chemicals.IDs:
            purged = float(product.imass[ID]) * self.parameters.purge_fraction
            product.imass[ID] -= purged
            purge.imass[ID] = purged
        co2_per_cycle = (
            self.captured_kg_hr.get("CarbonDioxide", 0.0)
            * self.parameters.adsorption_time_min
            / 60.0
        )
        self.adsorbent_inventory_kg = (
            co2_per_cycle
            / self.parameters.working_capacity_kg_co2_per_kg_adsorbent
            * self.parameters.number_of_beds
        )
        replacement = (
            self.adsorbent_inventory_kg
            * self.parameters.annual_attrition_fraction
            / self.parameters.operating_hours_per_year
        )
        fresh_adsorbent.imass["PSAAdsorbent"] = replacement
        spent_adsorbent.imass["PSAAdsorbent"] = replacement
        product.T = blowdown.T = purge.T = feed.T
        product.P = max(1_000.0, feed.P - self.parameters.pressure_drop_pa)
        blowdown.P = purge.P = self.parameters.blowdown_pressure_bar * 1e5
        product.phase = blowdown.phase = purge.phase = "g"
        fresh_adsorbent.T = spent_adsorbent.T = feed.T
        fresh_adsorbent.P = spent_adsorbent.P = feed.P
        fresh_adsorbent.phase = spent_adsorbent.phase = "s"

    def _design(self):
        feed = self.ins[0]
        product, blowdown, purge, _ = self.outs
        offgas_nm3 = normal_volume_nm3_hr(blowdown) + normal_volume_nm3_hr(purge)
        vacuum_power = offgas_nm3 * self.parameters.vacuum_electricity_kwh_nm3_offgas
        co2_per_cycle = (
            self.captured_kg_hr.get("CarbonDioxide", 0.0)
            * self.parameters.adsorption_time_min
            / 60.0
        )
        self.design_results["Feed gas"] = normal_volume_nm3_hr(feed)
        self.design_results["Product gas"] = normal_volume_nm3_hr(product)
        self.design_results["Blowdown gas"] = normal_volume_nm3_hr(blowdown)
        self.design_results["Purge gas"] = normal_volume_nm3_hr(purge)
        self.design_results["CO2 captured per cycle"] = co2_per_cycle
        self.design_results["Adsorbent inventory"] = self.adsorbent_inventory_kg
        self.design_results["Bed volume"] = self.adsorbent_inventory_kg / self.parameters.bulk_density_kg_m3
        self.design_results["Cycle time"] = self.parameters.adsorption_time_min + self.parameters.regeneration_time_min
        self.design_results["Methane loss"] = float(blowdown.imass["Methane"] + purge.imass["Methane"])
        self.design_results["Vacuum electricity"] = vacuum_power
        self.power_utility.consumption = vacuum_power


@dataclass(frozen=True)
class MEAParameters:
    absorber_pressure_bar: float
    compressor_efficiency: float
    absorber_temperature_c: float
    co2_capture_fraction: float
    methane_absorption_fraction: float
    h2s_capture_fraction: float
    lean_loading_mol_co2_per_mol_mea: float
    rich_loading_mol_co2_per_mol_mea: float
    solution_mea_mass_fraction: float
    absorber_pressure_drop_pa: float
    absorption_heat_kj_per_mol_co2: float
    rich_lean_heat_recovery_fraction: float
    solvent_heat_capacity_kj_kg_k: float
    stripper_temperature_c: float
    stripper_pressure_bar: float
    regeneration_energy_mj_per_kg_co2: float
    h2s_regeneration_fraction: float
    water_overhead_fraction: float
    reflux_fraction: float
    solvent_loss_fraction: float
    degradation_fraction: float
    antifoam_kg_per_kg_mea: float
    lean_cooler_temperature_c: float
    pump_pressure_bar: float
    absorber_velocity_m_s: float
    absorber_packing_height_m: float
    stripper_velocity_m_s: float
    stripper_packing_height_m: float

    def validate(self) -> None:
        positive(self.absorber_pressure_bar, "MEA absorber pressure")
        bounded_fraction(self.compressor_efficiency, "C641 efficiency", positive_lower=True)
        bounded_fraction(self.co2_capture_fraction, "MEA CO2 capture")
        bounded_fraction(self.methane_absorption_fraction, "MEA methane absorption")
        bounded_fraction(self.h2s_capture_fraction, "MEA H2S capture")
        nonnegative(self.lean_loading_mol_co2_per_mol_mea, "MEA lean loading")
        positive(self.rich_loading_mol_co2_per_mol_mea, "MEA rich loading")
        if self.rich_loading_mol_co2_per_mol_mea <= self.lean_loading_mol_co2_per_mol_mea:
            raise ValueError("MEA rich loading must exceed lean loading.")
        bounded_fraction(self.solution_mea_mass_fraction, "MEA solution fraction", positive_lower=True)
        nonnegative(self.absorber_pressure_drop_pa, "MEA absorber pressure drop")
        positive(self.absorption_heat_kj_per_mol_co2, "MEA absorption heat")
        bounded_fraction(self.rich_lean_heat_recovery_fraction, "MEA heat recovery")
        positive(self.solvent_heat_capacity_kj_kg_k, "MEA solution heat capacity")
        positive(self.stripper_pressure_bar, "MEA stripper pressure")
        positive(self.regeneration_energy_mj_per_kg_co2, "MEA regeneration energy")
        for name, value in (
            ("H2S regeneration", self.h2s_regeneration_fraction),
            ("water overhead", self.water_overhead_fraction),
            ("reflux fraction", self.reflux_fraction),
            ("solvent loss", self.solvent_loss_fraction),
            ("MEA degradation", self.degradation_fraction),
        ):
            bounded_fraction(value, name)
        nonnegative(self.antifoam_kg_per_kg_mea, "MEA antifoam dose")
        positive(self.pump_pressure_bar, "MEA pump pressure")
        positive(self.absorber_velocity_m_s, "MEA absorber velocity")
        positive(self.absorber_packing_height_m, "MEA absorber packing height")
        positive(self.stripper_velocity_m_s, "MEA stripper velocity")
        positive(self.stripper_packing_height_m, "MEA stripper packing height")


def mea_parameters_from_mapping(values: Mapping[str, object]) -> MEAParameters:
    parameters = MEAParameters(
        _required_float(values, "mea_absorber_pressure_bar"),
        _required_float(values, "mea_compressor_efficiency"),
        _required_float(values, "mea_absorber_temperature_c"),
        _required_float(values, "mea_co2_capture_fraction"),
        _required_float(values, "mea_methane_absorption_fraction"),
        _required_float(values, "mea_h2s_capture_fraction"),
        _required_float(values, "mea_lean_loading_mol_co2_per_mol_mea"),
        _required_float(values, "mea_rich_loading_mol_co2_per_mol_mea"),
        _required_float(values, "mea_solution_mass_fraction"),
        _required_float(values, "mea_absorber_pressure_drop_pa"),
        _required_float(values, "mea_absorption_heat_kj_per_mol_co2"),
        _required_float(values, "mea_rich_lean_heat_recovery_fraction"),
        _required_float(values, "mea_solvent_heat_capacity_kj_kg_k"),
        _required_float(values, "mea_stripper_temperature_c"),
        _required_float(values, "mea_stripper_pressure_bar"),
        _required_float(values, "mea_regeneration_energy_mj_per_kg_co2"),
        _required_float(values, "mea_h2s_regeneration_fraction"),
        _required_float(values, "mea_water_overhead_fraction"),
        _required_float(values, "mea_reflux_fraction"),
        _required_float(values, "mea_solvent_loss_fraction"),
        _required_float(values, "mea_degradation_fraction"),
        float(values.get("mea_antifoam_kg_per_kg_mea", 0.0)),
        _required_float(values, "mea_lean_cooler_temperature_c"),
        _required_float(values, "mea_pump_pressure_bar"),
        _required_float(values, "mea_absorber_velocity_m_s"),
        _required_float(values, "mea_absorber_packing_height_m"),
        _required_float(values, "mea_stripper_velocity_m_s"),
        _required_float(values, "mea_stripper_packing_height_m"),
    )
    parameters.validate()
    return parameters


class MEAAbsorber(bst.Unit):
    """Equivalent-loading MEA absorber with recycle-dependent makeup."""

    _N_ins = 3
    _N_outs = 2
    line = "MEA absorber"
    _units = {
        "Gas feed": "Nm3/hr",
        "CO2 captured": "kg/hr",
        "MEA circulation": "kg/hr",
        "Fresh MEA": "kg/hr",
        "Fresh water": "kg/hr",
        "Lean loading": "mol/mol",
        "Rich loading": "mol/mol",
        "Column diameter": "m",
        "Packing height": "m",
        "Absorption cooling": "kW",
    }

    def _init(self, parameters: MEAParameters):
        parameters.validate()
        self.parameters = parameters
        self.co2_captured_kg_hr = 0.0
        self.lean_loading = 0.0
        self.rich_loading = 0.0
        self.absorption_cooling_kw = 0.0
        self.warnings = (
            "A641 uses equivalent CO2 loading and does not claim rigorous MEA electrolyte speciation or rate-based mass transfer.",
        )
        self.limitation_ids = ("LIM-P6-011",)

    def _run(self):
        gas_feed, lean_recycle, fresh_makeup = self.ins
        biomethane, rich_solvent = self.outs
        biomethane.copy_like(gas_feed)
        fresh_makeup.empty()
        rich_solvent.empty()
        self.co2_captured_kg_hr = (
            float(gas_feed.imass["CarbonDioxide"])
            * self.parameters.co2_capture_fraction
        )
        co2_captured_kmol = self.co2_captured_kg_hr / chemicals.CarbonDioxide.MW
        loading_delta = (
            self.parameters.rich_loading_mol_co2_per_mol_mea
            - self.parameters.lean_loading_mol_co2_per_mol_mea
        )
        required_mea_kmol = co2_captured_kmol / loading_delta if loading_delta else 0.0
        required_mea_mass = required_mea_kmol * chemicals.Monoethanolamine.MW
        recycle_mea_mass = float(lean_recycle.imass["Monoethanolamine"])
        fresh_mea = max(0.0, required_mea_mass - recycle_mea_mass)
        target_solution_mass = (
            required_mea_mass / self.parameters.solution_mea_mass_fraction
            if required_mea_mass
            else 0.0
        )
        target_water = max(0.0, target_solution_mass - required_mea_mass)
        fresh_water = max(0.0, target_water - float(lean_recycle.imass["Water"]))
        fresh_makeup.imass["Monoethanolamine"] = fresh_mea
        fresh_makeup.imass["Water"] = fresh_water
        fresh_makeup.imass["Antifoam"] = (
            required_mea_mass * self.parameters.antifoam_kg_per_kg_mea
        )
        for source in (lean_recycle, fresh_makeup):
            for ID in chemicals.IDs:
                rich_solvent.imass[ID] += float(source.imass[ID])
        biomethane.imass["CarbonDioxide"] -= self.co2_captured_kg_hr
        rich_solvent.imass["CarbonDioxide"] += self.co2_captured_kg_hr
        for ID, fraction in (
            ("Methane", self.parameters.methane_absorption_fraction),
            ("HydrogenSulfide", self.parameters.h2s_capture_fraction),
        ):
            absorbed = float(biomethane.imass[ID]) * fraction
            biomethane.imass[ID] -= absorbed
            rich_solvent.imass[ID] += absorbed
        mea_kmol = float(rich_solvent.imol["Monoethanolamine"])
        self.lean_loading = (
            float(lean_recycle.imol["CarbonDioxide"])
            / float(lean_recycle.imol["Monoethanolamine"])
            if float(lean_recycle.imol["Monoethanolamine"])
            else 0.0
        )
        self.rich_loading = (
            float(rich_solvent.imol["CarbonDioxide"]) / mea_kmol
            if mea_kmol
            else 0.0
        )
        biomethane.T = rich_solvent.T = self.parameters.absorber_temperature_c + 273.15
        biomethane.P = max(1_000.0, gas_feed.P - self.parameters.absorber_pressure_drop_pa)
        rich_solvent.P = biomethane.P
        biomethane.phase = "g"
        rich_solvent.phase = "l"
        fresh_makeup.T = lean_recycle.T if lean_recycle.F_mass else biomethane.T
        fresh_makeup.P = rich_solvent.P
        fresh_makeup.phase = "l"

    def _design(self):
        gas_feed, _, fresh_makeup = self.ins
        rich_solvent = self.outs[1]
        geometry = size_gas_column(
            gas_kmol_hr=_gas_kmol(gas_feed),
            temperature_k=gas_feed.T,
            pressure_pa=gas_feed.P,
            design_superficial_velocity_m_s=self.parameters.absorber_velocity_m_s,
            packing_height_m=self.parameters.absorber_packing_height_m,
        )
        co2_kmol = self.co2_captured_kg_hr / chemicals.CarbonDioxide.MW
        self.absorption_cooling_kw = (
            co2_kmol
            * 1000.0
            * self.parameters.absorption_heat_kj_per_mol_co2
            / 3600.0
        )
        if self.absorption_cooling_kw:
            self.add_heat_utility(
                -self.absorption_cooling_kw * 3600.0,
                rich_solvent.T + 10.0,
                rich_solvent.T,
            )
        self.design_results["Gas feed"] = normal_volume_nm3_hr(gas_feed)
        self.design_results["CO2 captured"] = self.co2_captured_kg_hr
        self.design_results["MEA circulation"] = float(rich_solvent.imass["Monoethanolamine"])
        self.design_results["Fresh MEA"] = float(fresh_makeup.imass["Monoethanolamine"])
        self.design_results["Fresh water"] = float(fresh_makeup.imass["Water"])
        self.design_results["Lean loading"] = self.lean_loading
        self.design_results["Rich loading"] = self.rich_loading
        self.design_results["Column diameter"] = geometry.diameter_m
        self.design_results["Packing height"] = geometry.packing_height_m
        self.design_results["Absorption cooling"] = self.absorption_cooling_kw
        self.power_utility.consumption = 0.0


class RichLeanHeatExchanger(bst.Unit):
    """Calculate the rich side of the linked E641 solvent heat recovery."""

    _N_ins = 1
    _N_outs = 1
    line = "MEA rich-lean exchanger (rich side)"
    _units = {
        "Recovered heat": "kW",
        "Rich inlet temperature": "degC",
        "Rich outlet temperature": "degC",
        "Assumed lean inlet temperature": "degC",
    }

    def _init(self, parameters: MEAParameters):
        parameters.validate()
        self.parameters = parameters
        self.recovered_heat_kw = 0.0
        self.limitation_ids = ("LIM-P6-011",)

    def _run(self):
        rich_in = self.ins[0]
        heated_rich = self.outs[0]
        heated_rich.copy_like(rich_in)
        cp = self.parameters.solvent_heat_capacity_kj_kg_k
        c_rich = rich_in.F_mass * cp
        lean_in_temperature = self.parameters.stripper_temperature_c + 273.15
        available = max(0.0, lean_in_temperature - rich_in.T)
        duty_kj_hr = (
            c_rich
            * available
            * self.parameters.rich_lean_heat_recovery_fraction
        )
        self.recovered_heat_kw = duty_kj_hr / 3600.0
        if c_rich:
            heated_rich.T = rich_in.T + duty_kj_hr / c_rich
        heated_rich.P = rich_in.P
        heated_rich.phase = "l"

    def _design(self):
        rich_in = self.ins[0]
        heated_rich = self.outs[0]
        self.design_results["Recovered heat"] = self.recovered_heat_kw
        self.design_results["Rich inlet temperature"] = rich_in.T - 273.15
        self.design_results["Rich outlet temperature"] = heated_rich.T - 273.15
        self.design_results["Assumed lean inlet temperature"] = (
            self.parameters.stripper_temperature_c
        )
        self.power_utility.consumption = 0.0


class LeanHeatRecovery(bst.Unit):
    """Apply E641 recovered duty to the lean side without a second tear stream."""

    _N_ins = 1
    _N_outs = 1
    line = "MEA rich-lean exchanger (lean side)"
    _units = {
        "Transferred heat": "kW",
        "Lean inlet temperature": "degC",
        "Lean outlet temperature": "degC",
    }

    def _init(
        self,
        parameters: MEAParameters,
        *,
        rich_side: RichLeanHeatExchanger,
    ):
        parameters.validate()
        self.parameters = parameters
        self.rich_side = rich_side
        self.transferred_heat_kw = 0.0
        self.limitation_ids = ("LIM-P6-011",)

    def _run(self):
        lean_in = self.ins[0]
        cooled_lean = self.outs[0]
        cooled_lean.copy_like(lean_in)
        heat_capacity_kj_hr_k = (
            lean_in.F_mass * self.parameters.solvent_heat_capacity_kj_kg_k
        )
        maximum_duty_kw = (
            heat_capacity_kj_hr_k
            * max(0.0, lean_in.T - self.parameters.absorber_temperature_c - 273.15)
            / 3600.0
        )
        self.transferred_heat_kw = min(
            self.rich_side.recovered_heat_kw,
            maximum_duty_kw,
        )
        if heat_capacity_kj_hr_k:
            cooled_lean.T = (
                lean_in.T
                - self.transferred_heat_kw * 3600.0 / heat_capacity_kj_hr_k
            )
        cooled_lean.P = lean_in.P
        cooled_lean.phase = "l"

    def _design(self):
        lean_in = self.ins[0]
        cooled_lean = self.outs[0]
        self.design_results["Transferred heat"] = self.transferred_heat_kw
        self.design_results["Lean inlet temperature"] = lean_in.T - 273.15
        self.design_results["Lean outlet temperature"] = cooled_lean.T - 273.15
        self.power_utility.consumption = 0.0


class MEAReboiler(bst.Unit):
    """Supply specified Level-1 solvent-regeneration heat before stripping."""

    _N_ins = 1
    _N_outs = 1
    line = "MEA regenerator reboiler"
    _units = {
        "CO2 releasable": "kg/hr",
        "Reboiler duty": "kW",
        "Outlet temperature": "degC",
    }

    def _init(self, parameters: MEAParameters):
        parameters.validate()
        self.parameters = parameters
        self.reboiler_duty_kw = 0.0
        self.co2_releasable_kg_hr = 0.0
        self.limitation_ids = ("LIM-P6-011", "LIM-P6-012")

    def _run(self):
        rich = self.ins[0]
        heated = self.outs[0]
        heated.copy_like(rich)
        heated.T = self.parameters.stripper_temperature_c + 273.15
        heated.P = self.parameters.stripper_pressure_bar * 1e5
        heated.phase = "l"

    def _design(self):
        rich = self.ins[0]
        heated = self.outs[0]
        mea_kmol = float(rich.imol["Monoethanolamine"])
        lean_co2_kmol = mea_kmol * self.parameters.lean_loading_mol_co2_per_mol_mea
        current_co2_kmol = float(rich.imol["CarbonDioxide"])
        releasable_kmol = max(0.0, current_co2_kmol - lean_co2_kmol)
        self.co2_releasable_kg_hr = releasable_kmol * chemicals.CarbonDioxide.MW
        self.reboiler_duty_kw = (
            self.co2_releasable_kg_hr
            * self.parameters.regeneration_energy_mj_per_kg_co2
            / 3.6
        )
        if self.reboiler_duty_kw:
            self.add_heat_utility(
                self.reboiler_duty_kw * 3600.0,
                rich.T,
                heated.T,
            )
        self.design_results["CO2 releasable"] = self.co2_releasable_kg_hr
        self.design_results["Reboiler duty"] = self.reboiler_duty_kw
        self.design_results["Outlet temperature"] = heated.T - 273.15
        self.power_utility.consumption = 0.0


class MEAStripper(bst.Unit):
    """Regenerate lean MEA and assign overhead gas and solvent losses."""

    _N_ins = 1
    _N_outs = 3
    line = "MEA stripper"
    _units = {
        "CO2 released": "kg/hr",
        "H2S released": "kg/hr",
        "Methane released": "kg/hr",
        "Lean loading": "mol/mol",
        "MEA degradation": "kg/hr",
        "Physical solvent loss": "kg/hr",
        "Column diameter": "m",
        "Packing height": "m",
    }

    def _init(self, parameters: MEAParameters):
        parameters.validate()
        self.parameters = parameters
        self.co2_released_kg_hr = 0.0
        self.degraded_mea_kg_hr = 0.0
        self.physical_loss_kg_hr = 0.0
        self.lean_loading = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.limitation_ids = ("LIM-P6-011", "LIM-P6-013")

    def _run(self):
        heated_rich = self.ins[0]
        lean, overhead, spent = self.outs
        lean.copy_like(heated_rich)
        overhead.empty()
        spent.empty()
        mea_kmol = float(lean.imol["Monoethanolamine"])
        target_co2_kmol = mea_kmol * self.parameters.lean_loading_mol_co2_per_mol_mea
        current_co2_kmol = float(lean.imol["CarbonDioxide"])
        released_co2_kmol = max(0.0, current_co2_kmol - target_co2_kmol)
        lean.imol["CarbonDioxide"] -= released_co2_kmol
        overhead.imol["CarbonDioxide"] = released_co2_kmol
        self.co2_released_kg_hr = released_co2_kmol * chemicals.CarbonDioxide.MW
        h2s_released = (
            float(lean.imass["HydrogenSulfide"])
            * self.parameters.h2s_regeneration_fraction
        )
        lean.imass["HydrogenSulfide"] -= h2s_released
        overhead.imass["HydrogenSulfide"] = h2s_released
        methane_released = float(lean.imass["Methane"])
        lean.imass["Methane"] = 0.0
        overhead.imass["Methane"] = methane_released
        water_overhead = (
            float(lean.imass["Water"]) * self.parameters.water_overhead_fraction
        )
        lean.imass["Water"] -= water_overhead
        overhead.imass["Water"] = water_overhead
        self.degraded_mea_kg_hr = (
            float(lean.imass["Monoethanolamine"])
            * self.parameters.degradation_fraction
        )
        lean.imass["Monoethanolamine"] -= self.degraded_mea_kg_hr
        spent.imass["MEADegradationProducts"] = self.degraded_mea_kg_hr
        mea_loss = (
            float(lean.imass["Monoethanolamine"])
            * self.parameters.solvent_loss_fraction
        )
        water_loss = (
            float(lean.imass["Water"])
            * self.parameters.solvent_loss_fraction
        )
        lean.imass["Monoethanolamine"] -= mea_loss
        lean.imass["Water"] -= water_loss
        spent.imass["Monoethanolamine"] = mea_loss
        spent.imass["Water"] = water_loss
        self.physical_loss_kg_hr = mea_loss + water_loss
        self.reaction_delta_kg_hr = {ID: 0.0 for ID in chemicals.IDs}
        self.reaction_delta_kg_hr["Monoethanolamine"] = -self.degraded_mea_kg_hr
        self.reaction_delta_kg_hr["MEADegradationProducts"] = self.degraded_mea_kg_hr
        remaining_mea_kmol = float(lean.imol["Monoethanolamine"])
        self.lean_loading = (
            float(lean.imol["CarbonDioxide"]) / remaining_mea_kmol
            if remaining_mea_kmol
            else 0.0
        )
        pressure = self.parameters.stripper_pressure_bar * 1e5
        for stream, phase in ((lean, "l"), (overhead, "g"), (spent, "l")):
            stream.T = heated_rich.T
            stream.P = pressure
            stream.phase = phase

    def _design(self):
        lean, overhead, _ = self.outs
        geometry = size_gas_column(
            gas_kmol_hr=_gas_kmol(overhead),
            temperature_k=overhead.T,
            pressure_pa=overhead.P,
            design_superficial_velocity_m_s=self.parameters.stripper_velocity_m_s,
            packing_height_m=self.parameters.stripper_packing_height_m,
        )
        self.design_results["CO2 released"] = self.co2_released_kg_hr
        self.design_results["H2S released"] = float(overhead.imass["HydrogenSulfide"])
        self.design_results["Methane released"] = float(overhead.imass["Methane"])
        self.design_results["Lean loading"] = self.lean_loading
        self.design_results["MEA degradation"] = self.degraded_mea_kg_hr
        self.design_results["Physical solvent loss"] = self.physical_loss_kg_hr
        self.design_results["Column diameter"] = geometry.diameter_m
        self.design_results["Packing height"] = geometry.packing_height_m
        self.power_utility.consumption = 0.0


class RefluxCondenser(bst.Unit):
    """Condense stripper overhead water and split reflux from wastewater."""

    _N_ins = 1
    _N_outs = 3
    line = "MEA reflux condenser"
    _units = {
        "Reject gas": "Nm3/hr",
        "Condensed water": "kg/hr",
        "Reflux": "kg/hr",
        "Wastewater": "kg/hr",
        "Cooling duty": "kW",
    }

    def _init(self, parameters: MEAParameters):
        parameters.validate()
        self.parameters = parameters
        self.cooling_duty_kw = 0.0
        self.limitation_ids = ("LIM-P6-011",)

    def _run(self):
        overhead = self.ins[0]
        reject, reflux, wastewater = self.outs
        reject.copy_like(overhead)
        reflux.empty()
        wastewater.empty()
        condensed_water = float(reject.imass["Water"])
        reject.imass["Water"] = 0.0
        reflux.imass["Water"] = condensed_water * self.parameters.reflux_fraction
        wastewater.imass["Water"] = condensed_water - float(reflux.imass["Water"])
        target_temperature = self.parameters.absorber_temperature_c + 273.15
        for stream, phase in ((reject, "g"), (reflux, "l"), (wastewater, "l")):
            stream.T = target_temperature
            stream.P = overhead.P
            stream.phase = phase

    def _design(self):
        overhead = self.ins[0]
        reject, reflux, wastewater = self.outs
        condensed = reflux.F_mass + wastewater.F_mass
        sensible_kw = (
            overhead.F_mass
            * self.parameters.solvent_heat_capacity_kj_kg_k
            * max(0.0, overhead.T - reject.T)
            / 3600.0
        )
        latent_kw = condensed * 2257.0 / 3600.0
        self.cooling_duty_kw = sensible_kw + latent_kw
        if self.cooling_duty_kw:
            self.add_heat_utility(
                -self.cooling_duty_kw * 3600.0,
                overhead.T,
                reject.T,
            )
        self.design_results["Reject gas"] = normal_volume_nm3_hr(reject)
        self.design_results["Condensed water"] = condensed
        self.design_results["Reflux"] = reflux.F_mass
        self.design_results["Wastewater"] = wastewater.F_mass
        self.design_results["Cooling duty"] = self.cooling_duty_kw
        self.power_utility.consumption = 0.0
