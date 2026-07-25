"""Raw-biogas conditioning units for GreenHub Phase 6.

BioSTEAM does not provide project-specific H2S media, ammonia scrubber, or
siloxane-filter models. These custom units implement bounded Level-1 physics
and explicit chemistry where applicable. They deliberately have no CAPEX
correlations until vendor or validated design data are available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import biosteam as bst

from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.phase5_specifications import bounded_fraction, nonnegative, positive
from Greenhub.phase6_specifications import (
    actual_gas_volume_m3_hr,
    gas_vessel_volume_m3,
    normal_volume_nm3_hr,
    saturated_water_kmol_hr,
)


def _required_float(values: Mapping[str, object], name: str) -> float:
    try:
        return float(values[name])
    except KeyError as error:
        raise ValueError(f"Missing required Phase 6 parameter '{name}'.") from error


def _required_text(values: Mapping[str, object], name: str) -> str:
    try:
        value = str(values[name]).strip()
    except KeyError as error:
        raise ValueError(f"Missing required Phase 6 parameter '{name}'.") from error
    if not value:
        raise ValueError(f"Phase 6 parameter '{name}' cannot be blank.")
    return value


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


def _stream_component_flows(stream) -> dict[str, float]:
    return {ID: float(stream.imass[ID]) for ID in chemicals.IDs}


def _mix_into(output, streams) -> None:
    output.empty()
    streams = tuple(streams)
    if not streams:
        return
    for stream in streams:
        for ID in chemicals.IDs:
            output.imass[ID] += float(stream.imass[ID])
    total = sum(stream.F_mass for stream in streams)
    output.T = (
        sum(stream.F_mass * stream.T for stream in streams) / total
        if total
        else streams[0].T
    )
    output.P = min(stream.P for stream in streams)


def _reaction_delta(unit) -> dict[str, float]:
    inlet = {ID: 0.0 for ID in chemicals.IDs}
    outlet = {ID: 0.0 for ID in chemicals.IDs}
    for stream in unit.ins:
        for ID in chemicals.IDs:
            inlet[ID] += float(stream.imass[ID])
    for stream in unit.outs:
        for ID in chemicals.IDs:
            outlet[ID] += float(stream.imass[ID])
    return {ID: outlet[ID] - inlet[ID] for ID in chemicals.IDs}


@dataclass(frozen=True)
class GasCoolingParameters:
    enabled: bool
    outlet_temperature_c: float
    pressure_drop_pa: float
    heat_capacity_kj_kg_k: float
    water_latent_heat_kj_kg: float
    fan_power_kw_per_nm3_hr: float

    def validate(self) -> None:
        if not -45.0 <= self.outlet_temperature_c <= 80.0:
            raise ValueError("G601 outlet temperature must be -45 through 80 degC.")
        nonnegative(self.pressure_drop_pa, "G601 pressure drop")
        positive(self.heat_capacity_kj_kg_k, "Biogas heat capacity")
        positive(self.water_latent_heat_kj_kg, "Water latent heat")
        nonnegative(self.fan_power_kw_per_nm3_hr, "G601 fan power factor")


@dataclass(frozen=True)
class CondensateParameters:
    enabled: bool
    residence_time_min: float
    liquid_carryover_fraction: float
    ammonia_dissolved_fraction: float
    h2s_dissolved_fraction: float
    co2_dissolved_fraction: float

    def validate(self) -> None:
        nonnegative(self.residence_time_min, "S601 residence time")
        for name, value in (
            ("S601 liquid carryover", self.liquid_carryover_fraction),
            ("S601 ammonia dissolution", self.ammonia_dissolved_fraction),
            ("S601 H2S dissolution", self.h2s_dissolved_fraction),
            ("S601 CO2 dissolution", self.co2_dissolved_fraction),
        ):
            bounded_fraction(value, name)


@dataclass(frozen=True)
class H2SRemovalParameters:
    enabled: bool
    technology: str
    removal_fraction: float
    pressure_drop_pa: float
    empty_bed_contact_time_s: float
    media_bulk_density_kg_m3: float
    media_capacity_kg_h2s_per_kg: float
    air_oxygen_fraction: float
    oxygen_utilization_fraction: float

    def validate(self) -> None:
        if self.technology not in {"activated_carbon", "iron_sponge", "biological", "bypass"}:
            raise ValueError(
                "R601 technology must be activated_carbon, iron_sponge, biological, or bypass."
            )
        bounded_fraction(self.removal_fraction, "R601 H2S removal")
        nonnegative(self.pressure_drop_pa, "R601 pressure drop")
        nonnegative(self.empty_bed_contact_time_s, "R601 contact time")
        positive(self.media_bulk_density_kg_m3, "R601 media bulk density")
        positive(self.media_capacity_kg_h2s_per_kg, "R601 media capacity")
        bounded_fraction(
            self.air_oxygen_fraction,
            "Air oxygen fraction",
            positive_lower=True,
            open_upper=True,
        )
        bounded_fraction(
            self.oxygen_utilization_fraction,
            "Biological oxygen utilization",
            positive_lower=True,
        )


@dataclass(frozen=True)
class AmmoniaRemovalParameters:
    enabled: bool
    technology: str
    removal_fraction: float
    water_to_gas_kg_nm3: float
    co2_absorption_fraction: float
    h2s_absorption_fraction: float
    methane_absorption_fraction: float
    acid_type: str
    acid_purity: float
    pressure_drop_pa: float

    def validate(self) -> None:
        if self.technology not in {"water_wash", "acid_scrubber", "bypass"}:
            raise ValueError("R602 technology must be water_wash, acid_scrubber, or bypass.")
        bounded_fraction(self.removal_fraction, "R602 ammonia removal")
        nonnegative(self.water_to_gas_kg_nm3, "R602 water-to-gas ratio")
        for name, value in (
            ("R602 CO2 absorption", self.co2_absorption_fraction),
            ("R602 H2S absorption", self.h2s_absorption_fraction),
            ("R602 methane absorption", self.methane_absorption_fraction),
        ):
            bounded_fraction(value, name)
        if self.acid_type not in {"HydrochloricAcid", "SulfuricAcid"}:
            raise ValueError("R602 acid must be HydrochloricAcid or SulfuricAcid.")
        bounded_fraction(self.acid_purity, "R602 acid purity", positive_lower=True)
        nonnegative(self.pressure_drop_pa, "R602 pressure drop")


@dataclass(frozen=True)
class FilterParameters:
    enabled: bool
    particulate_removal_fraction: float
    siloxane_removal_fraction: float
    pressure_drop_pa: float
    contact_time_s: float
    media_bulk_density_kg_m3: float
    media_capacity_kg_contaminant_per_kg: float
    fan_efficiency: float

    def validate(self) -> None:
        bounded_fraction(self.particulate_removal_fraction, "F601 particulate removal")
        bounded_fraction(self.siloxane_removal_fraction, "F601 siloxane removal")
        nonnegative(self.pressure_drop_pa, "F601 pressure drop")
        nonnegative(self.contact_time_s, "F601 contact time")
        positive(self.media_bulk_density_kg_m3, "F601 media bulk density")
        positive(self.media_capacity_kg_contaminant_per_kg, "F601 media capacity")
        bounded_fraction(
            self.fan_efficiency,
            "F601 fan efficiency",
            positive_lower=True,
        )


@dataclass(frozen=True)
class PretreatmentParameterSet:
    cooling: GasCoolingParameters
    condensate: CondensateParameters
    h2s: H2SRemovalParameters
    ammonia: AmmoniaRemovalParameters
    filtration: FilterParameters

    def validate(self) -> None:
        self.cooling.validate()
        self.condensate.validate()
        self.h2s.validate()
        self.ammonia.validate()
        self.filtration.validate()


def pretreatment_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    enabled: bool,
) -> PretreatmentParameterSet:
    """Build and validate all G601-S601-R601-R602-F601 parameters."""

    cooling = GasCoolingParameters(
        enabled and _required_bool(values, "gas_cooler_enabled"),
        _required_float(values, "gas_cooler_outlet_temperature_c"),
        _required_float(values, "gas_cooler_pressure_drop_pa"),
        _required_float(values, "biogas_heat_capacity_kj_kg_k"),
        _required_float(values, "water_latent_heat_kj_kg"),
        _required_float(values, "gas_cooler_fan_power_kw_per_nm3_hr"),
    )
    condensate = CondensateParameters(
        enabled and _required_bool(values, "condensate_separator_enabled"),
        _required_float(values, "condensate_separator_residence_time_min"),
        _required_float(values, "condensate_liquid_carryover_fraction"),
        _required_float(values, "condensate_ammonia_dissolved_fraction"),
        _required_float(values, "condensate_h2s_dissolved_fraction"),
        _required_float(values, "condensate_co2_dissolved_fraction"),
    )
    h2s = H2SRemovalParameters(
        enabled and _required_bool(values, "h2s_removal_enabled"),
        _required_text(values, "h2s_removal_technology"),
        _required_float(values, "h2s_removal_fraction"),
        _required_float(values, "h2s_unit_pressure_drop_pa"),
        _required_float(values, "h2s_empty_bed_contact_time_s"),
        _required_float(values, "h2s_media_bulk_density_kg_m3"),
        _required_float(values, "h2s_media_capacity_kg_h2s_per_kg"),
        _required_float(values, "air_oxygen_mol_fraction"),
        _required_float(values, "biological_oxygen_utilization_fraction"),
    )
    ammonia = AmmoniaRemovalParameters(
        enabled and _required_bool(values, "ammonia_removal_enabled"),
        _required_text(values, "ammonia_removal_technology"),
        _required_float(values, "ammonia_removal_fraction"),
        _required_float(values, "ammonia_scrubber_water_kg_per_nm3"),
        _required_float(values, "ammonia_scrubber_co2_absorption_fraction"),
        _required_float(values, "ammonia_scrubber_h2s_absorption_fraction"),
        _required_float(values, "ammonia_scrubber_methane_absorption_fraction"),
        _required_text(values, "ammonia_scrubber_acid_type"),
        _required_float(values, "ammonia_scrubber_acid_purity"),
        _required_float(values, "ammonia_unit_pressure_drop_pa"),
    )
    filtration = FilterParameters(
        enabled and _required_bool(values, "particle_filter_enabled"),
        _required_float(values, "particle_removal_fraction"),
        _required_float(values, "siloxane_removal_fraction"),
        _required_float(values, "filter_pressure_drop_pa"),
        _required_float(values, "filter_contact_time_s"),
        _required_float(values, "filter_media_bulk_density_kg_m3"),
        _required_float(values, "filter_media_capacity_kg_contaminant_per_kg"),
        _required_float(values, "filter_fan_efficiency"),
    )
    parameters = PretreatmentParameterSet(
        cooling,
        condensate,
        h2s,
        ammonia,
        filtration,
    )
    parameters.validate()
    return parameters


class RawBiogasCooler(bst.Unit):
    """Cool raw gas and calculate equilibrium moisture condensation duty."""

    _N_ins = 1
    _N_outs = 1
    line = "Raw-biogas cooler"
    _units = {
        "Wet gas flow": "Nm3/hr",
        "Outlet temperature": "degC",
        "Pressure drop": "Pa",
        "Water expected to condense": "kg/hr",
        "Sensible cooling": "kW",
        "Latent cooling": "kW",
        "Total cooling": "kW",
    }

    def _init(self, parameters: GasCoolingParameters):
        parameters.validate()
        self.parameters = parameters
        self.condensable_water_kg_hr = 0.0
        self.cooling_duty_kw = 0.0
        self.warnings = (
            "G601 uses a Magnus pure-water saturation pressure and ideal-gas humidity; mixed-gas fugacity is not solved.",
        )
        self.limitation_ids = ("LIM-P6-001",)

    def _run(self):
        feed = self.ins[0]
        cooled = self.outs[0]
        cooled.copy_like(feed)
        if self.parameters.enabled:
            cooled.T = self.parameters.outlet_temperature_c + 273.15
            cooled.P = max(1_000.0, feed.P - self.parameters.pressure_drop_pa)
        cooled.phase = "g"

    def _design(self):
        feed = self.ins[0]
        cooled = self.outs[0]
        dry_kmol = sum(
            float(feed.imol[ID])
            for ID in COMPONENT_GROUPS["biogas_components"]
        )
        saturated_water = (
            saturated_water_kmol_hr(dry_kmol, cooled.T, cooled.P)
            if self.parameters.enabled and dry_kmol
            else float(feed.imol["Water"])
        )
        self.condensable_water_kg_hr = max(
            0.0,
            (float(feed.imol["Water"]) - saturated_water) * chemicals.Water.MW,
        )
        temperature_drop = max(0.0, feed.T - cooled.T)
        sensible_kw = (
            feed.F_mass
            * self.parameters.heat_capacity_kj_kg_k
            * temperature_drop
            / 3600.0
            if self.parameters.enabled
            else 0.0
        )
        latent_kw = (
            self.condensable_water_kg_hr
            * self.parameters.water_latent_heat_kj_kg
            / 3600.0
        )
        self.cooling_duty_kw = sensible_kw + latent_kw
        if self.cooling_duty_kw:
            self.add_heat_utility(
                -self.cooling_duty_kw * 3600.0,
                feed.T,
                cooled.T,
            )
        self.power_utility.consumption = (
            normal_volume_nm3_hr(feed)
            * self.parameters.fan_power_kw_per_nm3_hr
            if self.parameters.enabled
            else 0.0
        )
        self.design_results["Wet gas flow"] = normal_volume_nm3_hr(feed)
        self.design_results["Outlet temperature"] = cooled.T - 273.15
        self.design_results["Pressure drop"] = feed.P - cooled.P
        self.design_results["Water expected to condense"] = self.condensable_water_kg_hr
        self.design_results["Sensible cooling"] = sensible_kw
        self.design_results["Latent cooling"] = latent_kw
        self.design_results["Total cooling"] = self.cooling_duty_kw


class CondensateSeparator(bst.Unit):
    """Realize the G601 equilibrium moisture knock-out and disengage liquid."""

    _N_ins = 1
    _N_outs = 2
    line = "Biogas condensate separator"
    _units = {
        "Gas flow": "Nm3/hr",
        "Condensate": "kg/hr",
        "Water removed": "kg/hr",
        "Gas residence time": "min",
        "Working volume": "m3",
        "Liquid carryover": "fraction",
    }

    def _init(self, parameters: CondensateParameters):
        parameters.validate()
        self.parameters = parameters
        self.water_removed_kg_hr = 0.0
        self.warnings = (
            "S601 uses specified trace-gas dissolution fractions; Henry-law and droplet-size distributions require data.",
        )
        self.limitation_ids = ("LIM-P6-001", "LIM-P6-002")

    def _run(self):
        feed = self.ins[0]
        dry_gas, condensate = self.outs
        dry_gas.copy_like(feed)
        condensate.empty()
        if self.parameters.enabled:
            dry_kmol = sum(
                float(feed.imol[ID])
                for ID in COMPONENT_GROUPS["biogas_components"]
            )
            saturated = saturated_water_kmol_hr(dry_kmol, feed.T, feed.P)
            equilibrium_water = max(0.0, float(feed.imol["Water"]) - saturated)
            separated_water = equilibrium_water * (
                1.0 - self.parameters.liquid_carryover_fraction
            )
            condensate.imol["Water"] = separated_water
            dry_gas.imol["Water"] -= separated_water
            if separated_water > 0.0:
                for ID, fraction in (
                    ("Ammonia", self.parameters.ammonia_dissolved_fraction),
                    ("HydrogenSulfide", self.parameters.h2s_dissolved_fraction),
                    ("CarbonDioxide", self.parameters.co2_dissolved_fraction),
                ):
                    transferred = float(dry_gas.imass[ID]) * fraction
                    dry_gas.imass[ID] -= transferred
                    condensate.imass[ID] += transferred
        self.water_removed_kg_hr = float(condensate.imass["Water"])
        for stream, phase in ((dry_gas, "g"), (condensate, "l")):
            stream.T = feed.T
            stream.P = feed.P
            stream.phase = phase

    def _design(self):
        feed = self.ins[0]
        dry_gas, condensate = self.outs
        gas_kmol = sum(float(dry_gas.imol[ID]) for ID in chemicals.IDs)
        volume = gas_vessel_volume_m3(
            gas_kmol_hr=gas_kmol,
            temperature_k=feed.T,
            pressure_pa=feed.P,
            residence_time_min=self.parameters.residence_time_min,
        )
        self.design_results["Gas flow"] = normal_volume_nm3_hr(dry_gas)
        self.design_results["Condensate"] = condensate.F_mass
        self.design_results["Water removed"] = self.water_removed_kg_hr
        self.design_results["Gas residence time"] = self.parameters.residence_time_min
        self.design_results["Working volume"] = volume
        self.design_results["Liquid carryover"] = self.parameters.liquid_carryover_fraction
        self.power_utility.consumption = 0.0


class HydrogenSulfideRemoval(bst.Unit):
    """Remove H2S by selected carbon, iron-sponge, or biological mechanism."""

    _N_ins = 3
    _N_outs = 2
    line = "Hydrogen-sulfide removal"
    _units = {
        "Gas flow": "Nm3/hr",
        "H2S entering": "kg/hr",
        "H2S removed": "kg/hr",
        "Removal": "fraction",
        "Bed volume": "m3",
        "Media consumption": "kg/hr",
        "Oxygen supplied": "kg/hr",
        "Pressure drop": "Pa",
    }

    def _init(self, parameters: H2SRemovalParameters):
        parameters.validate()
        self.parameters = parameters
        self.h2s_removed_kg_hr = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "Activated-carbon mode retains intact H2S-equivalent mass and does not invent oxidation products.",
            "Iron-sponge mode uses Fe2O3 + 3 H2S -> Fe2S3 + 3 H2O without hydration or mixed iron phases.",
            "Biological mode uses complete H2S-to-elemental-sulfur stoichiometry with no kinetic or biomass-growth claim.",
        )
        self.limitation_ids = ("LIM-P6-003", "LIM-P6-004")

    def _run(self):
        feed, fresh_media, oxidation_air = self.ins
        cleaned, spent_media = self.outs
        cleaned.copy_like(feed)
        fresh_media.empty()
        oxidation_air.empty()
        spent_media.empty()
        self.h2s_removed_kg_hr = 0.0
        active = self.parameters.enabled and self.parameters.technology != "bypass"
        if active:
            h2s_entering = float(feed.imass["HydrogenSulfide"])
            self.h2s_removed_kg_hr = h2s_entering * self.parameters.removal_fraction
            h2s_kmol = self.h2s_removed_kg_hr / chemicals.HydrogenSulfide.MW
            cleaned.imass["HydrogenSulfide"] -= self.h2s_removed_kg_hr
            if self.parameters.technology == "activated_carbon":
                media = self.h2s_removed_kg_hr / self.parameters.media_capacity_kg_h2s_per_kg
                fresh_media.imass["ActivatedCarbon"] = media
                spent_media.imass["ActivatedCarbon"] = media
                spent_media.imass["CapturedHydrogenSulfide"] = self.h2s_removed_kg_hr
            elif self.parameters.technology == "iron_sponge":
                reaction_kmol = h2s_kmol / 3.0
                fresh_media.imol["FerricOxide"] = reaction_kmol
                spent_media.imol["FerricSulfide"] = reaction_kmol
                spent_media.imol["Water"] = h2s_kmol
            elif self.parameters.technology == "biological":
                oxygen_consumed_kmol = 0.5 * h2s_kmol
                oxygen_fed_kmol = oxygen_consumed_kmol / self.parameters.oxygen_utilization_fraction
                nitrogen_kmol = oxygen_fed_kmol * (
                    1.0 - self.parameters.air_oxygen_fraction
                ) / self.parameters.air_oxygen_fraction
                oxidation_air.imol["Oxygen"] = oxygen_fed_kmol
                oxidation_air.imol["Nitrogen"] = nitrogen_kmol
                cleaned.imol["Oxygen"] += oxygen_fed_kmol - oxygen_consumed_kmol
                cleaned.imol["Nitrogen"] += nitrogen_kmol
                cleaned.imol["Water"] += h2s_kmol
                spent_media.imol["ElementalSulfur"] = h2s_kmol
        cleaned.P = max(1_000.0, feed.P - (self.parameters.pressure_drop_pa if active else 0.0))
        cleaned.T = feed.T
        cleaned.phase = "g"
        for stream in (fresh_media, oxidation_air, spent_media):
            stream.T = feed.T
            stream.P = cleaned.P
        fresh_media.phase = "s"
        oxidation_air.phase = "g"
        spent_media.phase = "s"
        self.reaction_delta_kg_hr = _reaction_delta(self)

    def _design(self):
        feed, fresh_media, oxidation_air = self.ins
        cleaned = self.outs[0]
        gas_kmol = sum(float(feed.imol[ID]) for ID in chemicals.IDs)
        gas_flow = actual_gas_volume_m3_hr(gas_kmol, feed.T, feed.P)
        bed_volume = (
            gas_flow * self.parameters.empty_bed_contact_time_s / 3600.0
            if self.parameters.enabled
            else 0.0
        )
        h2s_entering = float(feed.imass["HydrogenSulfide"])
        self.design_results["Gas flow"] = normal_volume_nm3_hr(feed)
        self.design_results["H2S entering"] = h2s_entering
        self.design_results["H2S removed"] = self.h2s_removed_kg_hr
        self.design_results["Removal"] = self.h2s_removed_kg_hr / h2s_entering if h2s_entering else 0.0
        self.design_results["Bed volume"] = bed_volume
        self.design_results["Media consumption"] = fresh_media.F_mass
        self.design_results["Oxygen supplied"] = float(oxidation_air.imass["Oxygen"])
        self.design_results["Pressure drop"] = feed.P - cleaned.P
        self.power_utility.consumption = 0.0


class AmmoniaRemoval(bst.Unit):
    """Remove ammonia by physical water wash or stoichiometric acid scrubbing."""

    _N_ins = 3
    _N_outs = 2
    line = "Biogas ammonia removal"
    _units = {
        "Gas flow": "Nm3/hr",
        "Ammonia entering": "kg/hr",
        "Ammonia removed": "kg/hr",
        "Water demand": "kg/hr",
        "Pure acid demand": "kg/hr",
        "Scrubber liquor": "kg/hr",
        "Methane absorbed": "kg/hr",
        "Pressure drop": "Pa",
    }

    def _init(self, parameters: AmmoniaRemovalParameters):
        parameters.validate()
        self.parameters = parameters
        self.ammonia_removed_kg_hr = 0.0
        self.methane_absorbed_kg_hr = 0.0
        self.reaction_delta_kg_hr: dict[str, float] = {}
        self.warnings = (
            "R602 water-wash partitions are empirical and do not solve pH-dependent Henry equilibrium.",
            "Acid mode uses molecular salt bookkeeping and does not claim rigorous electrolyte speciation.",
        )
        self.limitation_ids = ("LIM-P6-005",)

    def _run(self):
        feed, wash_water, acid_solution = self.ins
        cleaned, scrubber_liquor = self.outs
        cleaned.copy_like(feed)
        wash_water.empty()
        acid_solution.empty()
        scrubber_liquor.empty()
        self.ammonia_removed_kg_hr = 0.0
        self.methane_absorbed_kg_hr = 0.0
        active = self.parameters.enabled and self.parameters.technology != "bypass"
        if active:
            wash_water.imass["Water"] = (
                normal_volume_nm3_hr(feed)
                * self.parameters.water_to_gas_kg_nm3
            )
            scrubber_liquor.imass["Water"] = float(wash_water.imass["Water"])
            self.ammonia_removed_kg_hr = (
                float(cleaned.imass["Ammonia"])
                * self.parameters.removal_fraction
            )
            if self.parameters.technology == "acid_scrubber":
                ammonia_kmol = self.ammonia_removed_kg_hr / chemicals.Ammonia.MW
                if self.parameters.acid_type == "HydrochloricAcid":
                    acid_kmol = ammonia_kmol
                    product_id = "AmmoniumChloride"
                    product_kmol = ammonia_kmol
                else:
                    acid_kmol = ammonia_kmol / 2.0
                    product_id = "AmmoniumSulfate"
                    product_kmol = acid_kmol
                pure_acid_mass = acid_kmol * chemicals[self.parameters.acid_type].MW
                acid_solution.imass[self.parameters.acid_type] = pure_acid_mass
                acid_solution.imass["Water"] = pure_acid_mass * (
                    1.0 / self.parameters.acid_purity - 1.0
                )
                scrubber_liquor.imass["Water"] += float(acid_solution.imass["Water"])
                scrubber_liquor.imol[product_id] = product_kmol
            else:
                scrubber_liquor.imass["Ammonia"] = self.ammonia_removed_kg_hr
            cleaned.imass["Ammonia"] -= self.ammonia_removed_kg_hr
            for ID, fraction in (
                ("CarbonDioxide", self.parameters.co2_absorption_fraction),
                ("HydrogenSulfide", self.parameters.h2s_absorption_fraction),
                ("Methane", self.parameters.methane_absorption_fraction),
            ):
                transferred = float(cleaned.imass[ID]) * fraction
                cleaned.imass[ID] -= transferred
                scrubber_liquor.imass[ID] += transferred
                if ID == "Methane":
                    self.methane_absorbed_kg_hr = transferred
        cleaned.P = max(1_000.0, feed.P - (self.parameters.pressure_drop_pa if active else 0.0))
        cleaned.T = feed.T
        cleaned.phase = "g"
        for stream in (wash_water, acid_solution, scrubber_liquor):
            stream.T = feed.T
            stream.P = cleaned.P
            stream.phase = "l"
        self.reaction_delta_kg_hr = _reaction_delta(self)

    def _design(self):
        feed, wash_water, acid_solution = self.ins
        cleaned, scrubber_liquor = self.outs
        entering = float(feed.imass["Ammonia"])
        self.design_results["Gas flow"] = normal_volume_nm3_hr(feed)
        self.design_results["Ammonia entering"] = entering
        self.design_results["Ammonia removed"] = self.ammonia_removed_kg_hr
        self.design_results["Water demand"] = wash_water.F_mass
        self.design_results["Pure acid demand"] = (
            float(acid_solution.imass[self.parameters.acid_type])
            if self.parameters.technology == "acid_scrubber"
            else 0.0
        )
        self.design_results["Scrubber liquor"] = scrubber_liquor.F_mass
        self.design_results["Methane absorbed"] = self.methane_absorbed_kg_hr
        self.design_results["Pressure drop"] = feed.P - cleaned.P
        self.power_utility.consumption = 0.0


class ParticleSiloxaneFilter(bst.Unit):
    """Remove entrained particulates and the aggregate siloxane marker."""

    _N_ins = 2
    _N_outs = 2
    line = "Particle and siloxane filter"
    _units = {
        "Gas flow": "Nm3/hr",
        "Particles removed": "kg/hr",
        "Siloxanes removed": "kg/hr",
        "Bed volume": "m3",
        "Bed media inventory": "kg",
        "Equivalent media replacement": "kg/hr",
        "Pressure drop": "Pa",
        "Fan electricity": "kW",
    }

    def _init(self, parameters: FilterParameters):
        parameters.validate()
        self.parameters = parameters
        self.particles_removed_kg_hr = 0.0
        self.siloxanes_removed_kg_hr = 0.0
        self.warnings = (
            "F601 uses a D5-equivalent aggregate siloxane marker and empirical media capacity; no competitive adsorption is claimed.",
        )
        self.limitation_ids = ("LIM-P6-006",)

    def _run(self):
        feed, fresh_media = self.ins
        conditioned, spent_media = self.outs
        conditioned.copy_like(feed)
        fresh_media.empty()
        spent_media.empty()
        self.particles_removed_kg_hr = 0.0
        self.siloxanes_removed_kg_hr = 0.0
        if self.parameters.enabled:
            for ID in COMPONENT_GROUPS["phase6_particulates"]:
                removed = (
                    float(conditioned.imass[ID])
                    * self.parameters.particulate_removal_fraction
                )
                conditioned.imass[ID] -= removed
                spent_media.imass[ID] += removed
                self.particles_removed_kg_hr += removed
            self.siloxanes_removed_kg_hr = (
                float(conditioned.imass["Siloxanes"])
                * self.parameters.siloxane_removal_fraction
            )
            conditioned.imass["Siloxanes"] -= self.siloxanes_removed_kg_hr
            spent_media.imass["Siloxanes"] += self.siloxanes_removed_kg_hr
            captured = self.particles_removed_kg_hr + self.siloxanes_removed_kg_hr
            replacement = captured / self.parameters.media_capacity_kg_contaminant_per_kg
            fresh_media.imass["ActivatedCarbon"] = replacement
            spent_media.imass["ActivatedCarbon"] = replacement
        conditioned.P = max(
            1_000.0,
            feed.P - (self.parameters.pressure_drop_pa if self.parameters.enabled else 0.0),
        )
        conditioned.T = feed.T
        conditioned.phase = "g"
        for stream in (fresh_media, spent_media):
            stream.T = feed.T
            stream.P = conditioned.P
            stream.phase = "s"

    def _design(self):
        feed = self.ins[0]
        fresh_media = self.ins[1]
        conditioned = self.outs[0]
        gas_kmol = sum(float(feed.imol[ID]) for ID in chemicals.IDs)
        gas_m3_hr = actual_gas_volume_m3_hr(gas_kmol, feed.T, feed.P)
        bed_volume = (
            gas_m3_hr * self.parameters.contact_time_s / 3600.0
            if self.parameters.enabled
            else 0.0
        )
        fan_power = (
            gas_m3_hr
            / 3600.0
            * self.parameters.pressure_drop_pa
            / self.parameters.fan_efficiency
            / 1000.0
            if self.parameters.enabled
            else 0.0
        )
        self.design_results["Gas flow"] = normal_volume_nm3_hr(feed)
        self.design_results["Particles removed"] = self.particles_removed_kg_hr
        self.design_results["Siloxanes removed"] = self.siloxanes_removed_kg_hr
        self.design_results["Bed volume"] = bed_volume
        self.design_results["Bed media inventory"] = (
            bed_volume * self.parameters.media_bulk_density_kg_m3
        )
        self.design_results["Equivalent media replacement"] = fresh_media.F_mass
        self.design_results["Pressure drop"] = feed.P - conditioned.P
        self.design_results["Fan electricity"] = fan_power
        self.power_utility.consumption = fan_power
