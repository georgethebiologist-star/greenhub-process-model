"""Programmatic Phase 1-5 limitation and data-gap register."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

LIMITATION_CATEGORIES = frozenset(
    {
        "chemistry",
        "kinetics",
        "thermodynamics",
        "mass_transfer",
        "hydraulics",
        "separation",
        "heat_transfer",
        "energy",
        "design",
        "costing",
        "controls",
        "seasonality",
        "scale_up",
        "data_quality",
        "regulatory",
        "contaminants",
    }
)


@dataclass(frozen=True)
class ModelLimitation:
    """One traceable limitation, simplification, or missing-data requirement."""

    limitation_id: str
    phase: int
    module: str
    unit_or_stream: str
    category: str
    description: str
    current_implementation: str
    reason_for_simplification: str
    impact_on_results: str
    affected_outputs: str
    priority: str
    data_needed: str
    preferred_data_source: str
    literature_needed: bool
    industry_data_needed: bool
    experimental_data_needed: bool
    validation_method: str
    temporary_parameter: str | None
    temporary_value: str | float | None
    unit: str | None
    uncertainty_range: str | None
    status: str
    planned_upgrade_phase: str
    comment: str

    def __post_init__(self) -> None:
        if self.category not in LIMITATION_CATEGORIES:
            raise ValueError(
                f"Limitation {self.limitation_id} has unknown category '{self.category}'."
            )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _entry(
    limitation_id: str,
    phase: int,
    module: str,
    unit_or_stream: str,
    category: str,
    description: str,
    current_implementation: str,
    reason: str,
    impact: str,
    data_needed: str,
    *,
    outputs: str = "scenario metrics and design reports",
    priority: str = "medium",
    source: str = "project experiment or validated peer-reviewed literature",
    literature: bool = True,
    industry: bool = False,
    experimental: bool = True,
    validation: str = "Replace placeholder and compare predicted values with independent measurements.",
    parameter: str | None = None,
    value: str | float | None = None,
    unit: str | None = None,
    uncertainty: str | None = None,
    status: str = "open",
    upgrade: str = "Future calibration phase",
    comment: str = "",
) -> ModelLimitation:
    return ModelLimitation(
        limitation_id,
        phase,
        module,
        unit_or_stream,
        category,
        description,
        current_implementation,
        reason,
        impact,
        outputs,
        priority,
        data_needed,
        source,
        literature,
        industry,
        experimental,
        validation,
        parameter,
        value,
        unit,
        uncertainty,
        status,
        upgrade,
        comment,
    )


BASE_LIMITATIONS: tuple[ModelLimitation, ...] = (
    _entry("LIM-P1-001", 1, "streams", "liquid_fraction", "data_quality", "Liquid-fraction flow and composition remain provisional.", "Monthly user-controlled workbook values with missing values preserved as blank.", "The complete laboratory dataset is not yet available.", "All downstream mass, utility, and product rates scale with these inputs.", "Monthly mass, density, component concentrations, and measurement uncertainty.", priority="high"),
    _entry("LIM-P1-002", 1, "units", "T101", "costing", "Storage-tank flow can fall below the validated BioSTEAM cost-correlation range.", "The BioSTEAM CostWarning is retained and reported.", "Current structural feed rates are small relative to the correlation range.", "Tank CAPEX is an extrapolation and is not design-grade.", "Vendor storage quotation at GreenHub flow and residence time.", industry=True, experimental=False, priority="medium"),
    _entry("LIM-P2-001", 2, "chemicals", "pseudo-components", "thermodynamics", "Lumped organics, proteins, solids, nutrients, and contaminants are not unique molecular species.", "Explicit pseudo-components use water or glucose sensible-property surrogates and metadata fractions.", "Exact species and thermophysical properties are unavailable.", "Heat capacity, phase behavior, and equilibrium results are screening-level.", "Species-resolved composition and measured heat capacity/density data.", priority="high"),
    _entry("LIM-P2-002", 2, "equilibria", "aqueous streams", "chemistry", "The active thermo does not solve rigorous electrolyte activities or charge balance.", "pH and alkalinity are metadata; validated molecular reactions track selected salts.", "Electrolyte interaction parameters and complete ionic measurements are unavailable.", "pH, ionic strength, precipitation, and gas speciation are approximate.", "Complete ion analysis, alkalinity titration, and an electrolyte property-package validation dataset.", priority="high"),
    _entry("LIM-P2-003", 2, "component_metadata", "contaminant pools", "contaminants", "PFAS, pesticides, microplastics, pathogens, and heavy metals are aggregate pools.", "Persistent pools are conserved without claiming treatment or destruction.", "Compound-specific concentrations and fate data are unavailable.", "No regulatory or risk conclusion can be made.", "Compound-specific laboratory analyses and process fate/removal studies.", outputs="contaminant inventories and regulatory interpretation", priority="high", upgrade="Dedicated contaminant-fate phase"),
    _entry("LIM-P3-001", 3, "phase3_units", "U201", "kinetics", "PEF release and juice-yield enhancement are empirical.", "Mass-conserving pool transfers use fixed class-E fractions.", "Pulse-response and scale-up measurements are missing.", "Clarified-liquid yield and protein/COD concentration are uncertain.", "PEF dose-response tests across field strength, pulse width, energy, and feed condition.", priority="high"),
    _entry("LIM-P3-002", 3, "phase3_units", "S201/C301", "separation", "Press and centrifuge component recoveries are fixed allocations.", "Component-group recoveries and analytical moisture constraints are used.", "Vendor curves and GreenHub separation trials are unavailable.", "Liquid yield, solids carryover, and downstream loading are uncertain.", "Pilot pressing and centrifuge partitioning, moisture, capacity, and power data.", industry=True, priority="high"),
    _entry("LIM-P3-003", 3, "systems", "P301 placeholder", "hydraulics", "No transfer pump is active.", "Pressure is propagated without a pressure-rise calculation.", "Required static head, line length, and pressure drop are unknown.", "Pumping electricity and pump design are omitted.", "Piping layout, elevations, flow velocities, pressure drops, and pump efficiency.", source="project engineering and vendor data", literature=False, industry=True, experimental=False),
    _entry("LIM-P3-004", 3, "phase3_units", "U101/U201/S201/C301", "costing", "Custom front-end equipment has no approved cost correlation.", "Purchase costs remain zero and the data gap is reported.", "No traceable project-scale cost basis has been approved.", "Phase 3 CAPEX and TEA conclusions are unavailable.", "Vendor quotations or cited correlations with year, currency, scale, and validity range.", outputs="equipment and system cost results", source="vendor or traceable industry cost source", literature=True, industry=True, experimental=False, priority="high"),
    _entry("LIM-P3-005", 3, "phase3_metrics", "seasonal model", "seasonality", "Monthly operation is represented by independent steady states.", "Each month uses its own mass and composition where supplied.", "Hourly variability, storage dynamics, and downtime distributions are unavailable.", "Shock loads and short-term capacity constraints are not predicted.", "Hourly/daily feed availability, composition, operating schedule, and downtime records.", source="project operating data", literature=False, industry=True, experimental=True, upgrade="Dynamic operations phase"),
    _entry("LIM-P4-001", 4, "phase4_specifications", "R401", "chemistry", "Protein solubility and effective isoelectric pH are aggregate approximations.", "A bounded empirical pH response or direct recovery can be selected.", "Protein-group-specific solubility measurements are missing.", "Precipitation recovery and product purity are uncertain.", "Solubility/recovery curves by pH, temperature, ionic strength, and protein group.", parameter="effective_protein_pI", value="class E workbook value", unit="pH", priority="high"),
    _entry("LIM-P4-002", 4, "phase4_inputs", "M401", "chemistry", "Acid demand lacks project titration data.", "An empirical pure-acid dose is used in structural mode.", "Acid-dose versus pH measurements are unavailable.", "Acid use, salt generation, and neutralization demand are uncertain.", "Replicated acid titration curves for each seasonal feed.", parameter="acid_dose_kg_per_m3", value="class E workbook value", unit="kg pure acid/m3", priority="high"),
    _entry("LIM-P4-003", 4, "phase4_units", "R401", "kinetics", "Precipitation and heat-coagulation kinetics are not calibrated.", "Direct fixed recoveries are used; optional first-order interfaces remain data-gated.", "Rate constants, activation energies, and residence-time data are missing.", "Vessel sizing and recovery response are screening-level.", "Time-resolved recovery at multiple pH and temperatures.", priority="high"),
    _entry("LIM-P4-004", 4, "phase4_units", "C401", "separation", "Co-precipitation and protein capture use component-specific fixed fractions.", "A transparent mass-allocation separator and analytical cake-moisture solver are used.", "Pilot separator partitioning and capacity data are missing.", "Product purity, residual COD, cake rate, and power are uncertain.", "Protein separator trials with full cake/centrate composition, power, and capacity.", industry=True, priority="high"),
    _entry("LIM-P4-005", 4, "phase4_units", "W401/D401", "separation", "Cake washing and dewatering are single-stage empirical allocations.", "Specified wash removal, protein loss, and target solids are imposed.", "Wash curves and dewatering performance data are unavailable.", "Water use, product loss, and dryer feed moisture are uncertain.", "Bench/pilot washing and dewatering mass balances.", industry=True, priority="medium"),
    _entry("LIM-P4-006", 4, "phase4_units", "DR401", "heat_transfer", "Dryer kinetics, air humidity, area, and heat recovery are not modelled.", "A single selected thermodynamic duty and utility-only air interface are used.", "Vendor dryer curves and psychrometric measurements are missing.", "Dryer heat, electricity, residence time, and product quality are highly uncertain.", "Vendor or pilot drying curves, air flow/humidity, efficiency, degradation, and capacity.", source="pilot drying tests and dryer vendor", industry=True, priority="high"),
    _entry("LIM-P4-007", 4, "phase4_units", "M403", "thermodynamics", "Neutralized-liquid pH and salt effects are not rigorous electrolyte predictions.", "Molecular acid-base salt formation is balanced; target pH is metadata.", "Buffering, activity coefficients, and complete ion data are unavailable.", "Residual alkalinity, salinity, and digester inhibition risk are approximate.", "Base titration, alkalinity, full ion analysis, and electrolyte validation.", priority="high"),
    _entry("LIM-P4-008", 4, "phase4_units", "Phase 4 custom equipment", "costing", "No approved custom-equipment CAPEX correlations are available.", "Custom purchase costs remain zero; supported built-in BioSTEAM costs are retained.", "Traceable project-scale cost data are missing.", "Phase 4 TEA conclusions are unavailable.", "Vendor quotations or peer-reviewed correlations with complete costing metadata.", source="vendor or traceable industry cost source", industry=True, experimental=False, priority="high"),
    _entry("LIM-P4-009", 4, "phase4_metrics", "dry_protein_product", "regulatory", "Protein product quality and regulatory suitability are undetermined.", "The model reports composition and contaminants without assigning feed/food grade.", "Amino-acid profile, digestibility, contaminants, microbiology, and specification limits are missing.", "No product-market or regulatory claim can be made.", "Accredited product characterization and applicable regulatory specification.", outputs="product quality, price, and market eligibility", source="accredited laboratory and regulatory review", literature=True, industry=True, experimental=True, priority="high"),
    _entry("LIM-P5-001", 5, "phase5_units", "M501", "controls", "Digester-feed pH conditioning is not solved from buffering chemistry.", "Empirical base dosage is added and target pH is retained as metadata.", "Base titration and online pH-control response data are unavailable.", "Chemical demand, alkalinity, sodium/calcium load, and pH stability are uncertain.", "Seasonal base-dose versus pH titration curves and alkalinity measurements.", parameter="conditioning_base_dose_kg_m3", value="class E workbook value", unit="kg pure base/m3", priority="high"),
    _entry("LIM-P5-002", 5, "phase5_units", "R501", "kinetics", "Hydrolysis uses fixed component-group conversions.", "Separate hydrolysis ledgers feed the steady-state digestion calculation.", "Hydrolysis rate constants, particle-size response, temperature coefficients, and inhibition data are missing.", "COD destruction, methane production, and required HRT are uncertain.", "Biochemical methane potential and time-course hydrolysis tests by substrate group.", parameter="*_hydrolysis_fraction", value="class E workbook values", unit="fraction", priority="high"),
    _entry("LIM-P5-003", 5, "phase5_units", "R501", "kinetics", "Acidogenesis, acetogenesis, and methanogenesis are fixed ultimate-fate stages rather than dynamic populations.", "Stage-specific conversion ledgers allocate converted COD to methane, biomass, H2S, and residual soluble COD.", "VFA product yields, uptake kinetics, SRT response, and microbial-population data are unavailable.", "VFA profile, COD removal, gas yield, and stability are screening-level.", "Batch/continuous digestion data including COD, VFAs, gas, HRT, SRT, and temperature.", parameter="methanogenesis_conversion", value="class E workbook value", unit="fraction", priority="high"),
    _entry("LIM-P5-004", 5, "phase5_units", "R501", "chemistry", "Pseudo-component digestion is balanced on mass, COD, C, N, P, and S rather than full molecular H/O stoichiometry.", "Molecular reactions are validated where formulas exist; empirical pools use metadata and a water mass adjustment.", "Lumped substrates do not have defensible unique formulas.", "Reaction water and heat cannot be interpreted as exact biochemical stoichiometry.", "Species-resolved substrate formulas or experimentally reconciled elemental/COD composition.", priority="high"),
    _entry("LIM-P5-005", 5, "phase5_units", "R501", "design", "One combined anaerobic biomass pool represents all microbial populations.", "MicrobialBiomass has explicit C/N/P/S, COD, and VS metadata with a fixed yield.", "Acidogen, acetogen, methanogen, and decay data are unavailable.", "Biomass inventory, nutrient assimilation, and SRT behavior are simplified.", "Population-specific yields, compositions, decay rates, and retention measurements.", parameter="biomass_cod_yield_fraction", value="class E workbook value", unit="kg biomass COD/kg converted COD", priority="medium"),
    _entry("LIM-P5-006", 5, "phase5_units", "R501", "kinetics", "Free-ammonia, VFA, and salinity inhibition are disabled.", "Indicators are calculated; only the bounded structural pH factor is active.", "GreenHub-specific inhibition constants and thresholds are unavailable.", "High-N or high-salt scenarios may overpredict conversion and methane.", "Continuous digestion inhibition tests across FAN, VFA/alkalinity, chloride, and salinity.", outputs="conversion, methane, stability warnings", priority="high"),
    _entry("LIM-P5-007", 5, "phase5_units", "V501", "mass_transfer", "Gas-liquid partitioning uses empirical Level-1 fractions.", "CH4, CO2, H2, NH3, and H2S are partitioned with explicit dissolved and uncaptured inventories.", "Henry constants in the GreenHub matrix, kLa, gas holdup, and pressure data are unavailable.", "Exported gas, dissolved methane, fugitive inventory, and gas composition are uncertain.", "Dissolved-gas measurements, headspace flow/composition, pressure, and gas-transfer tests.", parameter="dissolved_methane_fraction", value="class E workbook value", unit="fraction", priority="high"),
    _entry("LIM-P5-008", 5, "phase5_units", "V501", "thermodynamics", "H2S and inorganic-carbon speciation are screening-level and not charge-balanced.", "Existing pH/temperature speciation functions inform metadata; one H2S and one CO2 component carry dissolved inventories.", "A complete electrolyte model and measured alkalinity/sulphide data are unavailable.", "H2S, bicarbonate, carbonate, gas CO2, and corrosion risk are approximate.", "Total inorganic carbon, alkalinity, total sulphide, ion analysis, and validated equilibrium constants.", priority="high"),
    _entry("LIM-P5-009", 5, "phase5_units", "V501", "thermodynamics", "Raw-biogas water vapour uses a specified wet-mole fraction rather than saturation.", "The structural moisture fraction removes explicit water from digestate.", "Gas humidity or condenser data are unavailable.", "Wet gas flow and composition are approximate.", "Measured raw-gas humidity or validated saturation/dew-point model inputs.", parameter="raw_biogas_water_vapor_mol_fraction", value="class E workbook value", unit="mol fraction", priority="medium"),
    _entry("LIM-P5-010", 5, "phase5_units", "R501", "heat_transfer", "Digester heat loss uses a lumped U-value and conceptual geometry.", "Feed sensible heat and U*A*dT loss are reported without heat recovery or reaction heat.", "Insulation design, weather, buried area, and reaction-heat data are unavailable.", "Heating duty and utility sizing are uncertain.", "Site ambient profile, insulation specification, measured heat loss, and heat-exchanger performance.", parameter="digester_heat_loss_u_w_m2_k", value="class E workbook value", unit="W/m2/K", priority="medium"),
    _entry("LIM-P5-011", 5, "phase5_units", "R501", "energy", "Mixing power is a volume-based placeholder.", "Average electricity equals working volume times specific shaft power and schedule divided by motor efficiency.", "Rheology, mixer selection, duty cycle, and gas-recirculation data are unavailable.", "Electricity demand and mixing adequacy are uncertain.", "Vendor mixer design and measured rheology/power at scale.", parameter="specific_mixing_power_kw_m3", value="class E workbook value", unit="kW/m3", source="digester mixer vendor", industry=True, priority="medium"),
    _entry("LIM-P5-012", 5, "systems", "T501/P501/recycle", "hydraulics", "Equalization dynamics, pumping, and recycle loops are not active.", "The no-recycle system uses independent monthly steady states and propagates pressure.", "Hourly feed variability, line hydraulics, and recycle design data are unavailable.", "Shock loading, pump electricity, equalization capacity, and SRT control are not predicted.", "Hourly feed series, hydraulic layout, pressure requirements, and recycle/retention design.", source="project engineering and operating data", literature=False, industry=True, experimental=True, priority="medium", upgrade="Dynamic and detailed-design phase"),
    _entry("LIM-P5-013", 5, "scenarios", "AD4/AD5", "scale_up", "Two-stage and high-rate digesters are inactive.", "Scenario interfaces and missing-data requirements are registered but construction raises a clear error.", "Stage-specific kinetics, biomass retention, membrane/granule behavior, and hydraulic data are missing.", "No performance comparison is available for AD4 or AD5.", "Pilot two-stage/high-rate digestion, biomass retention, solids separation, fouling, and loading data.", outputs="scenario readiness and comparison", source="pilot testing and technology vendor", industry=True, priority="medium"),
    _entry("LIM-P5-014", 5, "phase5_units", "R501/V501", "contaminants", "Persistent contaminants are conserved and pathogen reduction is not claimed.", "Contaminant pools pass to digestate unless explicitly present in gas; no degradation is enabled.", "Compound-specific anaerobic fate and sanitation data are unavailable.", "Digestate safety and regulatory suitability are undetermined.", "Compound-specific digestate/gas fate tests and validated pathogen log-reduction data.", outputs="digestate composition and regulatory interpretation", priority="high"),
    _entry("LIM-P5-015", 5, "phase5_units", "R501", "costing", "No digester, gas-holder, or custom-separator CAPEX is assigned.", "Custom Phase 5 purchase-cost fields remain zero; supported H501 utility/cost results remain visible.", "No approved cost correlation or vendor quote is available.", "Phase 5 and total-plant TEA conclusions are unavailable.", "Vendor quotations or documented cost correlations with year, currency, capacity, exponent, and validity range.", outputs="equipment and system cost results", source="vendor or traceable industry cost source", literature=True, industry=True, experimental=False, priority="high"),
    _entry("LIM-P5-016", 5, "systems", "R501", "controls", "The digester is steady-state and has no startup, upset, or automatic control simulation.", "pH, temperature, OLR, gas, and alarm values are monitoring metadata only.", "Time-series feed, controller tuning, biomass inventory, and dynamic kinetics are unavailable.", "Startup time, instability, overload response, and control performance are not predicted.", "Dynamic feed data, control philosophy, online sensor data, and calibrated kinetic model.", outputs="operability and control conclusions", source="project operations and pilot data", literature=True, industry=True, experimental=True, priority="high", upgrade="Dynamic-model phase"),
    _entry("LIM-P5-017", 5, "phase5_units", "R501", "regulatory", "Raw biogas and digestate have no product or regulatory classification.", "The model reports inventories only and explicitly stops before gas upgrading and nutrient recovery.", "Gas-grid, emissions, digestate, and permitting requirements have not been evaluated.", "No compliance, sale, land-application, or sanitation claim can be made.", "Applicable Dutch/EU requirements, accredited analyses, and project permitting basis.", outputs="raw-biogas and digestate eligibility", source="regulatory specialist and accredited laboratory", literature=True, industry=True, experimental=True, priority="high"),
)


def build_limitations(model=None) -> tuple[ModelLimitation, ...]:
    """Return the permanent register updated for the selected Phase 5 scenario."""

    if model is None:
        return BASE_LIMITATIONS
    scenario_id = model.scenario.scenario_id
    values = model.parameters.get("values", {})
    result = []
    for item in BASE_LIMITATIONS:
        updated = item
        if item.phase == 5:
            value = values.get(item.temporary_parameter) if item.temporary_parameter else item.temporary_value
            updated = replace(
                item,
                temporary_value=item.temporary_value if value is None else value,
                comment=(
                    f"Selected scenario {scenario_id}. " + item.comment
                ).strip(),
            )
        result.append(updated)
    return tuple(result)


def limitation_rows(model=None) -> list[dict[str, Any]]:
    """Return flat rows suitable for CSV or Excel reporting."""

    return [item.as_dict() for item in build_limitations(model)]
