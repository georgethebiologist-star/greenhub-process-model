"""Machine-readable engineering-completeness audit for GreenHub units."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import biosteam as bst

from Greenhub.settings import PROJECT_ROOT, RESULTS_DIR

if TYPE_CHECKING:
    from Greenhub.integration import IntegratedGreenHubModel

VALID_STATES = frozenset(
    {
        "available",
        "calculated",
        "assumed",
        "placeholder",
        "not applicable",
        "missing",
        "not yet implemented",
    }
)

VIRTUAL_CLASSES = frozenset({"Mixer", "Splitter"})
STOICHIOMETRIC_CLASSES = frozenset(
    {
        "NeutralizationMixer",
        "AnaerobicDigester",
        "HydrogenSulfideRemoval",
        "AmmoniaRemoval",
        "StruviteCrystallizer",
        "CalciumPhosphateReactor",
        "AlkalineConditioner",
        "AcidAbsorber",
        "IonExchangeRegeneration",
    }
)
SIMPLIFIED_EQUILIBRIUM_CLASSES = frozenset(
    {
        "ProteinPrecipitation",
        "WaterAbsorber",
        "MembraneStage",
        "PressureSwingAdsorber",
        "MEAAbsorber",
        "MEAStripper",
        "StruviteCrystallizer",
        "CalciumPhosphateReactor",
        "AmmoniaStripper",
        "IonExchangeBed",
    }
)
KINETIC_DATA_NEEDED_CLASSES = frozenset(
    {
        "ProteinPrecipitation",
        "AnaerobicDigester",
        "AmmoniaStripper",
        "IonExchangeBed",
        "NutrientProductDryer",
        "ProteinDryer",
    }
)
POWER_MODEL_CLASSES = frozenset(
    {
        "FeedPreparation",
        "PulsedElectricField",
        "ScrewPress",
        "PrimaryCentrifuge",
        "AcidificationMixer",
        "ProteinPrecipitation",
        "ProteinSeparator",
        "MechanicalDewatering",
        "ProteinDryer",
        "NeutralizationMixer",
        "DigesterFeedConditioner",
        "AnaerobicDigester",
        "RawBiogasCooler",
        "ParticleSiloxaneFilter",
        "WaterRegenerator",
        "PressureSwingAdsorber",
        "IsentropicCompressor",
        "Pump",
        "DigestateEqualization",
        "DigestateSolidLiquidSeparator",
        "CrystalSeparator",
        "AlkalineConditioner",
        "AmmoniaStripper",
        "IonExchangeRegeneration",
        "PotassiumEvaporator",
        "PotassiumMembraneConcentrator",
        "NutrientProductDryer",
    }
)
HEAT_MODEL_CLASSES = frozenset(
    {
        "HXutility",
        "ProteinDryer",
        "AnaerobicDigester",
        "RawBiogasCooler",
        "RichLeanHeatExchanger",
        "LeanHeatRecovery",
        "MEAReboiler",
        "RefluxCondenser",
        "ProcessHeater",
        "AmmoniaStripper",
        "PotassiumEvaporator",
        "NutrientProductDryer",
    }
)
COOLING_MODEL_CLASSES = frozenset(
    {"RawBiogasCooler", "HXutility", "RefluxCondenser"}
)
CHEMICAL_DEMAND_CLASSES = frozenset(
    {
        "AcidificationMixer",
        "NeutralizationMixer",
        "DigesterFeedConditioner",
        "HydrogenSulfideRemoval",
        "AmmoniaRemoval",
        "AlkalineConditioner",
        "AcidAbsorber",
        "IonExchangeRegeneration",
        "StruviteCrystallizer",
        "CalciumPhosphateReactor",
    }
)
WATER_DEMAND_CLASSES = frozenset(
    {
        "PrimaryCentrifuge",
        "CakeWasher",
        "DigesterFeedConditioner",
        "AmmoniaRemoval",
        "WaterAbsorber",
        "WaterRegenerator",
        "NutrientProductWasher",
        "IonExchangeRegeneration",
    }
)
LOSS_MODEL_CLASSES = frozenset(
    {
        "FeedPreparation",
        "PulsedElectricField",
        "ProteinDryer",
        "BiogasDisengagement",
        "RawBiogasCooler",
        "HydrogenSulfideRemoval",
        "AmmoniaRemoval",
        "ParticleSiloxaneFilter",
        "WaterAbsorber",
        "MembraneStage",
        "PressureSwingAdsorber",
        "MEAAbsorber",
        "DigestateEqualization",
        "AmmoniaStripper",
        "PotassiumEvaporator",
        "NutrientProductDryer",
    }
)
E4_CLASSES = frozenset(
    {
        "StorageTank",
        "FeedPreparation",
        "PulsedElectricField",
        "ScrewPress",
        "PrimaryCentrifuge",
        "AcidificationMixer",
        "ProteinPrecipitation",
        "ProteinSeparator",
        "MechanicalDewatering",
        "ProteinDryer",
        "NeutralizationMixer",
        "DigesterFeedConditioner",
        "HXutility",
        "AnaerobicDigester",
        "RawBiogasCooler",
        "ParticleSiloxaneFilter",
        "WaterRegenerator",
        "PressureSwingAdsorber",
        "RichLeanHeatExchanger",
        "LeanHeatRecovery",
        "MEAReboiler",
        "RefluxCondenser",
        "IsentropicCompressor",
        "Pump",
        "DigestateEqualization",
        "DigestateSolidLiquidSeparator",
        "CrystalSeparator",
        "AlkalineConditioner",
        "ProcessHeater",
        "IonExchangeRegeneration",
        "PotassiumEvaporator",
        "PotassiumMembraneConcentrator",
        "NutrientProductDryer",
    }
)
E3_CLASSES = frozenset(
    {
        "WaterAbsorber",
        "MembraneStage",
        "MEAAbsorber",
        "MEAStripper",
        "AmmoniaStripper",
        "IonExchangeBed",
    }
)
E2_CLASSES = STOICHIOMETRIC_CLASSES
E1_CLASSES = frozenset(
    {
        "CakeWasher",
        "BiogasDisengagement",
        "CondensateSeparator",
        "HydrogenSulfideRemoval",
        "AmmoniaRemoval",
        "GasWaterSeparator",
        "WaterFlashTank",
        "StruviteCrystallizer",
        "CalciumPhosphateReactor",
        "NutrientProductWasher",
        "ProductStorage",
    }
)

AREA_RECOMMENDATIONS = {
    "Feed Preparation and Primary Separation": (
        "Measured monthly composition and vendor-validated capacity, separation, power, and cost data.",
        "green biomass screw press centrifuge PEF specific energy vendor cost correlation",
    ),
    "Protein Recovery": (
        "Project titration curves, protein-pool recoveries, membrane or fermentation data where selected, drying trials, and vendor costs.",
        "grass juice protein precipitation pH yield centrifuge drying kinetics equipment cost",
    ),
    "Anaerobic Digestion": (
        "BMP or continuous-reactor data, kinetic calibration, inhibition data, heat-loss validation, and digester quotations.",
        "grass juice anaerobic digestion BMP kinetics ammonia inhibition digester CAPEX",
    ),
    "Biogas Conditioning and Upgrading": (
        "Vendor performance curves, media lifetime, methane-slip measurements, compression duty, CHP definition, and equipment quotations.",
        "biogas water scrubbing methane recovery electricity media replacement CHP cost",
    ),
    "Digestate Treatment and Nutrient Recovery": (
        "Ionic analyses, pH titration, pilot recoveries, product moisture and purity, reagent demand, heat integration, and vendor costs.",
        "digestate struvite ammonia stripping potassium concentration pilot cost heat duty",
    ),
    "Shared Utilities and Supporting Operations": (
        "A defined CHP and plant utility network with temperature levels, efficiencies, availability, and cost basis.",
        "biogas CHP heat integration steam cooling water electricity export GreenHub",
    ),
}

VALIDATION_REFERENCES = {
    "Feed Preparation and Primary Separation": "tests/test_system.py; tests/test_mass_balance.py; tests/test_phase3_mass_balance.py; tests/test_phase3_elemental_balance.py",
    "Protein Recovery": "tests/test_phase4_system.py; tests/test_phase4_mass_balance.py",
    "Anaerobic Digestion": "tests/test_phase5_system.py; tests/test_phase5_mass_balance.py",
    "Biogas Conditioning and Upgrading": "tests/test_phase6_scenarios.py; tests/test_phase6_reporting.py",
    "Digestate Treatment and Nutrient Recovery": "tests/test_phase7_system.py; tests/test_phase7_balance_and_utilities.py",
    "Shared Utilities and Supporting Operations": "not yet implemented",
}


@dataclass(frozen=True)
class AlternativeUnitDefinition:
    """Unit instantiated only by a non-selected or compatibility configuration."""

    unit_id: str
    unit_class: str
    process_area: str
    active_scenarios: str
    factory_reference: str


ALTERNATIVE_UNIT_CATALOG = (
    AlternativeUnitDefinition("T101", "StorageTank", "Feed Preparation and Primary Separation", "legacy foundation", "Greenhub.systems.create_greenhub_system"),
    AlternativeUnitDefinition("S101", "Splitter", "Feed Preparation and Primary Separation", "legacy foundation", "Greenhub.systems.create_greenhub_system"),
    AlternativeUnitDefinition("S609", "Splitter", "Biogas Conditioning and Upgrading", "BG0", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M621", "MembraneStage", "Biogas Conditioning and Upgrading", "BG3", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M622", "MembraneStage", "Biogas Conditioning and Upgrading", "BG3", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("C621", "IsentropicCompressor", "Biogas Conditioning and Upgrading", "BG3", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("E621", "HXutility", "Biogas Conditioning and Upgrading", "BG3", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("D621", "GasWaterSeparator", "Biogas Conditioning and Upgrading", "BG3", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M620", "Mixer", "Biogas Conditioning and Upgrading", "BG3 feed-recycle option", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M628", "Mixer", "Biogas Conditioning and Upgrading", "BG3 stage-recycle option", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("S622", "Splitter", "Biogas Conditioning and Upgrading", "BG3 stage-recycle option", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M629", "Mixer", "Biogas Conditioning and Upgrading", "BG3", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("C631", "IsentropicCompressor", "Biogas Conditioning and Upgrading", "BG4", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("D631", "GasWaterSeparator", "Biogas Conditioning and Upgrading", "BG4", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("A631", "PressureSwingAdsorber", "Biogas Conditioning and Upgrading", "BG4", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M630", "Mixer", "Biogas Conditioning and Upgrading", "BG4 recycle option", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("S631", "Splitter", "Biogas Conditioning and Upgrading", "BG4 recycle option", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M639", "Mixer", "Biogas Conditioning and Upgrading", "BG4", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("C641", "IsentropicCompressor", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("E640", "HXutility", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("A641", "MEAAbsorber", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("E641", "RichLeanHeatExchanger", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("H641", "MEAReboiler", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("A642", "MEAStripper", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("V641", "RefluxCondenser", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("E643", "LeanHeatRecovery", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("P641", "Pump", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("E642", "HXutility", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("M641", "Mixer", "Biogas Conditioning and Upgrading", "BG5", "Greenhub.systems.create_phase6_scenario"),
    AlternativeUnitDefinition("R712", "CalciumPhosphateReactor", "Digestate Treatment and Nutrient Recovery", "NR5", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("S712", "CrystalSeparator", "Digestate Treatment and Nutrient Recovery", "NR5", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("W712", "NutrientProductWasher", "Digestate Treatment and Nutrient Recovery", "NR5", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("D712", "NutrientProductDryer", "Digestate Treatment and Nutrient Recovery", "NR5", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("A731", "IonExchangeBed", "Digestate Treatment and Nutrient Recovery", "NR6", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("R731", "IonExchangeRegeneration", "Digestate Treatment and Nutrient Recovery", "NR6", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("E741", "PotassiumEvaporator", "Digestate Treatment and Nutrient Recovery", "NR7 evaporation", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("M741", "PotassiumMembraneConcentrator", "Digestate Treatment and Nutrient Recovery", "NR7 membrane", "Greenhub.phase7_systems.create_phase7_scenario"),
    AlternativeUnitDefinition("V741", "ProductStorage", "Digestate Treatment and Nutrient Recovery", "NR7", "Greenhub.phase7_systems.create_phase7_scenario"),
)


@dataclass(frozen=True)
class UnitCompletenessRecord:
    """One explicit engineering-completeness row for an active unit."""

    unit_id: str
    unit_class: str
    process_area: str
    active_scenarios: str
    inlet_basis: str
    outlet_basis: str
    mass_model_present: str
    stoichiometry_present: str
    kinetics_present: str
    equilibrium_present: str
    energy_balance_present: str
    heat_duty_present: str
    cooling_duty_present: str
    power_demand_present: str
    power_production_present: str
    design_sizing_present: str
    purchase_cost_present: str
    installed_cost_present: str
    equipment_lifetime_present: str
    maintenance_basis_present: str
    consumables_present: str
    chemical_demand_present: str
    water_demand_present: str
    emissions_or_losses_present: str
    source_references: str
    validation_test_present: str
    current_maturity_level: str
    missing_items: str
    recommended_data: str
    recommended_search_keywords: str
    implementation_priority: str


def _maturity(unit_class: str) -> str:
    if unit_class in E4_CLASSES:
        return "E4"
    if unit_class in E3_CLASSES:
        return "E3"
    if unit_class in E2_CLASSES:
        return "E2"
    if unit_class in E1_CLASSES:
        return "E1"
    return "E0"


def _has_design(unit: object) -> bool:
    unit_design = getattr(type(unit), "_design", None)
    return unit_design is not None and unit_design is not bst.Unit._design


def _stream_basis(streams: object) -> str:
    IDs = [str(stream.ID) for stream in streams]
    return f"kg/hr component mass ({', '.join(IDs)})" if IDs else "not applicable"


def _equipment_lifetime_state(unit: object, virtual: bool) -> str:
    if virtual:
        return "not applicable"
    lifetime = getattr(unit, "equipment_lifetime", None)
    return "available" if lifetime else "missing"


def _cost_state(unit: object, virtual: bool, installed: bool = False) -> str:
    if virtual:
        return "not applicable"
    if installed:
        return "calculated" if float(getattr(unit, "installed_cost", 0.0)) > 0.0 else "missing"
    costs = getattr(unit, "baseline_purchase_costs", {})
    return "calculated" if costs and any(float(value) > 0.0 for value in costs.values()) else "missing"


def _process_area_by_unit(model: "IntegratedGreenHubModel") -> dict[str, str]:
    areas: dict[str, str] = {}
    for view in model.process_areas.values():
        for unit_id in view.units:
            areas[unit_id] = view.name
    return areas


def _missing_items(states: dict[str, str]) -> str:
    missing = [
        name.replace("_present", "").replace("_", " ")
        for name, state in states.items()
        if state in {"missing", "not yet implemented"}
    ]
    return "; ".join(missing) if missing else "none identified at this maturity level"


def build_model_completeness(
    model: "IntegratedGreenHubModel",
) -> tuple[UnitCompletenessRecord, ...]:
    """Classify every unit in the selected connected flowsheet."""

    area_by_unit = _process_area_by_unit(model)
    scenario = model.scenario_configuration
    active_scenarios = f"{scenario.scenario_chain}; order {scenario.process_order}"
    records: list[UnitCompletenessRecord] = []
    for unit_id, unit in model.units.items():
        unit_class = type(unit).__name__
        area = area_by_unit.get(unit_id, "Shared Utilities and Supporting Operations")
        virtual = unit_class in VIRTUAL_CLASSES
        maturity = _maturity(unit_class)
        has_design = _has_design(unit)
        if virtual:
            power_state = "not applicable"
        elif unit_class in POWER_MODEL_CLASSES:
            power_state = "calculated"
        else:
            power_state = "missing"
        heat_state = "calculated" if unit_class in HEAT_MODEL_CLASSES else "not applicable"
        cooling_state = "calculated" if unit_class in COOLING_MODEL_CLASSES else "not applicable"
        if unit_class in KINETIC_DATA_NEEDED_CLASSES:
            kinetics_state = "not yet implemented"
        else:
            kinetics_state = "not applicable"
        if unit_class in SIMPLIFIED_EQUILIBRIUM_CLASSES:
            equilibrium_state = "assumed"
        else:
            equilibrium_state = "not applicable"
        states = {
            "mass_model_present": "available",
            "stoichiometry_present": "calculated" if unit_class in STOICHIOMETRIC_CLASSES else "not applicable",
            "kinetics_present": kinetics_state,
            "equilibrium_present": equilibrium_state,
            "energy_balance_present": "calculated" if unit_class in E4_CLASSES else ("not applicable" if virtual else "not yet implemented"),
            "heat_duty_present": heat_state,
            "cooling_duty_present": cooling_state,
            "power_demand_present": power_state,
            "power_production_present": "not applicable",
            "design_sizing_present": "calculated" if has_design and bool(unit.design_results) else ("available" if has_design else ("not applicable" if virtual else "missing")),
            "purchase_cost_present": _cost_state(unit, virtual),
            "installed_cost_present": _cost_state(unit, virtual, installed=True),
            "equipment_lifetime_present": _equipment_lifetime_state(unit, virtual),
            "maintenance_basis_present": "not applicable" if virtual else "missing",
            "consumables_present": "calculated" if unit_class in CHEMICAL_DEMAND_CLASSES | WATER_DEMAND_CLASSES else ("not applicable" if virtual else "missing"),
            "chemical_demand_present": "calculated" if unit_class in CHEMICAL_DEMAND_CLASSES else "not applicable",
            "water_demand_present": "calculated" if unit_class in WATER_DEMAND_CLASSES else "not applicable",
            "emissions_or_losses_present": "calculated" if unit_class in LOSS_MODEL_CLASSES else "not applicable",
        }
        recommendation, keywords = AREA_RECOMMENDATIONS[area]
        priority = "P1" if area == "Shared Utilities and Supporting Operations" else (
            "P4" if states["purchase_cost_present"] == "missing" else "P3"
        )
        records.append(
            UnitCompletenessRecord(
                unit_id=unit_id,
                unit_class=unit_class,
                process_area=area,
                active_scenarios=active_scenarios,
                inlet_basis=_stream_basis(unit.ins),
                outlet_basis=_stream_basis(unit.outs),
                source_references=(
                    f"{type(unit).__module__}.{unit_class}; "
                    f"{model.dataset_provenance['master_input_workbook']}; "
                    f"validation: {VALIDATION_REFERENCES[area]}"
                ),
                validation_test_present=(
                    "not yet implemented"
                    if VALIDATION_REFERENCES[area] == "not yet implemented"
                    else "available"
                ),
                current_maturity_level=maturity,
                missing_items=_missing_items(states),
                recommended_data=recommendation,
                recommended_search_keywords=keywords,
                implementation_priority=priority,
                **states,
            )
        )
    selected_unit_ids = set(model.units)
    built_in_cost_classes = {"StorageTank", "HXutility", "IsentropicCompressor", "Pump"}
    for definition in ALTERNATIVE_UNIT_CATALOG:
        if definition.unit_id in selected_unit_ids:
            continue
        unit_class = definition.unit_class
        virtual = unit_class in VIRTUAL_CLASSES
        maturity = _maturity(unit_class)
        power_state = (
            "not applicable"
            if virtual
            else ("available" if unit_class in POWER_MODEL_CLASSES else "missing")
        )
        states = {
            "mass_model_present": "available",
            "stoichiometry_present": "available" if unit_class in STOICHIOMETRIC_CLASSES else "not applicable",
            "kinetics_present": "not yet implemented" if unit_class in KINETIC_DATA_NEEDED_CLASSES else "not applicable",
            "equilibrium_present": "assumed" if unit_class in SIMPLIFIED_EQUILIBRIUM_CLASSES else "not applicable",
            "energy_balance_present": "available" if unit_class in E4_CLASSES else ("not applicable" if virtual else "not yet implemented"),
            "heat_duty_present": "available" if unit_class in HEAT_MODEL_CLASSES else "not applicable",
            "cooling_duty_present": "available" if unit_class in COOLING_MODEL_CLASSES else "not applicable",
            "power_demand_present": power_state,
            "power_production_present": "not applicable",
            "design_sizing_present": "not applicable" if virtual else "available",
            "purchase_cost_present": "available" if unit_class in built_in_cost_classes else ("not applicable" if virtual else "missing"),
            "installed_cost_present": "available" if unit_class in built_in_cost_classes else ("not applicable" if virtual else "missing"),
            "equipment_lifetime_present": "not applicable" if virtual else "missing",
            "maintenance_basis_present": "not applicable" if virtual else "missing",
            "consumables_present": "available" if unit_class in CHEMICAL_DEMAND_CLASSES | WATER_DEMAND_CLASSES else ("not applicable" if virtual else "missing"),
            "chemical_demand_present": "available" if unit_class in CHEMICAL_DEMAND_CLASSES else "not applicable",
            "water_demand_present": "available" if unit_class in WATER_DEMAND_CLASSES else "not applicable",
            "emissions_or_losses_present": "available" if unit_class in LOSS_MODEL_CLASSES else "not applicable",
        }
        recommendation, keywords = AREA_RECOMMENDATIONS[definition.process_area]
        records.append(
            UnitCompletenessRecord(
                unit_id=definition.unit_id,
                unit_class=unit_class,
                process_area=definition.process_area,
                active_scenarios=f"{definition.active_scenarios}; not selected in current run",
                inlet_basis="kg/hr component mass; scenario-defined streams",
                outlet_basis="kg/hr component mass; scenario-defined streams",
                source_references=(
                    f"{definition.factory_reference}; validation: "
                    f"{VALIDATION_REFERENCES[definition.process_area]}"
                ),
                validation_test_present="available",
                current_maturity_level=maturity,
                missing_items=_missing_items(states),
                recommended_data=recommendation,
                recommended_search_keywords=keywords,
                implementation_priority=(
                    "P4" if states["purchase_cost_present"] == "missing" else "P3"
                ),
                **states,
            )
        )
    model.model_completeness = tuple(records)
    return tuple(records)


def _validate_records(records: tuple[UnitCompletenessRecord, ...]) -> None:
    if not records:
        raise ValueError("The model-completeness register cannot be empty.")
    state_fields = tuple(
        field.name
        for field in fields(UnitCompletenessRecord)
        if field.name.endswith("_present")
    )
    for record in records:
        for field_name in state_fields:
            state = getattr(record, field_name)
            if state not in VALID_STATES:
                raise ValueError(
                    f"Unit {record.unit_id} has invalid completeness state "
                    f"'{state}' in {field_name}."
                )


def _markdown_report(
    model: "IntegratedGreenHubModel",
    records: tuple[UnitCompletenessRecord, ...],
) -> str:
    maturity_counts = Counter(record.current_maturity_level for record in records)
    area_counts = Counter(record.process_area for record in records)
    scenario = model.scenario_configuration
    selected_unit_count = len(model.units)
    alternative_unit_count = len(records) - selected_unit_count
    lines = [
        "# GreenHub Model Completeness Register",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Selected configuration: `{scenario.scenario_chain}`; order `{scenario.process_order}`; month `{scenario.selected_month}`.",
        f"Selected connected units represented: **{selected_unit_count}**.",
        f"Additional implemented scenario-only or compatibility units represented: **{alternative_unit_count}**.",
        f"Total unit-ID rows: **{len(records)}**.",
        "",
        "This register describes implementation presence, not scientific validation. A calculated value may still use structural-test inputs. Zero is never interpreted as proof that a model is available.",
        "",
        "## State Definitions",
        "",
        "`available`, `calculated`, `assumed`, `placeholder`, `not applicable`, `missing`, and `not yet implemented` are the only completeness states.",
        "",
        "## Coverage Summary",
        "",
        "| Process area | Active units |",
        "|---|---:|",
    ]
    lines.extend(f"| {area} | {count} |" for area, count in sorted(area_counts.items()))
    lines.extend(
        (
            "",
            "| Maturity | Units |",
            "|---|---:|",
        )
    )
    lines.extend(f"| {level} | {maturity_counts.get(level, 0)} |" for level in ("E0", "E1", "E2", "E3", "E4", "E5"))
    lines.extend(
        (
            "",
            "No unit is classified E5: the active model uses structural inputs and lacks sufficient project validation and custom-equipment costing.",
            "",
            "## Active Unit Register",
            "",
            "| Unit | Class | Process area | Maturity | Purchase cost | Power | Heat | Principal gaps |",
            "|---|---|---|---|---|---|---|---|",
        )
    )
    for record in records:
        lines.append(
            f"| {record.unit_id} | {record.unit_class} | {record.process_area} | "
            f"{record.current_maturity_level} | {record.purchase_cost_present} | "
            f"{record.power_demand_present} | {record.heat_duty_present} | "
            f"{record.missing_items} |"
        )
    lines.extend(
        (
            "",
            "## Consolidated Missing Data",
            "",
            "### Feedstock",
            "Monthly availability is workbook-controlled, but project laboratory composition, density, pH, solids, COD, elemental pools, and uncertainty distributions remain incomplete. Missing measurements are not silently replaced with value-generating defaults.",
            "",
            "### Protein Recovery",
            "Project titration curves, precipitation or coagulation recoveries, separation performance, product quality, drying trials, and vendor costs are required. The 17 protein-recovery CSV datasets remain disconnected because several required values and validators are missing.",
            "",
            "### Anaerobic Digestion",
            "BMP or continuous-reactor calibration, kinetics, inhibition data, measured gas partitioning, digestate validation, heat-loss measurements, and equipment quotations remain required. R501 is not ADM1.",
            "",
            "### Biogas Upgrading",
            "Vendor curves, media lifetime, methane slip, gas specifications, compression and pumping validation, final storage or grid injection, and a CHP definition remain required.",
            "",
            "### Nutrient Recovery",
            "Full ionic analyses, activity or electrolyte treatment, pH titration, precipitation and stripping pilot data, product purity and moisture, reagent use, energy integration, and vendor prices remain required.",
            "",
            "### Drying",
            "Protein and nutrient drying use screening-level moisture, loss, heat, and power relationships. Drying kinetics, air psychrometrics, equipment geometry, emissions control, and vendor costs are not validated.",
            "",
            "### Filtration",
            "Separation and membrane units require measured rejection, flux, fouling, pressure-drop, cleaning, membrane lifetime, and module-cost data before design claims.",
            "",
            "### Shared Utilities",
            "No active CHP or plant-wide utility network exists. Heat recovery and electricity production remain explicit missing interfaces and default to zero rather than being inferred.",
            "",
            "### Equipment Economics",
            "Custom units intentionally have no invented CAPEX, installed-cost, lifetime, or maintenance basis. Built-in BioSTEAM correlations are reported where active but remain subject to their stated validity ranges.",
            "",
            "### Process Validation",
            "Conservation tests are extensive, but conservation alone does not validate yields, kinetics, equilibrium, energy demand, equipment sizing, product eligibility, or economics. Project measurements and pilot comparisons remain necessary.",
            "",
            "The complete field set and one row per selected or implemented scenario-only unit ID are available in `Greenhub/results/model_completeness.csv`.",
            "",
        )
    )
    return "\n".join(lines)


def write_model_completeness_reports(
    model: "IntegratedGreenHubModel",
    *,
    csv_path: Path | None = None,
    markdown_path: Path | None = None,
) -> dict[str, Path]:
    """Write the complete CSV and concise human-readable audit report."""

    records = build_model_completeness(model)
    _validate_records(records)
    csv_path = csv_path or RESULTS_DIR / "model_completeness.csv"
    markdown_path = markdown_path or PROJECT_ROOT / "docs" / "audit" / "model_completeness.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [field.name for field in fields(UnitCompletenessRecord)]
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    markdown_path.write_text(_markdown_report(model, records), encoding="utf-8")
    paths = {
        "model_completeness_csv": csv_path,
        "model_completeness_markdown": markdown_path,
    }
    model.integrated_report_paths.update(paths)
    return paths
