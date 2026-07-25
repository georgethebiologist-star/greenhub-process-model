"""Permanent Phase 6 limitations and missing-data register."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from Greenhub.phase5_limitations import ModelLimitation, _entry, build_limitations


PHASE6_LIMITATIONS: tuple[ModelLimitation, ...] = (
    _entry("LIM-P6-001", 6, "phase6_units", "G601/S601", "thermodynamics", "Biogas cooling uses pure-water saturation pressure and ideal-gas humidity.", "A Magnus saturation-pressure equation calculates condensation; trace-gas dissolution is empirical.", "Validated gas dew-point, fugacity, and condensate-composition data are unavailable.", "Cooling duty, condensate rate, and wet gas composition are screening-level.", "Raw-gas humidity/dew point, cooler outlet data, condensate composition, and validated thermodynamics.", priority="high", parameter="gas_cooler_outlet_temperature_c", value="class E workbook value", unit="degC"),
    _entry("LIM-P6-002", 6, "phase6_units", "S601", "design", "Condensate-separator geometry is residence-time based.", "A working volume is calculated without droplet-size or entrainment correlations.", "Droplet distribution, allowable carryover, and vendor separator data are missing.", "Separator diameter, carryover, and CAPEX are not design-grade.", "Vendor knock-out sizing, droplet distribution, demister efficiency, and pressure-drop data.", industry=True),
    _entry("LIM-P6-003", 6, "phase6_units", "R601", "separation", "H2S removal and media replacement use class-E removal and capacity values.", "Activated carbon retains an intact H2S-equivalent pool; iron sponge and biological modes use explicit stoichiometry.", "GreenHub inlet loading, breakthrough curves, humidity response, and media grade are unknown.", "Residual H2S, media use, replacement interval, and waste rate are uncertain.", "Seasonal H2S data and vendor breakthrough/capacity tests at GreenHub humidity and flow.", source="project gas analysis and media vendor", industry=True, priority="high"),
    _entry("LIM-P6-004", 6, "phase6_units", "R601 biological/iron modes", "kinetics", "Iron-sponge hydration and biological kinetics are not represented.", "Only complete screening stoichiometries and oxygen demand are available.", "Media phase composition, microbial kinetics, sulfur selectivity, and reactor data are missing.", "Alternative R601 mode sizing and utility results are structural only.", "Pilot/vendor data for iron media conversion or biological sulfur oxidation and air transfer.", priority="medium"),
    _entry("LIM-P6-005", 6, "phase6_units", "R602", "thermodynamics", "Ammonia washing does not solve pH-dependent gas-liquid equilibrium.", "Water wash uses apparent partition fractions; acid mode forms a molecular ammonium salt.", "Gas NH3, wash-water pH, alkalinity, Henry data, and titration data are unavailable.", "Water/acid demand, methane loss, and residual ammonia are uncertain.", "Raw-gas ammonia, wash tests, pH, temperature, acid titration, and complete liquor analysis.", priority="high"),
    _entry("LIM-P6-006", 6, "phase6_units", "F601", "contaminants", "Siloxanes are represented by one D5-equivalent marker and empirical capture.", "Zero input remains zero; the marker can be populated when analyses become available.", "Compound-resolved siloxane and particulate gas measurements are unavailable.", "Media consumption, engine/membrane protection, and silicon risk cannot be validated.", "D4/D5/D6 and particulate measurements plus filter-media breakthrough curves.", outputs="gas quality, media replacement, and downstream protection", priority="high"),
    _entry("LIM-P6-007", 6, "phase6_upgrading", "A611/V612/A612", "mass_transfer", "Water scrubbing uses a calibrated apparent-partition model.", "Removal responds monotonically to pressure, temperature, and gross water circulation; dissolved gases are flashed and regenerated explicitly.", "Henry constants, stage efficiencies, packing transfer data, and pilot calibration are missing.", "Purity, recovery, methane slip, column size, and water circulation are uncertain.", "Pilot water-scrubber gas/liquid balances over pressure, temperature, and L/G ratio.", parameter="water_scrubber_co2_absorption_fraction", value="class E workbook value", unit="fraction", priority="high"),
    _entry("LIM-P6-008", 6, "phase6_upgrading", "D611/D621/D631", "separation", "Gas drying uses bounded water-removal fractions.", "Water is conserved to explicit condensate streams without a desiccant or dew-point model.", "Product dew point, desiccant equilibrium, regeneration, and vendor data are unavailable.", "Product humidity, dryer sizing, regeneration utility, and compliance are uncertain.", "Required product dew point and vendor drying/regeneration performance.", priority="high"),
    _entry("LIM-P6-009", 6, "phase6_upgrading", "M621-M623", "mass_transfer", "Membrane permeances and area are class-E structural values.", "Segmented solution-diffusion flux uses component partial-pressure driving force and computes stage cut.", "Validated mixed-gas permeance, plasticization, aging, fouling, module pressure loss, and recycle data are missing.", "Purity, recovery, area, replacement, and compressor duty are uncertain.", "Vendor mixed-gas permeance/selectivity and module tests at GreenHub composition, pressure, humidity, and contaminants.", source="membrane vendor and pilot tests", industry=True, priority="high"),
    _entry("LIM-P6-010", 6, "phase6_upgrading", "A631", "separation", "PSA is a Level-1 cycle-average allocation rather than a dynamic bed model.", "Pressure-responsive adsorption fractions, purge, working capacity, and complete blowdown allocation conserve material.", "Competitive isotherms, mass-transfer coefficients, bed sequencing, equalization, and breakthrough data are unavailable.", "Purity, recovery, adsorbent inventory, cycle timing, and power are uncertain.", "Vendor/pilot cycle data and competitive isotherms for the selected adsorbent.", source="PSA vendor and pilot tests", industry=True, priority="high"),
    _entry("LIM-P6-011", 6, "phase6_upgrading", "A641/A642", "chemistry", "MEA absorption uses equivalent loading rather than rigorous electrolyte chemistry.", "CO2 circulation follows captured CO2 divided by rich-minus-lean loading; solvent is regenerated and recycled.", "Activity coefficients, speciation, rate-based packing data, and validated solvent composition are unavailable.", "Solvent circulation, purity, column design, and H2S interaction are screening-level.", "Rate-based MEA absorber/stripper data, electrolyte parameters, solvent analyses, and packing performance.", priority="high"),
    _entry("LIM-P6-012", 6, "phase6_upgrading", "H641/V641", "heat_transfer", "MEA regeneration heat is a specific-energy placeholder.", "Reboiler and condenser duties are explicit, with sensible rich/lean recovery reported separately.", "Steam conditions, water vaporization, desorption heat, exchanger approach, and heat-loss data are missing.", "MEA heat demand and integration potential are highly uncertain.", "Pilot/vendor heat balance, steam/reflux data, exchanger approach temperatures, and heat losses.", parameter="mea_regeneration_energy_mj_per_kg_co2", value="class E workbook value", unit="MJ/kg CO2", priority="high"),
    _entry("LIM-P6-013", 6, "phase6_upgrading", "MEA solvent losses", "chemistry", "MEA degradation is one elemental-equivalent pool.", "Only selected degradation and physical-loss fractions create makeup and spent-solvent streams.", "Thermal/oxidative degradation, heat-stable salts, corrosion, and reclaiming data are unavailable.", "Solvent makeup, waste classification, emissions, and OPEX are uncertain.", "Long-duration solvent analysis, reclaiming data, corrosion testing, and vendor loss guarantees.", priority="medium"),
    _entry("LIM-P6-014", 6, "phase6_units/phase6_upgrading", "custom Phase 6 equipment", "costing", "No custom gas-cleaning or upgrading CAPEX correlation is approved.", "Custom purchase costs remain zero; supported BioSTEAM compressor, pump, and exchanger results remain visible.", "Project-scale vendor quotations and traceable cost correlations are unavailable.", "No Phase 6 TEA ranking or final technology selection is supported.", "Vendor quotations or documented correlations with year, currency, capacity, exponent, and range.", outputs="equipment and system cost results", source="technology vendors or traceable industry source", industry=True, experimental=False, priority="high"),
    _entry("LIM-P6-015", 6, "phase6_validation", "conditioned_biogas", "regulatory", "Feed and product quality limits are structural checks rather than selected end-use standards.", "The model reports exceedances and warns in structural mode; it does not claim grid compliance.", "Project end use, Dutch/EU standard edition, pressure class, odorization, Wobbe index, and contaminant limits are not selected.", "Biomethane cannot yet be labelled grid-injection or vehicle-fuel compliant.", "Select end use and applicable current standard, then provide accredited complete gas analysis.", outputs="feed suitability and biomethane quality", source="regulatory specialist and accredited laboratory", literature=True, industry=True, experimental=True, priority="high"),
    _entry("LIM-P6-016", 6, "scenarios", "BG1/BG6", "data_quality", "CHP and cryogenic scenarios remain inactive data-gated architectures.", "Factories raise clear missing-data errors instead of simulating arbitrary efficiencies or cryogenic fixed splits.", "CHP maps/combustion integration and low-temperature thermodynamics are reserved for later sections.", "No BG1 or BG6 performance comparison is available.", "CHP engine and heat-network specification; validated cryogenic EOS, phase envelope, and refrigeration design.", outputs="scenario readiness and comparison", priority="high", upgrade="Next Phase 6 section and future cryogenic study"),
    _entry("LIM-P6-017", 6, "systems", "plant utility network", "energy", "Plant-wide CHP, heat recovery, biomethane storage/compression, and grid injection are not yet implemented.", "Technology-specific utilities are calculated locally and kept ready for the next integration section.", "The attached specification explicitly assigns these systems to the next section.", "Net plant import/export and integrated heat use cannot yet be reported.", "CHP, heat-exchanger-network, storage, final-compression, grid-interface, and operating-priority specifications.", outputs="net electricity, net heat, and final usable energy", priority="high", upgrade="Next Phase 6 section"),
    _entry("LIM-P6-018", 6, "streams", "raw_biogas", "data_quality", "Raw-gas trace contaminants are absent unless measured upstream values exist.", "Blank siloxane/particulate inputs remain zero and do not break simulation.", "No GreenHub raw-gas trace-contaminant laboratory dataset is available.", "Pretreatment loading and media replacement may be understated.", "Seasonal complete raw-gas analysis including humidity, NH3, H2S, O2, siloxanes, and particulates.", priority="high"),
)


def build_phase6_limitations(model=None) -> tuple[ModelLimitation, ...]:
    """Return the permanent Phase 1-6 register for a selected model."""

    upstream = build_limitations(model.upstream_model) if model is not None else build_limitations()
    if model is None:
        return (*upstream, *PHASE6_LIMITATIONS)
    values = model.parameters.get("values", {})
    selected: list[ModelLimitation] = list(upstream)
    for item in PHASE6_LIMITATIONS:
        value = (
            values.get(item.temporary_parameter)
            if item.temporary_parameter
            else item.temporary_value
        )
        selected.append(
            replace(
                item,
                temporary_value=item.temporary_value if value is None else value,
                comment=(
                    f"Selected scenario {model.scenario.scenario_id}. " + item.comment
                ).strip(),
            )
        )
    return tuple(selected)


def phase6_limitation_rows(model=None) -> list[dict[str, Any]]:
    """Return flat limitation rows for report writers."""

    return [item.as_dict() for item in build_phase6_limitations(model)]
