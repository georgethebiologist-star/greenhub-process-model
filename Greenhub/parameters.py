"""Static parameter schema retained for reports and future model phases.

Runtime Phase 3 values and their provenance are canonical in the master
workbook ``Phase3Parameters`` sheet and are resolved by ``phase3_inputs.py``.
Keeping values blank here avoids maintaining two competing assumption sets.
"""

from __future__ import annotations

from dataclasses import asdict

from Greenhub.input_schema import ParameterDefinition


def _p(category, name, python_name, value, unit, minimum, maximum, required, source, comment, phase, active):
    return ParameterDefinition(category, name, python_name, value, unit, minimum, maximum, "none", required, source, comment, phase, active)


PARAMETER_REGISTRY = (
    _p("feed", "Default feed temperature", "default_feed_temperature", 25.0, "degC", 0.0, 60.0, True, "Phase 1 assumption", "Workbook measurement overrides this value.", 1, True),
    _p("feed", "Default atmospheric pressure", "default_pressure", 101325.0, "Pa", 50000.0, 200000.0, True, "Phase 1 assumption", "Active Phase 2 system pressure.", 1, True),
    _p("primary_separation", "Default soluble fraction to clarified", "separator_default_soluble_split", 0.98, "fraction", 0.0, 1.0, True, "Engineering placeholder", "Fraction routed to clarified-liquid outlet.", 2, True),
    _p("primary_separation", "Default particulate fraction to clarified", "separator_default_particulate_split", 0.10, "fraction", 0.0, 1.0, True, "Engineering placeholder", "Fraction routed to clarified-liquid outlet.", 2, True),
    _p("preparation", "Cleaning electricity", "cleaning_electricity_kwh_per_t_wet", None, "kWh/t wet", 0.0, None, False, "Master workbook", "Active in grass-entry scenarios; load the scenario/month value from Phase3Parameters.", 3, True),
    _p("pef", "Specific energy", "specific_energy_kwh_per_t_wet", None, "kWh/t wet", 0.0, None, False, "Master workbook", "Active in F2/F3 only; no implicit default is applied.", 3, True),
    _p("pef", "Electric field strength", "electric_field_strength_kv_per_cm", None, "kV/cm", 0.0, None, False, "Master workbook", "Reported design input; it does not independently create mass or energy.", 3, True),
    _p("pef", "Pulse width", "pulse_width_us", None, "us", 0.0, None, False, "Master workbook", "Reported design input for F2/F3.", 3, True),
    _p("pef", "Pulse number", "number_of_pulses", None, "count", 0.0, None, False, "Master workbook", "Reported design input for F2/F3.", 3, True),
    _p("pef", "Cell disintegration index", "cell_disintegration_index", None, "fraction", 0.0, 1.0, False, "Master workbook", "Empirical PEF performance indicator.", 3, True),
    _p("pressing", "Juice yield", "juice_yield_kg_per_kg_wet_feed", None, "kg/kg wet grass", 0.0, 1.0, False, "Master workbook", "Mode A only; checked against the cake-moisture target.", 3, True),
    _p("pressing", "Cake moisture", "cake_moisture_fraction", None, "fraction wet basis", 0.0, 1.0, False, "Master workbook", "Mode A analytical water-partition target.", 3, True),
    _p("pressing", "Dry-matter recovery", "dry_solids_recovery_to_cake", None, "fraction to cake", 0.0, 1.0, False, "Master workbook", "Mode A component-partitioning input.", 3, True),
    _p("centrifuge", "TSS removal", "tss_removal_efficiency", None, "fraction removed", 0.0, 1.0, False, "Master workbook", "Active in all Phase 3 scenarios.", 3, True),
    _p("centrifuge", "Sludge moisture", "sludge_moisture_fraction", None, "fraction wet basis", 0.0, 1.0, False, "Master workbook", "Analytical sludge-water partition target.", 3, True),
    _p("centrifuge", "Specific electricity", "centrifuge_electricity_kwh_per_m3", None, "kWh/m3", 0.0, None, False, "Master workbook", "Hydraulic-load electricity basis.", 3, True),
    _p("protein_recovery", "Protein recovery", "protein_recovery", None, "fraction", 0.0, 1.0, False, "Not yet available", "Deferred to Phase 4; no protein recovery unit is active in Phase 3.", 4, False),
    _p("digestion", "COD removal", "digester_cod_removal", None, "fraction", 0.0, 1.0, False, "Not yet available", "Inactive until digestion is implemented.", 3, False),
    _p("struvite", "Phosphorus recovery", "struvite_p_recovery", None, "fraction", 0.0, 1.0, False, "Not yet available", "Inactive until nutrient recovery is implemented.", 3, False),
    _p("ammonia_recovery", "Ammonia recovery", "ammonia_recovery", None, "fraction", 0.0, 1.0, False, "Not yet available", "Inactive until nutrient recovery is implemented.", 3, False),
)


def parameter_table() -> list[dict[str, object]]:
    """Return parameter registry rows for reporting or workbook creation."""

    return [asdict(parameter) for parameter in PARAMETER_REGISTRY]
