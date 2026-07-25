"""GreenHub scenario definitions, including the active Phase 3 front end."""

from __future__ import annotations

from dataclasses import dataclass

from Greenhub.streams import BASELINE_FEED_FLOWS_KG_HR


@dataclass(frozen=True)
class ScenarioDefinition:
    """Lightweight scenario metadata placeholder for later phases."""

    name: str
    description: str
    feed_flows_kg_hr: dict[str, float]


BASELINE_PHASE_1_SCENARIO = ScenarioDefinition(
    name="phase_1_baseline",
    description=(
        "Liquid-fraction storage followed by provisional primary solid-liquid "
        "separation."
    ),
    feed_flows_kg_hr=dict(BASELINE_FEED_FLOWS_KG_HR),
)


@dataclass(frozen=True)
class FrontEndScenario:
    """Topology metadata for a Phase 3 scenario."""

    scenario_id: str
    name: str
    entry_mode: str
    preparation_enabled: bool
    pef_enabled: bool
    sensitivity_ready: bool
    description: str


FRONT_END_SCENARIOS = {
    "F0": FrontEndScenario(
        "F0",
        "Measured liquid fraction",
        "measured_liquid",
        False,
        False,
        False,
        "Measured raw liquid is stored and sent directly to primary centrifugation.",
    ),
    "F1": FrontEndScenario(
        "F1",
        "Roadside grass without PEF",
        "roadside_grass",
        True,
        False,
        False,
        "Prepared roadside grass is screw pressed without PEF, then centrifuged.",
    ),
    "F2": FrontEndScenario(
        "F2",
        "PEF baseline",
        "roadside_grass",
        True,
        True,
        False,
        "Prepared roadside grass receives baseline PEF before pressing and centrifugation.",
    ),
    "F3": FrontEndScenario(
        "F3",
        "PEF sensitivity-ready",
        "roadside_grass",
        True,
        True,
        True,
        "F2 topology with explicit parameter overrides for deterministic sensitivity studies.",
    ),
}


def get_front_end_scenario(scenario_id: str) -> FrontEndScenario:
    """Return an F0-F3 definition with a clear validation error."""

    key = str(scenario_id).upper()
    try:
        return FRONT_END_SCENARIOS[key]
    except KeyError as error:
        raise ValueError(f"Unknown Phase 3 scenario '{scenario_id}'; use F0, F1, F2, or F3.") from error


@dataclass(frozen=True)
class ProteinRecoveryScenario:
    """Topology and readiness metadata for a Phase 4 scenario."""

    scenario_id: str
    name: str
    acid_enabled: bool
    heat_enabled: bool
    wash_enabled: bool
    active: bool
    description: str
    missing_data_requirements: tuple[str, ...] = ()


PROTEIN_RECOVERY_SCENARIOS = {
    "PR0": ProteinRecoveryScenario(
        "PR0",
        "No protein recovery",
        False,
        False,
        False,
        True,
        "Clarified liquid bypasses recovery and remains available for future digestion.",
    ),
    "PR1": ProteinRecoveryScenario(
        "PR1",
        "Acid precipitation",
        True,
        False,
        False,
        True,
        "HCl acidification, empirical precipitation, separation, dewatering, drying, and neutralization.",
    ),
    "PR2": ProteinRecoveryScenario(
        "PR2",
        "Heat coagulation",
        False,
        True,
        False,
        True,
        "Thermal coagulation, separation, dewatering, and low-temperature drying without acid addition.",
    ),
    "PR3": ProteinRecoveryScenario(
        "PR3",
        "Combined acid and heat",
        True,
        True,
        True,
        True,
        "Combined HCl and moderate heat recovery with cake washing, dewatering, drying, and neutralization.",
    ),
    "PR4": ProteinRecoveryScenario(
        "PR4",
        "Lactic-fermentation precipitation",
        False,
        False,
        False,
        False,
        "Architecture reserved; no fermentation performance is assumed in Phase 4.",
        ("glucose conversion", "lactic-acid yield", "fermentation kinetics", "biomass yield"),
    ),
    "PR5": ProteinRecoveryScenario(
        "PR5",
        "CO2-assisted precipitation",
        False,
        False,
        False,
        False,
        "Architecture reserved; gas-liquid transfer and pH data are not available.",
        ("CO2 dissolution efficiency", "mass-transfer coefficient", "pressure", "CO2 titration curve"),
    ),
    "PR6": ProteinRecoveryScenario(
        "PR6",
        "Ultrafiltration",
        False,
        False,
        False,
        False,
        "Architecture reserved; membrane design and retention data are not available.",
        ("membrane flux", "retention matrix", "TMP", "fouling factor", "cleaning cycle"),
    ),
}


def get_protein_recovery_scenario(scenario_id: str) -> ProteinRecoveryScenario:
    """Return PR0-PR6 metadata with a clear validation error."""

    key = str(scenario_id).upper()
    try:
        return PROTEIN_RECOVERY_SCENARIOS[key]
    except KeyError as error:
        raise ValueError(
            f"Unknown Phase 4 scenario '{scenario_id}'; use PR0 through PR6."
        ) from error


@dataclass(frozen=True)
class DigestionScenario:
    """Phase 5 feed route, temperature mode, and data-readiness status."""

    scenario_id: str
    name: str
    description: str
    digestion_enabled: bool
    feed_mode: str
    temperature_mode: str
    digester_type: str
    active: bool
    missing_data_requirements: tuple[str, ...] = ()


DIGESTION_SCENARIOS: dict[str, DigestionScenario] = {
    "AD0": DigestionScenario(
        "AD0",
        "No digestion",
        "Conditioned liquid bypass with no substrate conversion or biogas production.",
        False,
        "post_protein_recovery",
        "ambient",
        "bypass",
        True,
    ),
    "AD1": DigestionScenario(
        "AD1",
        "Post-protein-recovery mesophilic digestion",
        "Conditioned protein-depleted liquid to a steady-state mesophilic CSTR.",
        True,
        "post_protein_recovery",
        "mesophilic",
        "cstr",
        True,
    ),
    "AD2": DigestionScenario(
        "AD2",
        "Direct mesophilic digestion",
        "Clarified protein-rich liquid enters digestion through the PR0 bypass.",
        True,
        "direct_protein_rich",
        "mesophilic",
        "cstr",
        True,
    ),
    "AD3": DigestionScenario(
        "AD3",
        "Thermophilic digestion",
        "Post-protein-recovery liquid to a structural thermophilic CSTR case.",
        True,
        "post_protein_recovery",
        "thermophilic",
        "cstr",
        True,
    ),
    "AD4": DigestionScenario(
        "AD4",
        "Two-stage digestion",
        "Reserved hydrolysis/acidogenesis and methanogenesis architecture.",
        True,
        "post_protein_recovery",
        "mesophilic",
        "two_stage",
        False,
        (
            "stage-specific hydrolysis and VFA-production kinetics",
            "interstage pH and residence-time design",
            "stage-specific biomass yields and retention",
        ),
    ),
    "AD5": DigestionScenario(
        "AD5",
        "High-rate digestion",
        "Reserved UASB/EGSB/AnMBR-style interface.",
        True,
        "post_protein_recovery",
        "mesophilic",
        "high_rate",
        False,
        (
            "biomass-retention and purge data",
            "granule or membrane solids-separation performance",
            "hydraulic loading, fouling, and cleaning data",
        ),
    ),
}


def get_digestion_scenario(scenario_id: str) -> DigestionScenario:
    """Return an AD0-AD5 scenario by case-insensitive identifier."""

    key = str(scenario_id).upper()
    try:
        return DIGESTION_SCENARIOS[key]
    except KeyError as error:
        raise ValueError(
            f"Unknown Phase 5 scenario '{scenario_id}'; use AD0 through AD5."
        ) from error


@dataclass(frozen=True)
class BiogasUpgradingScenario:
    """Phase 6 pathway mechanism and data-readiness metadata."""

    scenario_id: str
    name: str
    mechanism: str
    pretreatment_enabled: bool
    upgrading_enabled: bool
    active: bool
    description: str
    missing_data_requirements: tuple[str, ...] = ()


BIOGAS_UPGRADING_SCENARIOS: dict[str, BiogasUpgradingScenario] = {
    "BG0": BiogasUpgradingScenario(
        "BG0",
        "Raw biogas export",
        "reference_export",
        False,
        False,
        True,
        "Raw biogas is exported without conditioning or upgrading as the Phase 6 reference.",
    ),
    "BG1": BiogasUpgradingScenario(
        "BG1",
        "CHP pathway",
        "combustion_and_heat_recovery",
        True,
        False,
        False,
        "Architecture reserved for the next Phase 6 section on CHP and plant utilities.",
        (
            "engine electrical and thermal efficiency maps",
            "engine contaminant limits and methane number",
            "heat-recovery temperatures and plant utility-network rules",
            "combustion emissions and excess-air basis",
        ),
    ),
    "BG2": BiogasUpgradingScenario(
        "BG2",
        "High-pressure water scrubbing",
        "physical_absorption",
        True,
        True,
        True,
        "Level-1 pressure-, temperature-, and circulation-dependent physical absorption with explicit water and flash-gas recycles.",
    ),
    "BG3": BiogasUpgradingScenario(
        "BG3",
        "Membrane separation",
        "solution_diffusion",
        True,
        True,
        True,
        "Segmented partial-pressure-driven permeation with one to three stages and optional permeate recycle.",
    ),
    "BG4": BiogasUpgradingScenario(
        "BG4",
        "Pressure swing adsorption",
        "cycle_average_adsorption",
        True,
        True,
        True,
        "Mass-conserving Level-1 cycle-average adsorption, blowdown, and product purge model.",
    ),
    "BG5": BiogasUpgradingScenario(
        "BG5",
        "MEA chemical absorption",
        "equivalent_loading_absorption",
        True,
        True,
        True,
        "Reversible Level-1 MEA loading loop with explicit solvent regeneration, losses, heat, and recycle.",
    ),
    "BG6": BiogasUpgradingScenario(
        "BG6",
        "Cryogenic upgrading",
        "cryogenic_phase_equilibrium",
        True,
        False,
        False,
        "Future-ready interface only; no fixed-split cryogenic separator is presented as rigorous.",
        (
            "validated low-temperature equation of state",
            "CO2 freezing and phase-envelope limits",
            "refrigeration-cycle and multistream heat-exchanger design",
            "validated methane/CO2 low-temperature property data",
        ),
    ),
}


def get_biogas_upgrading_scenario(scenario_id: str) -> BiogasUpgradingScenario:
    """Return BG0-BG6 metadata with a clear validation error."""

    key = str(scenario_id).upper()
    try:
        return BIOGAS_UPGRADING_SCENARIOS[key]
    except KeyError as error:
        raise ValueError(
            f"Unknown Phase 6 scenario '{scenario_id}'; use BG0 through BG6."
        ) from error


@dataclass(frozen=True)
class NutrientRecoveryScenario:
    """Phase 7 topology, process order, and active recovery mechanisms."""

    scenario_id: str
    name: str
    description: str
    default_order: str
    separation_enabled: bool
    phosphorus_route: str
    ammonia_route: str
    potassium_route: str
    active: bool = True


NUTRIENT_RECOVERY_SCENARIOS: dict[str, NutrientRecoveryScenario] = {
    "NR0": NutrientRecoveryScenario(
        "NR0", "No targeted nutrient recovery",
        "Actual Phase 5 digestate leaves without a nutrient-product claim.",
        "D", False, "none", "none", "none",
    ),
    "NR1": NutrientRecoveryScenario(
        "NR1", "Digestate solid-liquid separation",
        "Component-specific mechanical separation into nutrient-rich solids and centrate.",
        "D", True, "none", "none", "none",
    ),
    "NR2": NutrientRecoveryScenario(
        "NR2", "Struvite recovery",
        "Mechanical separation followed by Mg-N-P precipitation and crystal recovery.",
        "A", True, "struvite", "none", "none",
    ),
    "NR3": NutrientRecoveryScenario(
        "NR3", "Ammonia stripping and acid capture",
        "Mechanical separation, pH/temperature conditioning, stripping, and stoichiometric acid capture.",
        "A", True, "none", "stripping", "none",
    ),
    "NR4": NutrientRecoveryScenario(
        "NR4", "Integrated struvite and ammonia recovery",
        "Baseline cascade with selectable A, B, or C process order.",
        "A", True, "struvite", "stripping", "none",
    ),
    "NR5": NutrientRecoveryScenario(
        "NR5", "Calcium-phosphate recovery",
        "Mechanical separation and configurable calcium-phosphate precipitation without an N-product claim.",
        "A", True, "calcium_phosphate", "none", "none",
    ),
    "NR6": NutrientRecoveryScenario(
        "NR6", "Ion-exchange ammonia recovery",
        "Mechanical separation followed by capacity-limited Na-form zeolite exchange and NaCl regeneration.",
        "A", True, "none", "ion_exchange", "none",
    ),
    "NR7": NutrientRecoveryScenario(
        "NR7", "Integrated recovery and potassium concentration",
        "Struvite, ammonia-salt, and non-selective potassium-rich residual-liquor concentration cascade.",
        "A", True, "struvite", "stripping", "concentration",
    ),
}


def get_nutrient_recovery_scenario(scenario_id: str) -> NutrientRecoveryScenario:
    """Return NR0-NR7 metadata with a clear validation error."""

    key = str(scenario_id).upper()
    try:
        return NUTRIENT_RECOVERY_SCENARIOS[key]
    except KeyError as error:
        raise ValueError(
            f"Unknown Phase 7 scenario '{scenario_id}'; use NR0 through NR7."
        ) from error
