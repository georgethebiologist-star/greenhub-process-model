"""Custom BioSTEAM units for GreenHub Phase 3 front-end processing."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import ceil
from typing import Mapping

import biosteam as bst

from Greenhub.chemicals import chemicals
from Greenhub.component_groups import COMPONENT_GROUPS
from Greenhub.component_metadata import COMPONENT_METADATA
from Greenhub.specifications import solve_two_outlet_water_partition


def _bounded_fraction(value: float, name: str, *, upper_open: bool = False) -> float:
    number = float(value)
    valid = 0.0 <= number < 1.0 if upper_open else 0.0 <= number <= 1.0
    if not valid:
        bound = "[0, 1)" if upper_open else "[0, 1]"
        raise ValueError(f"{name} must be within {bound}; received {number}.")
    return number


def _nonnegative(value: float, name: str) -> float:
    number = float(value)
    if number < 0.0:
        raise ValueError(f"{name} must be non-negative; received {number}.")
    return number


def _required_float(values: Mapping[str, object], name: str) -> float:
    if name not in values or values[name] is None:
        raise ValueError(f"Missing required Phase 3 parameter '{name}'.")
    try:
        return float(values[name])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Parameter '{name}' must be numeric.") from error


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


def _set_conditions(stream, source) -> None:
    stream.T = source.T
    stream.P = source.P
    stream.phase = source.phase


@dataclass(frozen=True)
class PreparationParameters:
    """Optional coarse-cleaning assumptions; all removals go to rejects."""

    enabled: bool = True
    component_removal_fractions: Mapping[str, float] = field(default_factory=dict)
    group_removal_fractions: Mapping[str, float] = field(default_factory=dict)
    biomass_loss_fraction: float = 0.0
    electricity_kwh_per_t_wet: float = 0.0
    capacity_t_per_h: float | None = None

    def validate(self) -> None:
        _bounded_fraction(self.biomass_loss_fraction, "Preparation biomass loss")
        _nonnegative(self.electricity_kwh_per_t_wet, "Preparation specific electricity")
        if self.capacity_t_per_h is not None and self.capacity_t_per_h <= 0.0:
            raise ValueError("Preparation capacity must be positive when supplied.")
        unknown_components = set(self.component_removal_fractions) - set(chemicals.IDs)
        unknown_groups = set(self.group_removal_fractions) - set(COMPONENT_GROUPS)
        if unknown_components or unknown_groups:
            raise KeyError(
                "Unknown preparation classifications: "
                f"components={sorted(unknown_components)}, groups={sorted(unknown_groups)}."
            )
        for name, value in self.component_removal_fractions.items():
            _bounded_fraction(value, f"Preparation removal for {name}")
        for name, value in self.group_removal_fractions.items():
            _bounded_fraction(value, f"Preparation removal for group {name}")


@dataclass(frozen=True)
class PEFParameters:
    """Mass-transfer, temperature, and electrical assumptions for PEF."""

    specific_energy_kwh_per_t_wet: float
    electric_field_strength_kv_per_cm: float
    pulse_width_us: float
    number_of_pulses: float
    treatment_time_s: float
    treatment_temperature_c: float | None
    temperature_rise_c: float | None
    temperature_mode: str
    thermal_retention_efficiency: float
    effective_heat_capacity_kj_per_kg_k: float
    cell_disintegration_index: float
    soluble_protein_release_fraction: float
    suspended_protein_solubilization_fraction: float
    sugar_release_fraction: float
    soluble_cod_increase_fraction: float
    dissolved_nitrogen_release_fraction: float
    dissolved_phosphorus_release_fraction: float
    potassium_release_fraction: float
    juice_yield_improvement_fraction: float
    mass_loss_fraction: float = 0.0
    capacity_t_per_h: float | None = None

    def validate(self) -> None:
        for name in (
            "specific_energy_kwh_per_t_wet",
            "electric_field_strength_kv_per_cm",
            "pulse_width_us",
            "number_of_pulses",
            "treatment_time_s",
            "effective_heat_capacity_kj_per_kg_k",
        ):
            _nonnegative(getattr(self, name), name)
        if self.effective_heat_capacity_kj_per_kg_k <= 0.0:
            raise ValueError("PEF effective heat capacity must be positive.")
        for name in (
            "thermal_retention_efficiency",
            "cell_disintegration_index",
            "soluble_protein_release_fraction",
            "suspended_protein_solubilization_fraction",
            "sugar_release_fraction",
            "soluble_cod_increase_fraction",
            "dissolved_nitrogen_release_fraction",
            "dissolved_phosphorus_release_fraction",
            "potassium_release_fraction",
            "juice_yield_improvement_fraction",
            "mass_loss_fraction",
        ):
            _bounded_fraction(getattr(self, name), name)
        if self.temperature_mode not in {"specified", "calculated"}:
            raise ValueError("PEF temperature_mode must be 'specified' or 'calculated'.")
        if self.temperature_mode == "specified" and self.treatment_temperature_c is None and self.temperature_rise_c is None:
            raise ValueError("Specified PEF temperature mode requires treatment temperature or temperature rise.")
        if self.capacity_t_per_h is not None and self.capacity_t_per_h <= 0.0:
            raise ValueError("PEF capacity must be positive when supplied.")


@dataclass(frozen=True)
class ScrewPressParameters:
    """Screw-press recoveries using fraction-to-juice convention."""

    juice_yield_kg_per_kg_wet_feed: float | None
    liquid_recovery_fraction: float
    cake_moisture_fraction: float | None
    dry_solids_recovery_to_cake: float
    water_recovery_to_juice: float
    soluble_protein_recovery_to_juice: float
    suspended_protein_recovery_to_juice: float
    sugar_recovery_to_juice: float
    organic_acid_recovery_to_juice: float
    amino_acid_recovery_to_juice: float
    ammonium_recovery_to_juice: float
    phosphate_recovery_to_juice: float
    potassium_recovery_to_juice: float
    soluble_salt_recovery_to_juice: float
    cellulose_recovery_to_cake: float
    hemicellulose_recovery_to_cake: float
    lignin_recovery_to_cake: float
    inert_solids_recovery_to_cake: float
    contaminant_recovery_to_cake: float
    press_electricity_kwh_per_t_wet: float
    press_capacity_t_per_h: float | None
    constraint_priority: str = "cake_moisture_priority"
    component_recoveries_to_juice: Mapping[str, float] = field(default_factory=dict)
    group_recoveries_to_juice: Mapping[str, float] = field(default_factory=dict)

    def validate(self) -> None:
        if self.juice_yield_kg_per_kg_wet_feed is not None:
            _bounded_fraction(self.juice_yield_kg_per_kg_wet_feed, "Press juice yield")
        if self.cake_moisture_fraction is not None:
            _bounded_fraction(self.cake_moisture_fraction, "Cake moisture", upper_open=True)
        for name in (
            "liquid_recovery_fraction",
            "dry_solids_recovery_to_cake",
            "water_recovery_to_juice",
            "soluble_protein_recovery_to_juice",
            "suspended_protein_recovery_to_juice",
            "sugar_recovery_to_juice",
            "organic_acid_recovery_to_juice",
            "amino_acid_recovery_to_juice",
            "ammonium_recovery_to_juice",
            "phosphate_recovery_to_juice",
            "potassium_recovery_to_juice",
            "soluble_salt_recovery_to_juice",
            "cellulose_recovery_to_cake",
            "hemicellulose_recovery_to_cake",
            "lignin_recovery_to_cake",
            "inert_solids_recovery_to_cake",
            "contaminant_recovery_to_cake",
        ):
            _bounded_fraction(getattr(self, name), name)
        _nonnegative(self.press_electricity_kwh_per_t_wet, "Press specific electricity")
        if self.press_capacity_t_per_h is not None and self.press_capacity_t_per_h <= 0.0:
            raise ValueError("Press capacity must be positive when supplied.")
        if self.constraint_priority not in {
            "cake_moisture_priority",
            "juice_yield_priority",
            "reconciliation_mode",
        }:
            raise ValueError("Unknown screw-press constraint priority.")
        for component, fraction in self.component_recoveries_to_juice.items():
            if component not in chemicals.IDs:
                raise KeyError(f"Unknown press component override '{component}'.")
            _bounded_fraction(fraction, f"Press recovery for {component}")
        for group, fraction in self.group_recoveries_to_juice.items():
            if group not in COMPONENT_GROUPS:
                raise KeyError(f"Unknown press group override '{group}'.")
            _bounded_fraction(fraction, f"Press recovery for group {group}")


@dataclass(frozen=True)
class CentrifugeParameters:
    """Primary-centrifuge separation, moisture, capacity, and power data."""

    tss_removal_efficiency: float
    vss_removal_efficiency: float
    suspended_protein_removal_efficiency: float
    soluble_protein_loss_fraction: float
    particulate_cod_removal_efficiency: float
    particulate_p_removal_efficiency: float
    dissolved_p_loss_fraction: float
    heavy_metal_particulate_removal_efficiency: float
    microplastic_removal_efficiency: float
    sand_removal_efficiency: float
    sludge_solids_fraction: float | None
    sludge_moisture_fraction: float | None
    liquid_entrainment_fraction: float
    centrifuge_electricity_kwh_per_m3: float
    throughput_m3_per_h: float | None
    optional_polymer_kg_per_t_ds: float = 0.0
    wash_water_kg_per_kg_feed: float = 0.0
    feed_density_kg_m3: float = 1000.0
    component_splits_to_clarified: Mapping[str, float] = field(default_factory=dict)
    group_splits_to_clarified: Mapping[str, float] = field(default_factory=dict)

    def validate(self) -> None:
        for name in (
            "tss_removal_efficiency",
            "vss_removal_efficiency",
            "suspended_protein_removal_efficiency",
            "soluble_protein_loss_fraction",
            "particulate_cod_removal_efficiency",
            "particulate_p_removal_efficiency",
            "dissolved_p_loss_fraction",
            "heavy_metal_particulate_removal_efficiency",
            "microplastic_removal_efficiency",
            "sand_removal_efficiency",
            "liquid_entrainment_fraction",
        ):
            _bounded_fraction(getattr(self, name), name)
        if self.sludge_solids_fraction is None and self.sludge_moisture_fraction is None:
            raise ValueError("Centrifuge requires sludge solids fraction or sludge moisture.")
        solids = self.sludge_solids_fraction
        moisture = self.sludge_moisture_fraction
        if solids is not None:
            _bounded_fraction(solids, "Sludge solids fraction", upper_open=True)
        if moisture is not None:
            _bounded_fraction(moisture, "Sludge moisture", upper_open=True)
        if solids is not None and moisture is not None and abs(solids + moisture - 1.0) > 1e-6:
            raise ValueError("Sludge solids fraction and moisture conflict; they must sum to one.")
        _nonnegative(self.centrifuge_electricity_kwh_per_m3, "Centrifuge specific electricity")
        _nonnegative(self.optional_polymer_kg_per_t_ds, "Polymer dose")
        _nonnegative(self.wash_water_kg_per_kg_feed, "Wash-water ratio")
        if self.feed_density_kg_m3 <= 0.0:
            raise ValueError("Centrifuge feed density must be positive.")
        if self.throughput_m3_per_h is not None and self.throughput_m3_per_h <= 0.0:
            raise ValueError("Centrifuge equipment capacity must be positive when supplied.")

    @property
    def resolved_sludge_moisture_fraction(self) -> float:
        if self.sludge_moisture_fraction is not None:
            return self.sludge_moisture_fraction
        return 1.0 - float(self.sludge_solids_fraction)


def preparation_parameters_from_mapping(values: Mapping[str, object]) -> PreparationParameters:
    parameters = PreparationParameters(
        enabled=bool(values.get("cleaning_enabled", True)),
        component_removal_fractions={
            "Sand": _optional_float(values, "cleaning_sand_removal_fraction", 0.0),
            "Litter": _optional_float(values, "cleaning_litter_removal_fraction", 0.0),
            "InertSolids": _optional_float(values, "cleaning_inert_removal_fraction", 0.0),
        },
        biomass_loss_fraction=_optional_float(values, "cleaning_biomass_loss_fraction", 0.0),
        electricity_kwh_per_t_wet=_required_float(values, "cleaning_electricity_kwh_per_t_wet"),
        capacity_t_per_h=_optional_float(values, "cleaning_capacity_t_per_h"),
    )
    parameters.validate()
    return parameters


def pef_parameters_from_mapping(values: Mapping[str, object]) -> PEFParameters:
    parameters = PEFParameters(
        specific_energy_kwh_per_t_wet=_required_float(values, "specific_energy_kwh_per_t_wet"),
        electric_field_strength_kv_per_cm=_required_float(values, "electric_field_strength_kv_per_cm"),
        pulse_width_us=_required_float(values, "pulse_width_us"),
        number_of_pulses=_required_float(values, "number_of_pulses"),
        treatment_time_s=_required_float(values, "treatment_time_s"),
        treatment_temperature_c=_optional_float(values, "treatment_temperature_c"),
        temperature_rise_c=_optional_float(values, "temperature_rise_c"),
        temperature_mode=_text(values, "temperature_mode", "specified"),
        thermal_retention_efficiency=_required_float(values, "thermal_retention_efficiency"),
        effective_heat_capacity_kj_per_kg_k=_required_float(values, "effective_heat_capacity_kj_per_kg_k"),
        cell_disintegration_index=_required_float(values, "cell_disintegration_index"),
        soluble_protein_release_fraction=_required_float(values, "soluble_protein_release_fraction"),
        suspended_protein_solubilization_fraction=_required_float(values, "suspended_protein_solubilization_fraction"),
        sugar_release_fraction=_required_float(values, "sugar_release_fraction"),
        soluble_cod_increase_fraction=_required_float(values, "soluble_cod_increase_fraction"),
        dissolved_nitrogen_release_fraction=_required_float(values, "dissolved_nitrogen_release_fraction"),
        dissolved_phosphorus_release_fraction=_required_float(values, "dissolved_phosphorus_release_fraction"),
        potassium_release_fraction=_required_float(values, "potassium_release_fraction"),
        juice_yield_improvement_fraction=_required_float(values, "juice_yield_improvement_fraction"),
        mass_loss_fraction=_optional_float(values, "mass_loss_fraction", 0.0),
        capacity_t_per_h=_optional_float(values, "pef_capacity_t_per_h"),
    )
    parameters.validate()
    return parameters


def press_parameters_from_mapping(
    values: Mapping[str, object],
    *,
    pef: PEFParameters | None = None,
) -> ScrewPressParameters:
    juice_yield = _optional_float(values, "juice_yield_kg_per_kg_wet_feed")
    soluble_protein = _required_float(values, "soluble_protein_recovery_to_juice")
    if pef is not None:
        if juice_yield is not None:
            juice_yield = min(1.0, juice_yield + pef.juice_yield_improvement_fraction)
        soluble_protein = min(
            1.0,
            soluble_protein + pef.soluble_protein_release_fraction * (1.0 - soluble_protein),
        )
    parameters = ScrewPressParameters(
        juice_yield_kg_per_kg_wet_feed=juice_yield,
        liquid_recovery_fraction=_required_float(values, "liquid_recovery_fraction"),
        cake_moisture_fraction=_optional_float(values, "cake_moisture_fraction"),
        dry_solids_recovery_to_cake=_required_float(values, "dry_solids_recovery_to_cake"),
        water_recovery_to_juice=_required_float(values, "water_recovery_to_juice"),
        soluble_protein_recovery_to_juice=soluble_protein,
        suspended_protein_recovery_to_juice=_required_float(values, "suspended_protein_recovery_to_juice"),
        sugar_recovery_to_juice=_required_float(values, "sugar_recovery_to_juice"),
        organic_acid_recovery_to_juice=_required_float(values, "organic_acid_recovery_to_juice"),
        amino_acid_recovery_to_juice=_required_float(values, "amino_acid_recovery_to_juice"),
        ammonium_recovery_to_juice=_required_float(values, "ammonium_recovery_to_juice"),
        phosphate_recovery_to_juice=_required_float(values, "phosphate_recovery_to_juice"),
        potassium_recovery_to_juice=_required_float(values, "potassium_recovery_to_juice"),
        soluble_salt_recovery_to_juice=_required_float(values, "soluble_salt_recovery_to_juice"),
        cellulose_recovery_to_cake=_required_float(values, "cellulose_recovery_to_cake"),
        hemicellulose_recovery_to_cake=_required_float(values, "hemicellulose_recovery_to_cake"),
        lignin_recovery_to_cake=_required_float(values, "lignin_recovery_to_cake"),
        inert_solids_recovery_to_cake=_required_float(values, "inert_solids_recovery_to_cake"),
        contaminant_recovery_to_cake=_required_float(values, "contaminant_recovery_to_cake"),
        press_electricity_kwh_per_t_wet=_required_float(values, "press_electricity_kwh_per_t_wet"),
        press_capacity_t_per_h=_optional_float(values, "press_capacity_t_per_h"),
        constraint_priority=_text(values, "press_constraint_priority", "cake_moisture_priority"),
    )
    parameters.validate()
    return parameters


def centrifuge_parameters_from_mapping(values: Mapping[str, object]) -> CentrifugeParameters:
    parameters = CentrifugeParameters(
        tss_removal_efficiency=_required_float(values, "tss_removal_efficiency"),
        vss_removal_efficiency=_required_float(values, "vss_removal_efficiency"),
        suspended_protein_removal_efficiency=_required_float(values, "suspended_protein_removal_efficiency"),
        soluble_protein_loss_fraction=_required_float(values, "soluble_protein_loss_fraction"),
        particulate_cod_removal_efficiency=_required_float(values, "particulate_cod_removal_efficiency"),
        particulate_p_removal_efficiency=_required_float(values, "particulate_p_removal_efficiency"),
        dissolved_p_loss_fraction=_required_float(values, "dissolved_p_loss_fraction"),
        heavy_metal_particulate_removal_efficiency=_required_float(values, "heavy_metal_particulate_removal_efficiency"),
        microplastic_removal_efficiency=_required_float(values, "microplastic_removal_efficiency"),
        sand_removal_efficiency=_required_float(values, "sand_removal_efficiency"),
        sludge_solids_fraction=_optional_float(values, "sludge_solids_fraction"),
        sludge_moisture_fraction=_optional_float(values, "sludge_moisture_fraction"),
        liquid_entrainment_fraction=_required_float(values, "liquid_entrainment_fraction"),
        centrifuge_electricity_kwh_per_m3=_required_float(values, "centrifuge_electricity_kwh_per_m3"),
        throughput_m3_per_h=_optional_float(values, "centrifuge_capacity_m3_per_h"),
        optional_polymer_kg_per_t_ds=_optional_float(values, "optional_polymer_kg_per_t_ds", 0.0),
        wash_water_kg_per_kg_feed=_optional_float(values, "wash_water_kg_per_kg_feed", 0.0),
        feed_density_kg_m3=_required_float(values, "raw_liquid_density_kg_m3"),
    )
    parameters.validate()
    return parameters


class FeedPreparation(bst.Unit):
    """Optional component-specific cleaning with rejects as outlet 1."""

    _N_ins = 1
    _N_outs = 2
    line = "Feed preparation"
    _units = {
        "Wet throughput": "kg/hr",
        "Wet throughput per train": "t/hr",
        "Equipment count": "-",
        "Reject flow": "kg/hr",
        "Specific electricity": "kWh/t wet",
    }

    def _init(self, parameters: PreparationParameters):
        parameters.validate()
        self.parameters = parameters
        self.partitioning: dict[str, tuple[float, str]] = {}

    def _run(self):
        feed = self.ins[0]
        prepared, rejects = self.outs
        prepared.empty()
        rejects.empty()
        self.partitioning = {}
        for component in chemicals.IDs:
            removal = 0.0
            source = "no_removal"
            if self.parameters.enabled:
                if component in self.parameters.component_removal_fractions:
                    removal = float(self.parameters.component_removal_fractions[component])
                    source = "component_override"
                else:
                    matched = next(
                        (
                            name
                            for name in self.parameters.group_removal_fractions
                            if component in COMPONENT_GROUPS[name]
                        ),
                        None,
                    )
                    if matched:
                        removal = float(self.parameters.group_removal_fractions[matched])
                        source = f"group:{matched}"
                    elif component not in COMPONENT_GROUPS["contaminants"] and component != "Water":
                        removal = self.parameters.biomass_loss_fraction
                        source = "documented_biomass_loss"
            inlet = float(feed.imass[component])
            rejects.imass[component] = inlet * removal
            prepared.imass[component] = inlet - rejects.imass[component]
            self.partitioning[component] = (removal, source)
        _set_conditions(prepared, feed)
        _set_conditions(rejects, feed)

    def _design(self):
        wet_t_h = self.ins[0].F_mass / 1000.0
        count = (
            max(1, ceil(wet_t_h / self.parameters.capacity_t_per_h))
            if self.parameters.capacity_t_per_h and wet_t_h > 0.0
            else (1 if wet_t_h > 0.0 else 0)
        )
        self.design_results["Wet throughput"] = self.ins[0].F_mass
        self.design_results["Wet throughput per train"] = wet_t_h / count if count else 0.0
        self.design_results["Equipment count"] = count
        self.design_results["Reject flow"] = self.outs[1].F_mass
        self.design_results["Specific electricity"] = self.parameters.electricity_kwh_per_t_wet
        self.power_utility.consumption = (
            wet_t_h * self.parameters.electricity_kwh_per_t_wet
            if self.parameters.enabled
            else 0.0
        )


class PulsedElectricField(bst.Unit):
    """Mass-conserving empirical PEF release model with documented losses."""

    _N_ins = 1
    _N_outs = 2
    line = "PEF pretreatment"
    _units = {
        "Wet throughput": "kg/hr",
        "Wet throughput per train": "t/hr",
        "Equipment count": "-",
        "Specific electricity": "kWh/t wet",
        "Electric field strength": "kV/cm",
        "Pulse width": "us",
        "Pulse count": "-",
        "Treatment time": "s",
        "Cell disintegration index": "-",
        "Temperature rise": "degC",
        "Documented mass loss": "kg/hr",
    }

    _TRANSFERS = (
        ("SuspendedProtein", "SolubleProtein", "suspended_protein_solubilization_fraction"),
        ("EntrappedSugars", "Glucose", "sugar_release_fraction"),
        ("ParticulateBiodegradableOrganics", "OtherBiodegradableOrganics", "soluble_cod_increase_fraction"),
        ("ParticulateNitrogen", "OrganicNitrogen", "dissolved_nitrogen_release_fraction"),
        ("ParticulatePhosphorus", "DissolvedPhosphorus", "dissolved_phosphorus_release_fraction"),
        ("ParticulatePotassium", "PotassiumIon", "potassium_release_fraction"),
    )

    def _init(self, parameters: PEFParameters):
        parameters.validate()
        self.parameters = parameters
        self.transfers_kg_hr: dict[str, float] = {}

    def _run(self):
        feed = self.ins[0]
        treated, documented_loss = self.outs
        treated.copy_like(feed)
        self.transfers_kg_hr = {}
        for source, target, parameter_name in self._TRANSFERS:
            fraction = float(getattr(self.parameters, parameter_name))
            if source == "SuspendedProtein":
                fraction *= self.parameters.cell_disintegration_index
            transferred = float(treated.imass[source]) * min(fraction, 1.0)
            treated.imass[source] -= transferred
            treated.imass[target] += transferred
            self.transfers_kg_hr[f"{source}_to_{target}"] = transferred

        documented_loss.copy_like(treated)
        documented_loss.scale(self.parameters.mass_loss_fraction)
        treated.scale(1.0 - self.parameters.mass_loss_fraction)
        _set_conditions(documented_loss, feed)

        if self.parameters.temperature_mode == "specified":
            if self.parameters.treatment_temperature_c is not None:
                treated.T = self.parameters.treatment_temperature_c + 273.15
            else:
                treated.T = feed.T + float(self.parameters.temperature_rise_c)
        else:
            retained_kj_hr = (
                feed.F_mass
                / 1000.0
                * self.parameters.specific_energy_kwh_per_t_wet
                * 3600.0
                * self.parameters.thermal_retention_efficiency
            )
            heat_capacity_flow = feed.F_mass * self.parameters.effective_heat_capacity_kj_per_kg_k
            treated.T = feed.T + (retained_kj_hr / heat_capacity_flow if heat_capacity_flow > 0.0 else 0.0)
        documented_loss.T = treated.T

    def _design(self):
        feed = self.ins[0]
        wet_t_h = feed.F_mass / 1000.0
        count = (
            max(1, ceil(wet_t_h / self.parameters.capacity_t_per_h))
            if self.parameters.capacity_t_per_h and wet_t_h > 0.0
            else (1 if wet_t_h > 0.0 else 0)
        )
        self.design_results["Wet throughput"] = feed.F_mass
        self.design_results["Wet throughput per train"] = wet_t_h / count if count else 0.0
        self.design_results["Equipment count"] = count
        self.design_results["Specific electricity"] = self.parameters.specific_energy_kwh_per_t_wet
        self.design_results["Electric field strength"] = self.parameters.electric_field_strength_kv_per_cm
        self.design_results["Pulse width"] = self.parameters.pulse_width_us
        self.design_results["Pulse count"] = self.parameters.number_of_pulses
        self.design_results["Treatment time"] = self.parameters.treatment_time_s
        self.design_results["Cell disintegration index"] = self.parameters.cell_disintegration_index
        self.design_results["Temperature rise"] = self.outs[0].T - feed.T
        self.design_results["Documented mass loss"] = self.outs[1].F_mass
        self.power_utility.consumption = wet_t_h * self.parameters.specific_energy_kwh_per_t_wet


def resolve_press_recoveries(
    parameters: ScrewPressParameters,
) -> tuple[dict[str, float], dict[str, str], tuple[str, ...]]:
    """Resolve component > group > solubility hierarchy to fraction-to-juice."""

    parameters.validate()
    component = dict(parameters.component_recoveries_to_juice)
    component.update(
        {
            "Cellulose": 1.0 - parameters.cellulose_recovery_to_cake,
            "Hemicellulose": 1.0 - parameters.hemicellulose_recovery_to_cake,
            "Lignin": 1.0 - parameters.lignin_recovery_to_cake,
            "PotassiumIon": parameters.potassium_recovery_to_juice,
            "Ammonium": parameters.ammonium_recovery_to_juice,
            "InertSolids": 1.0 - parameters.inert_solids_recovery_to_cake,
            "SuspendedInertSolids": 1.0 - parameters.inert_solids_recovery_to_cake,
            "Ash": 1.0 - parameters.inert_solids_recovery_to_cake,
            "Sand": 1.0 - parameters.inert_solids_recovery_to_cake,
            "Litter": 1.0 - parameters.contaminant_recovery_to_cake,
        }
    )
    groups = {
        "soluble_proteins": parameters.soluble_protein_recovery_to_juice,
        "suspended_proteins": parameters.suspended_protein_recovery_to_juice,
        "soluble_sugars": parameters.sugar_recovery_to_juice,
        "organic_acids": parameters.organic_acid_recovery_to_juice,
        "amino_acids": parameters.amino_acid_recovery_to_juice,
        "peptides": parameters.amino_acid_recovery_to_juice,
        "dissolved_phosphorus": parameters.phosphate_recovery_to_juice,
        "dissolved_minerals": parameters.soluble_salt_recovery_to_juice,
        "contaminants": 1.0 - parameters.contaminant_recovery_to_cake,
    }
    groups.update(parameters.group_recoveries_to_juice)
    splits: dict[str, float] = {}
    sources: dict[str, str] = {}
    warnings: list[str] = []
    for ID in chemicals.IDs:
        if ID == "Water":
            continue
        if ID in component:
            splits[ID] = float(component[ID])
            sources[ID] = "component_override"
            continue
        matched = next((name for name in groups if ID in COMPONENT_GROUPS[name]), None)
        if matched:
            splits[ID] = float(groups[matched])
            sources[ID] = f"group:{matched}"
            continue
        metadata = COMPONENT_METADATA[ID]
        if metadata.solubility_class == "soluble":
            splits[ID] = parameters.liquid_recovery_fraction
            sources[ID] = "default_soluble"
        elif metadata.particle_class == "suspended" or metadata.default_phase == "s":
            splits[ID] = 1.0 - parameters.dry_solids_recovery_to_cake
            sources[ID] = "default_particulate"
        else:
            splits[ID] = parameters.liquid_recovery_fraction
            sources[ID] = "fallback_unclassified"
            warnings.append(f"Press component '{ID}' is unclassified; soluble default was used.")
    return splits, sources, tuple(warnings)


class ScrewPress(bst.Unit):
    """Component-partitioning press; outlet order is cake then raw liquid."""

    _N_ins = 1
    _N_outs = 2
    line = "Screw press"
    _units = {
        "Wet throughput": "kg/hr",
        "Wet throughput per train": "t/hr",
        "Equipment count": "-",
        "Raw liquid flow": "kg/hr",
        "Fibre cake flow": "kg/hr",
        "Cake moisture": "fraction",
        "Juice yield": "kg/kg wet feed",
        "Specific electricity": "kWh/t wet",
    }

    def _init(self, parameters: ScrewPressParameters):
        parameters.validate()
        self.parameters = parameters
        self.splits_to_juice, self.split_sources, warnings = resolve_press_recoveries(parameters)
        self.warnings = list(warnings)
        self.water_specification_warning: str | None = None

    def _run(self):
        feed = self.ins[0]
        cake, juice = self.outs
        cake.empty()
        juice.empty()
        for ID in chemicals.IDs:
            if ID == "Water":
                continue
            inlet = float(feed.imass[ID])
            to_juice = inlet * self.splits_to_juice[ID]
            juice.imass[ID] = to_juice
            cake.imass[ID] = inlet - to_juice
        water_result = solve_two_outlet_water_partition(
            available_water_kg_hr=float(feed.imass["Water"]),
            solids_nonwater_kg_hr=cake.F_mass,
            liquid_nonwater_kg_hr=juice.F_mass,
            wet_feed_kg_hr=feed.F_mass,
            target_solids_moisture_fraction=self.parameters.cake_moisture_fraction,
            target_liquid_yield_fraction=self.parameters.juice_yield_kg_per_kg_wet_feed,
            priority_mode=self.parameters.constraint_priority,
            fallback_water_recovery_to_liquid=self.parameters.water_recovery_to_juice,
        )
        juice.imass["Water"] = water_result.water_to_liquid_kg_hr
        cake.imass["Water"] = water_result.water_to_solids_kg_hr
        self.water_specification_warning = water_result.warning
        if water_result.warning and water_result.warning not in self.warnings:
            self.warnings.append(water_result.warning)
        _set_conditions(cake, feed)
        _set_conditions(juice, feed)

    def _design(self):
        feed = self.ins[0]
        cake, juice = self.outs
        wet_t_h = feed.F_mass / 1000.0
        count = (
            max(1, ceil(wet_t_h / self.parameters.press_capacity_t_per_h))
            if self.parameters.press_capacity_t_per_h and wet_t_h > 0.0
            else (1 if wet_t_h > 0.0 else 0)
        )
        cake_moisture = float(cake.imass["Water"]) / cake.F_mass if cake.F_mass else 0.0
        self.design_results["Wet throughput"] = feed.F_mass
        self.design_results["Wet throughput per train"] = wet_t_h / count if count else 0.0
        self.design_results["Equipment count"] = count
        self.design_results["Raw liquid flow"] = juice.F_mass
        self.design_results["Fibre cake flow"] = cake.F_mass
        self.design_results["Cake moisture"] = cake_moisture
        self.design_results["Juice yield"] = juice.F_mass / feed.F_mass if feed.F_mass else 0.0
        self.design_results["Specific electricity"] = self.parameters.press_electricity_kwh_per_t_wet
        self.power_utility.consumption = wet_t_h * self.parameters.press_electricity_kwh_per_t_wet


def resolve_centrifuge_splits(
    parameters: CentrifugeParameters,
) -> tuple[dict[str, float], dict[str, str], tuple[str, ...]]:
    """Resolve physical class recoveries as fractions to clarified liquid."""

    parameters.validate()
    component = {
        "SolubleProtein": 1.0 - parameters.soluble_protein_loss_fraction,
        "SuspendedProtein": 1.0 - parameters.suspended_protein_removal_efficiency,
        "ParticulatePhosphorus": 1.0 - parameters.particulate_p_removal_efficiency,
        "HeavyMetals": 1.0 - parameters.heavy_metal_particulate_removal_efficiency,
        "Microplastics": 1.0 - parameters.microplastic_removal_efficiency,
        "Sand": 1.0 - parameters.sand_removal_efficiency,
    }
    component.update(parameters.component_splits_to_clarified)
    groups = {
        "dissolved_phosphorus": 1.0 - parameters.dissolved_p_loss_fraction,
        "particulate_cod_components": 1.0 - parameters.particulate_cod_removal_efficiency,
        "volatile_solids": 1.0 - parameters.vss_removal_efficiency,
        "suspended_solids": 1.0 - parameters.tss_removal_efficiency,
    }
    groups.update(parameters.group_splits_to_clarified)
    splits: dict[str, float] = {}
    sources: dict[str, str] = {}
    warnings: list[str] = []
    for ID in chemicals.IDs:
        if ID == "Water":
            continue
        if ID in component:
            splits[ID] = float(component[ID])
            sources[ID] = "component_override"
            continue
        matched = next((name for name in groups if ID in COMPONENT_GROUPS[name]), None)
        if matched:
            splits[ID] = float(groups[matched])
            sources[ID] = f"group:{matched}"
            continue
        metadata = COMPONENT_METADATA[ID]
        if metadata.solubility_class == "soluble":
            splits[ID] = 0.99
            sources[ID] = "default_soluble"
        elif metadata.particle_class == "suspended" or metadata.default_phase == "s":
            splits[ID] = 1.0 - parameters.tss_removal_efficiency
            sources[ID] = "default_particulate"
        else:
            splits[ID] = 0.99
            sources[ID] = "fallback_unclassified"
            warnings.append(
                f"Centrifuge component '{ID}' is unclassified; soluble default was used."
            )
    return splits, sources, tuple(warnings)


class PrimaryCentrifuge(bst.Unit):
    """Physical primary solids separator with wash/polymer inputs disabled by default."""

    _N_ins = 3
    _N_outs = 2
    line = "Primary centrifuge"
    _units = {
        "Hydraulic throughput": "m3/hr",
        "Hydraulic throughput per train": "m3/hr",
        "Dry-solids load": "kg/hr",
        "Equipment count": "-",
        "Sludge flow": "kg/hr",
        "Sludge moisture": "fraction",
        "Specific electricity": "kWh/m3",
        "Polymer flow": "kg/hr",
        "Wash-water flow": "kg/hr",
    }

    def _init(self, parameters: CentrifugeParameters):
        parameters.validate()
        self.parameters = parameters
        self.splits_to_clarified, self.split_sources, warnings = resolve_centrifuge_splits(parameters)
        self.warnings = list(warnings)

    def _run(self):
        raw_liquid, wash_water, polymer = self.ins
        clarified, sludge = self.outs
        wash_water.empty()
        polymer.empty()
        wash_water.imass["Water"] = raw_liquid.F_mass * self.parameters.wash_water_kg_per_kg_feed
        raw_dry_solids = raw_liquid.F_mass - float(raw_liquid.imass["Water"])
        polymer.imass["Flocculant"] = (
            raw_dry_solids / 1000.0 * self.parameters.optional_polymer_kg_per_t_ds
        )
        _set_conditions(wash_water, raw_liquid)
        _set_conditions(polymer, raw_liquid)

        clarified.empty()
        sludge.empty()
        inlet_by_component = {
            ID: sum(float(stream.imass[ID]) for stream in self.ins)
            for ID in chemicals.IDs
        }
        for ID, inlet in inlet_by_component.items():
            if ID == "Water":
                continue
            to_clarified = inlet * self.splits_to_clarified[ID]
            clarified.imass[ID] = to_clarified
            sludge.imass[ID] = inlet - to_clarified
        total_feed = sum(inlet_by_component.values())
        water_result = solve_two_outlet_water_partition(
            available_water_kg_hr=inlet_by_component["Water"],
            solids_nonwater_kg_hr=sludge.F_mass,
            liquid_nonwater_kg_hr=clarified.F_mass,
            wet_feed_kg_hr=total_feed,
            target_solids_moisture_fraction=self.parameters.resolved_sludge_moisture_fraction,
            priority_mode="cake_moisture_priority",
            fallback_water_recovery_to_liquid=1.0 - self.parameters.liquid_entrainment_fraction,
        )
        clarified.imass["Water"] = water_result.water_to_liquid_kg_hr
        sludge.imass["Water"] = water_result.water_to_solids_kg_hr
        _set_conditions(clarified, raw_liquid)
        _set_conditions(sludge, raw_liquid)

    def _design(self):
        raw_liquid = self.ins[0]
        sludge = self.outs[1]
        total_mass = sum(stream.F_mass for stream in self.ins)
        volume = total_mass / self.parameters.feed_density_kg_m3
        count = (
            max(1, ceil(volume / self.parameters.throughput_m3_per_h))
            if self.parameters.throughput_m3_per_h and volume > 0.0
            else (1 if volume > 0.0 else 0)
        )
        dry_solids = total_mass - sum(float(stream.imass["Water"]) for stream in self.ins)
        moisture = float(sludge.imass["Water"]) / sludge.F_mass if sludge.F_mass else 0.0
        self.design_results["Hydraulic throughput"] = volume
        self.design_results["Hydraulic throughput per train"] = volume / count if count else 0.0
        self.design_results["Dry-solids load"] = dry_solids
        self.design_results["Equipment count"] = count
        self.design_results["Sludge flow"] = sludge.F_mass
        self.design_results["Sludge moisture"] = moisture
        self.design_results["Specific electricity"] = self.parameters.centrifuge_electricity_kwh_per_m3
        self.design_results["Polymer flow"] = self.ins[2].F_mass
        self.design_results["Wash-water flow"] = self.ins[1].F_mass
        self.power_utility.consumption = volume * self.parameters.centrifuge_electricity_kwh_per_m3

