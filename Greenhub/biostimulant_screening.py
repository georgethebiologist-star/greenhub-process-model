"""Hormone-capture screening calculations for the gated PR7 route.

This module calculates analyte-equivalent mass recovery from clarified juice.
It does not predict membrane flux decline, bulk retentate composition, product
quality, utilities, or economics.
"""

from __future__ import annotations

import csv
import math
import threading
from uuid import uuid4
from dataclasses import dataclass
from pathlib import Path


DATA_PATH = (
    Path(__file__).parent
    / "data"
    / "Protein recovery"
    / "Membrane"
    / "biostimulant_hormone_benchmarks.csv"
)

TECHNOLOGY_COLUMNS = {
    "TUF": "retention_TUF_fraction",
    "LNF": "retention_LNF_fraction",
    "MEUF": "retention_MEUF_fraction",
}

FLUX_BASELINE_L_M2_H = {"TUF": 22.0, "LNF": 12.0, "MEUF": 22.5}
_BIOSTEAM_SCREEN_LOCK = threading.RLock()


def _parameter_value(parameter_id: str, component_target: str, membrane_class: str = "ALL") -> float:
    """Load one explicitly populated screening parameter from its data register."""
    matches = [
        row for row in _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
        if row["parameter_id"] == parameter_id
        and row["component_target"] == component_target
        and row["membrane_class"] == membrane_class
    ]
    if len(matches) != 1 or not matches[0]["value"].strip():
        raise ValueError(f"Missing or ambiguous gated parameter: {parameter_id}/{component_target}/{membrane_class}.")
    value = float(matches[0]["value"])
    if not math.isfinite(value):
        raise ValueError(f"Parameter {parameter_id}/{component_target} must be finite.")
    return value


@dataclass(frozen=True)
class HormoneCaptureResult:
    """Annual total hormone-equivalent capture for one analyte.

    Free/bound feed and captured quantities use the distinct state-retention
    factors registered in the user-supplied screening dataset.
    """

    solute_id: str
    technology_id: str
    feed_volume_m3_year: float
    total_feed_kg_year: float
    free_feed_kg_year: float
    bound_feed_kg_year: float
    total_retention_fraction: float
    captured_total_kg_year: float
    captured_free_kg_year: float | None
    captured_bound_kg_year: float | None
    permeate_total_kg_year: float
    benchmark_concentration_ug_L: float
    evidence_status: str
    state_specific_capture_status: str


@dataclass(frozen=True)
class MembraneFluxResult:
    """Flux from the supplied resistance model at explicit pressure/feed ratio."""

    technology_id: str
    pressure_bar: float
    feed_to_reference_concentration_ratio: float
    membrane_resistance_m_inv: float
    fouling_resistance_m_inv: float
    gel_resistance_m_inv: float
    predicted_flux_L_m2_h: float
    empirical_baseline_flux_L_m2_h: float


@dataclass(frozen=True)
class MembraneScreeningResult:
    """Volume, area and gross revenue screen at a specified VCF and flux."""

    technology_id: str
    feed_volume_m3_year: float
    concentration_factor: float
    product_volume_L_year: float
    permeate_volume_L_year: float
    flux_L_m2_h: float
    flux_basis: str
    operating_hours_year: float
    membrane_area_m2: float
    price_EUR_L: float
    gross_revenue_EUR_year: float
    membrane_module_capex_low_EUR: float
    membrane_module_capex_high_EUR: float
    annualized_replacement_low_EUR_year: float
    annualized_replacement_high_EUR_year: float
    fx_eur_per_usd: float
    fx_date: str
    fx_source: str


def estimate_pressure_work_electricity(
    feed_volume_m3_year: float,
    concentration_factor: float,
    transmembrane_pressure_bar: float,
    pump_efficiency_fraction: float,
) -> dict[str, float | str]:
    """Estimate permeate-side hydraulic electricity from sourced inputs.

    This is a pressure-work lower-bound screen: it excludes crossflow
    recirculation, pressure losses, CIP, controls, and other auxiliaries.
    """
    feed = float(feed_volume_m3_year)
    vcf = float(concentration_factor)
    pressure = float(transmembrane_pressure_bar)
    efficiency = float(pump_efficiency_fraction)
    if not all(math.isfinite(value) for value in (feed, vcf, pressure, efficiency)):
        raise ValueError("Hydraulic energy inputs must be finite.")
    if feed < 0.0 or vcf <= 1.0 or pressure <= 0.0 or not 0.0 < efficiency <= 1.0:
        raise ValueError("Feed must be non-negative, VCF > 1, pressure > 0, and pump efficiency in (0, 1].")
    permeate = feed * (1.0 - 1.0 / vcf)
    electricity = pressure * 1e5 * permeate / 3.6e6 / efficiency
    return {
        "basis": "permeate-side pressure work only; excludes crossflow circulation, pressure losses, CIP, and auxiliaries",
        "permeate_volume_m3_year": permeate,
        "transmembrane_pressure_bar": pressure,
        "pump_efficiency_fraction": efficiency,
        "electricity_kwh_year": electricity,
        "electricity_mwh_year": electricity / 1000.0,
    }


ENERGY_INPUTS = {
    "electricity": (
        "annual_electricity_kwh",
        "electricity_kg_co2e_kwh",
        "electricity_price_eur_kwh",
    ),
    "heat": (
        "annual_heat_kwh",
        "heat_kg_co2e_kwh",
        "heat_price_eur_kwh",
    ),
}


def calculate_energy_tea_lca_screen(
    *,
    annual_electricity_kwh: float | None = None,
    electricity_kg_co2e_kwh: float | None = None,
    electricity_price_eur_kwh: float | None = None,
    annual_heat_kwh: float | None = None,
    heat_kg_co2e_kwh: float | None = None,
    heat_price_eur_kwh: float | None = None,
    input_sources: dict[str, str] | None = None,
) -> dict[str, object]:
    """Calculate energy-only climate and cost subtotals from sourced inputs.

    Missing utilities are never interpreted as zero. A source note is required
    for each supplied numeric input. A documented zero activity closes that
    utility category without needing a factor or price.
    """

    values = {
        "annual_electricity_kwh": annual_electricity_kwh,
        "electricity_kg_co2e_kwh": electricity_kg_co2e_kwh,
        "electricity_price_eur_kwh": electricity_price_eur_kwh,
        "annual_heat_kwh": annual_heat_kwh,
        "heat_kg_co2e_kwh": heat_kg_co2e_kwh,
        "heat_price_eur_kwh": heat_price_eur_kwh,
    }
    sources = dict(input_sources or {})
    unknown_sources = set(sources) - set(values)
    if unknown_sources:
        raise ValueError("Unknown energy input source keys: " + ", ".join(sorted(unknown_sources)))
    unused_sources = {key for key in sources if values[key] is None}
    if unused_sources:
        raise ValueError("Source notes were supplied without corresponding numeric values: " + ", ".join(sorted(unused_sources)))
    for name, value in values.items():
        if value is None:
            continue
        number = float(value)
        if not math.isfinite(number) or number < 0.0:
            raise ValueError(f"{name} must be finite and non-negative.")
        if not isinstance(sources.get(name), str) or not sources[name].strip():
            raise ValueError(f"A non-empty input_sources note is required for {name}.")
        values[name] = number

    by_utility = {}
    known_climate = 0.0
    known_cost = 0.0
    climate_any = False
    cost_any = False
    climate_complete = True
    cost_complete = True
    missing_climate = []
    missing_cost = []
    for utility, (quantity_key, factor_key, price_key) in ENERGY_INPUTS.items():
        quantity = values[quantity_key]
        factor = values[factor_key]
        price = values[price_key]
        climate = quantity * factor if quantity is not None and factor is not None else (0.0 if quantity == 0.0 else None)
        cost = quantity * price if quantity is not None and price is not None else (0.0 if quantity == 0.0 else None)
        if climate is None:
            climate_complete = False
            missing_climate.extend(key for key in (quantity_key, factor_key) if values[key] is None and not (quantity == 0.0 and key == factor_key))
        else:
            climate_any = True
            known_climate += climate
        if cost is None:
            cost_complete = False
            missing_cost.extend(key for key in (quantity_key, price_key) if values[key] is None and not (quantity == 0.0 and key == price_key))
        else:
            cost_any = True
            known_cost += cost
        by_utility[utility] = {
            "annual_energy_kwh": quantity,
            "emission_factor_kg_co2e_kwh": factor,
            "energy_cost_eur_kwh": price,
            "energy_climate_kg_co2e_year": climate,
            "energy_cost_eur_year": cost,
            "source_notes": {key: sources[key] for key in (quantity_key, factor_key, price_key) if key in sources},
        }

    return {
        "scope": "membrane-route energy only; excludes chemicals, membrane manufacture, waste, and product use/substitution",
        "climate_status": "complete_energy_only" if climate_complete else "partial" if climate_any else "not_calculated",
        "energy_climate_kg_co2e_year": known_climate if climate_complete else None,
        "known_energy_climate_subtotal_kg_co2e_year": known_climate if climate_any else None,
        "climate_missing_inputs": sorted(set(missing_climate)),
        "tea_status": "energy_cost_only" if cost_complete else "partial" if cost_any else "not_calculated",
        "energy_cost_eur_year": known_cost if cost_complete else None,
        "known_energy_cost_subtotal_eur_year": known_cost if cost_any else None,
        "tea_missing_inputs": sorted(set(missing_cost)),
        "by_utility": by_utility,
        "input_sources": sources,
    }


def calculate_cip_reagent_screen(
    *,
    operating_hours_year: float,
    solution_volume_L_per_step: float,
    makeup_fraction_per_cycle: float,
    input_source: str,
    include_screening_lca: bool = False,
) -> dict[str, object]:
    """Calculate PR7 CIP reagent make-up mass and cost from explicit inputs.

    Each CIP is modelled as one NaOH wash and one citric-acid wash, each with
    the supplied working-solution volume. The make-up fraction is the share of
    each working-solution batch replaced after every event. Dilute solution
    density is approximated as 1 kg/L and is reported as such. This excludes
    CIP water cost, heating, labor, downtime, disposal, and any cleaning-loop
    loss/recovery not represented by the entered make-up fraction.
    """
    hours = float(operating_hours_year)
    volume = float(solution_volume_L_per_step)
    makeup = float(makeup_fraction_per_cycle)
    if not all(math.isfinite(value) for value in (hours, volume, makeup)):
        raise ValueError("CIP hours, solution volume, and make-up fraction must be finite.")
    if hours < 0.0 or volume <= 0.0 or not 0.0 <= makeup <= 1.0:
        raise ValueError("CIP hours must be non-negative, volume positive, and make-up fraction in [0, 1].")
    if not isinstance(input_source, str) or not input_source.strip():
        raise ValueError("A source/evidence note is required for CIP volume and make-up fraction.")

    interval_h = _parameter_value("CIP_Interval", "Membrane")
    naoh_working_wt = _parameter_value("CIP_Sodium_Hydroxide_Concentration", "CIP_Solution") / 100.0
    citric_working_wt = _parameter_value("CIP_Citric_Acid_Concentration", "CIP_Solution") / 100.0
    naoh_stock_wt = 0.50
    naoh_stock_price_eur_t = _parameter_value("CIP_NaOH_50pct_Price", "NaOH_50wt_solution")
    citric_price_eur_t = _parameter_value("CIP_Citric_Acid_Price", "Citric_Acid_bulk")
    price_rows = {
        row["parameter_id"]: row
        for row in _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
        if row["parameter_id"] in {"CIP_NaOH_50pct_Price", "CIP_Citric_Acid_Price"}
    }
    events = hours / interval_h
    solution_mass_kg = volume  # documented working-solution density screen: 1 kg/L
    solution_replaced_kg_year_per_step = solution_mass_kg * makeup * events
    naoh_active_kg = solution_mass_kg * naoh_working_wt * makeup * events
    naoh_stock_kg = naoh_active_kg / naoh_stock_wt
    citric_acid_kg = solution_mass_kg * citric_working_wt * makeup * events
    naoh_cost = naoh_stock_kg / 1000.0 * naoh_stock_price_eur_t
    citric_cost = citric_acid_kg / 1000.0 * citric_price_eur_t

    result = {
        "status": "screening_calculated_from_explicit_volume_and_makeup_fraction",
        "operating_hours_year": hours,
        "cip_events_year": events,
        "interval_operating_hours": interval_h,
        "cip_interval_operating_hours": interval_h,
        "solution_volume_L_per_step_per_event": volume,
        "makeup_fraction_per_cycle": makeup,
        "solution_density_kg_L": 1.0,
        "density_basis": "explicit screening approximation for dilute cleaning solutions; replace with measured density if available",
        "solution_mass_replaced_kg_year_per_step": solution_replaced_kg_year_per_step,
        "working_solution_volume_L_per_step": volume,
        "working_solution_density_kg_L": 1.0,
        "makeup_fraction_per_cycle": makeup,
        "naoh": {
            "working_solution_concentration_wt_pct": naoh_working_wt * 100.0,
            "working_solution_wt_fraction": naoh_working_wt,
            "active_naoh_kg_year": naoh_active_kg,
            "purchased_50wt_solution_kg_year": naoh_stock_kg,
            "price_eur_t": naoh_stock_price_eur_t,
            "cost_eur_year": naoh_cost,
            "price_source_status": price_rows["CIP_NaOH_50pct_Price"]["source_status"],
        },
        "citric_acid": {
            "working_solution_concentration_wt_pct": citric_working_wt * 100.0,
            "working_solution_wt_fraction": citric_working_wt,
            "citric_acid_kg_year": citric_acid_kg,
            "price_eur_t": citric_price_eur_t,
            "cost_eur_year": citric_cost,
            "price_source_status": price_rows["CIP_Citric_Acid_Price"]["source_status"],
        },
        "total_reagent_cost_eur_year": naoh_cost + citric_cost,
        "price_references": [
            {
                "parameter_id": key,
                "value": float(row["value"]),
                "units": row["units"],
                "source_reference": row["source_reference"],
                "source_status": row["source_status"],
                "source_date": row["source_date"],
                "model_use": row["model_use"],
            }
            for key, row in price_rows.items()
        ],
        "cost_boundary": (
            "working-chemical make-up only; excludes CIP water, heat, labor, downtime, "
            "disposal, and recovery-loop losses beyond the entered make-up fraction"
        ),
        "input_source": input_source.strip(),
    }
    if include_screening_lca:
        factors = {
            row["factor_id"]: row
            for row in _load_csv_rows("biostimulant_chemical_lca_factors.csv")
        }
        naoh_factor = factors["pr7_cip_naoh_active"]
        citric_factor = factors["pr7_cip_citric_acid"]
        naoh_kgco2e = naoh_active_kg * float(naoh_factor["value"])
        citric_kgco2e = citric_acid_kg * float(citric_factor["value"])
        result["screening_lca"] = {
            "status": "opt_in_attributional_upstream_chemical_screen; not a complete PR7 LCA",
            "naoh_production_kg_CO2e_year": naoh_kgco2e,
            "citric_acid_production_kg_CO2e_year": citric_kgco2e,
            "total_chemical_production_kg_CO2e_year": naoh_kgco2e + citric_kgco2e,
            "factors": [
                {key: factor[key] for key in (
                    "chemical_id", "factor_id", "value", "quantity_unit", "geography",
                    "reference_year", "system_boundary", "allocation", "method",
                    "source_title", "source_url", "source_status", "warning",
                )}
                for factor in (naoh_factor, citric_factor)
            ],
            "excluded": [
                "CIP water, heating, pumping, and labor",
                "cleaning wastewater treatment and disposal",
                "membrane manufacture and replacement",
                "MEUF surfactant recovery and fate",
            ],
        }
    else:
        result["screening_lca"] = None
    return result


def calculate_meuf_surfactant_screen(feed_volume_m3_year: float) -> dict[str, object]:
    """Screen SDS dose and unrecovered make-up for the user-supplied MEUF basis.

    The treated aqueous volume is set equal to clarified-juice feed volume
    (1 kg ~= 1 L project convention). This is a screening inventory only: it
    does not add SDS to BioSTEAM streams or estimate acid, energy, price,
    residual surfactant fate, or product compliance.
    """
    volume = float(feed_volume_m3_year)
    if not math.isfinite(volume) or volume < 0.0:
        raise ValueError("feed_volume_m3_year must be finite and non-negative.")
    cmc_mol_L = _parameter_value("SDS_CMC", "MEUF_Surfactant", "MEUF") / 1000.0
    dose_low = _parameter_value("MEUF_Surfactant_Dose_Low", "MEUF_Surfactant", "MEUF")
    dose_high = _parameter_value("MEUF_Surfactant_Dose_High", "MEUF_Surfactant", "MEUF")
    recovery = _parameter_value("MEUF_Surfactant_Recovery", "MEUF_Surfactant", "MEUF")
    molecular_weight_g_mol = _parameter_value(
        "SDS_Molecular_Weight", "Sodium_Dodecyl_Sulfate", "MEUF"
    )
    price_reference = next(
        row for row in _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
        if row["parameter_id"] == "MEUF_SDS_Price_LabGrade"
    )
    price_references = [
        {
            "value": float(row["value"]),
            "units": row["units"],
            "source_reference": row["source_reference"],
            "source_status": row["source_status"],
            "source_date": row["source_date"],
            "model_use": row["model_use"],
        }
        for row in _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
        if row["parameter_id"] in {"MEUF_SDS_Price_20kg_Pack", "MEUF_SDS_Price_LabGrade"}
    ]

    def dose(multiple: float) -> dict[str, float]:
        gross_kg = volume * cmc_mol_L * multiple * molecular_weight_g_mol
        recovered_kg = gross_kg * recovery
        return {
            "dose_multiple_CMC": multiple,
            "dose_mmol_L": cmc_mol_L * multiple * 1000.0,
            "gross_SDS_kg_year": gross_kg,
            "recovered_SDS_kg_year": recovered_kg,
            "unrecovered_makeup_SDS_kg_year": gross_kg - recovered_kg,
        }

    return {
        "status": "screening_inventory_only; not added to BioSTEAM material balances",
        "surfactant": "SDS",
        "treated_solution_volume_m3_year": volume,
        "solution_volume_basis": "clarified-juice feed volume; 1 kg ~= 1 L project convention",
        "CMC_mmol_L": cmc_mol_L * 1000.0,
        "molecular_weight_g_mol": molecular_weight_g_mol,
        "recovery_fraction": recovery,
        "dose_low": dose(dose_low),
        "dose_high": dose(dose_high),
        "missing_for_TEA_LCA": [
            "SDS purchase price and grade", "acid identity and precipitation stoichiometry",
            "recovery-loop energy and yield validation", "residual surfactant fate and product limit",
            "surfactant and acid upstream climate factors",
        ],
        "price_reference_only": {
            "value": float(price_reference["value"]),
            "units": price_reference["units"],
            "source_reference": price_reference["source_reference"],
            "source_status": price_reference["source_status"],
            "source_date": price_reference["source_date"],
            "model_use": price_reference["model_use"],
        },
        "price_references_only": price_references,
        "source_status": "user-supplied screening parameters; independently unverified",
    }
def _load_benchmarks(path: Path = DATA_PATH) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No hormone benchmarks found in {path}.")
    return rows


def _load_csv_rows(filename: str) -> list[dict[str, str]]:
    with (DATA_PATH.parent / filename).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def membrane_flux_bounds(technology_id: str) -> tuple[float, float]:
    """Return the supplied empirical flux range for a membrane option."""
    technology = str(technology_id).strip().upper()
    row = next((
        item for item in _load_csv_rows("biostimulant_membrane_options.csv")
        if item["technology_id"] == technology
    ), None)
    if row is None:
        raise ValueError("technology_id must be TUF, LNF, or MEUF.")
    return float(row["permeate_flux_min_L_m2_h"]), float(row["permeate_flux_max_L_m2_h"])


def calculate_hormone_capture(
    feed_volume_m3_year: float,
    technology_id: str,
    *,
    flux_L_m2_h: float | None = None,
    benchmark_path: Path = DATA_PATH,
) -> tuple[HormoneCaptureResult, ...]:
    """Calculate screen-level target-hormone recovery from juice volume.

    Concentrations, state fractions, and state-specific retention factors are
    read from the editable, user-supplied benchmark CSV. Output excludes
    carrier/matrix mass.
    """

    volume = float(feed_volume_m3_year)
    if not math.isfinite(volume) or volume < 0.0:
        raise ValueError("feed_volume_m3_year must be finite and non-negative.")
    technology = str(technology_id).strip().upper()
    if technology not in TECHNOLOGY_COLUMNS:
        raise ValueError("technology_id must be TUF, LNF, or MEUF.")
    flux = FLUX_BASELINE_L_M2_H[technology] if flux_L_m2_h is None else float(flux_L_m2_h)
    if not math.isfinite(flux) or flux <= 0.0:
        raise ValueError("flux_L_m2_h must be finite and positive.")
    results = []
    for row in _load_benchmarks(benchmark_path):
        concentration = float(row["total_concentration_ug_L"])
        free_fraction = float(row["free_fraction"])
        bound_fraction = float(row["bound_fraction"])
        free_retention = float(row[f"retention_{technology}_free_fraction"])
        bound_retention = float(row[f"retention_{technology}_bound_fraction"])
        reference_retention = (
            free_fraction * free_retention + bound_fraction * bound_retention
        )
        declared_reference_retention = float(row[f"retention_{technology}_fraction"])
        if not math.isclose(
            reference_retention,
            declared_reference_retention,
            rel_tol=1e-6,
            abs_tol=1e-8,
        ):
            raise ValueError(
                f"Inconsistent aggregate and state-specific {technology} retention "
                f"for {row['solute_id']}: weighted={reference_retention:.8g}, "
                f"registered={declared_reference_retention:.8g}."
            )
        if technology == "TUF":
            free_retention = float(
                calculate_film_retention(technology, row["solute_id"], "free", flux)[
                    "predicted_retention_fraction"
                ]
            )
        retention = free_fraction * free_retention + bound_fraction * bound_retention
        if not math.isfinite(concentration) or concentration < 0.0:
            raise ValueError(f"Concentration for {row['solute_id']} must be finite and non-negative.")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in (free_fraction, bound_fraction)):
            raise ValueError(f"Fractions for {row['solute_id']} must be in [0, 1].")
        if not math.isclose(free_fraction + bound_fraction, 1.0, abs_tol=1e-9):
            raise ValueError(f"Free and bound fractions do not sum to 1 for {row['solute_id']}.")
        if any(not 0.0 <= value <= 1.0 for value in (free_retention, bound_retention)):
            raise ValueError(f"State retention for {row['solute_id']} is outside [0, 1].")

        # ug/L * (m3/year * 1000 L/m3) * 1e-9 kg/ug
        feed_mass = concentration * volume * 1e-6
        captured = feed_mass * retention
        results.append(
            HormoneCaptureResult(
                solute_id=row["solute_id"],
                technology_id=technology,
                feed_volume_m3_year=volume,
                total_feed_kg_year=feed_mass,
                free_feed_kg_year=feed_mass * free_fraction,
                bound_feed_kg_year=feed_mass * bound_fraction,
                total_retention_fraction=retention,
                captured_total_kg_year=captured,
                captured_free_kg_year=feed_mass * free_fraction * free_retention,
                captured_bound_kg_year=feed_mass * bound_fraction * bound_retention,
                permeate_total_kg_year=feed_mass - captured,
                benchmark_concentration_ug_L=concentration,
                evidence_status=row["provenance"],
                state_specific_capture_status=(
                    "calculated_from_state_specific_user_supplied_screening_factors; "
                    "screening data not independently validated"
                ),
            )
        )
    return tuple(results)


def hormone_benchmark_feed_flows_kg_hr(feed_volume_m3_hr: float) -> dict[str, float]:
    """Convert registered clarified-juice benchmarks to analyte-equivalent kg/h.

    This function is only for an explicitly selected screening mode. It does
    not claim that the values are GreenHub measurements or add carrier mass.
    """
    volume = float(feed_volume_m3_hr)
    if not math.isfinite(volume) or volume < 0.0:
        raise ValueError("feed_volume_m3_hr must be finite and non-negative.")
    pool_ids = {
        "IAA": ("Indole3AceticAcid", "ProteinBoundIAA"),
        "Zeatin": ("Zeatin", "PeptideBoundZeatin"),
        "ZeatinRiboside": ("ZeatinRiboside", "BoundZeatinRiboside"),
    }
    flows: dict[str, float] = {}
    for row in _load_benchmarks():
        total_kg_hr = float(row["total_concentration_ug_L"]) * volume * 1e-6
        free_id, bound_id = pool_ids[row["solute_id"]]
        flows[free_id] = total_kg_hr * float(row["free_fraction"])
        flows[bound_id] = total_kg_hr * float(row["bound_fraction"])
    return flows


def calculate_resistance_flux(
    technology_id: str,
    pressure_bar: float,
    feed_to_reference_concentration_ratio: float,
    *,
    viscosity_Pa_s: float | None = None,
) -> MembraneFluxResult:
    """Apply J=ΔP/[μ(Rm+Rf+Rg)] using an explicit Cf/C0 ratio.

    The input values are user-supplied and are kept separate from the empirical
    baseline flux. This function intentionally exposes their disagreement.
    """

    technology = str(technology_id).strip().upper()
    if technology not in {"TUF", "LNF"}:
        raise ValueError("Resistance model is parameterized only for TUF or LNF.")
    pressure = float(pressure_bar)
    ratio = float(feed_to_reference_concentration_ratio)
    if not math.isfinite(pressure) or pressure <= 0.0:
        raise ValueError("pressure_bar must be finite and positive.")
    if not math.isfinite(ratio) or ratio <= 0.0:
        raise ValueError("Cf/C0 must be finite and positive.")
    rm = _parameter_value("Resistance_Rm", f"{technology}_Membrane", technology)
    # The registered 1.35 mPa·s value describes fermented juice. PR7 currently
    # excludes fermentation, so it cannot be silently reused for the active feed.
    if viscosity_Pa_s is None:
        raise ValueError(
            "No-fermentation PR7 flux requires an explicit unfermented-juice viscosity; "
            "the registered 1.35 mPa·s value is for fermented juice only."
        )
    viscosity = float(viscosity_Pa_s)
    if not math.isfinite(viscosity) or viscosity <= 0.0:
        raise ValueError("viscosity_Pa_s must be finite and positive.")
    fouling = _parameter_value("Resistance_Rf", "Fouling_Cake")
    gel_base = _parameter_value("Resistance_Rg0", "Gel_Layer")
    gel_exponent = _parameter_value("Resistance_Rg_Concentration_Exponent", "Gel_Layer")
    rg = gel_base * ratio**gel_exponent
    total_resistance = rm + fouling + rg
    flux_m_s = pressure * 1e5 / (viscosity * total_resistance)
    flux_L_m2_h = flux_m_s * 3.6e6
    return MembraneFluxResult(
        technology_id=technology,
        pressure_bar=pressure,
        feed_to_reference_concentration_ratio=ratio,
        membrane_resistance_m_inv=rm,
        fouling_resistance_m_inv=fouling,
        gel_resistance_m_inv=rg,
        predicted_flux_L_m2_h=flux_L_m2_h,
        empirical_baseline_flux_L_m2_h=FLUX_BASELINE_L_M2_H[technology],
    )


def calculate_film_retention(
    technology_id: str,
    solute_id: str,
    state: str,
    flux_L_m2_h: float,
    *,
    bound_diffusivity_m2_s: float | None = None,
) -> dict[str, float | str]:
    """Predict retention with the supplied sigma/Peclet equation.

    Bound-state diffusivity is required explicitly; it is not silently equated
    to the free analyte diffusivity.
    """

    technology = str(technology_id).strip().upper()
    form = str(state).strip().lower()
    if technology not in {"TUF", "LNF"} or form not in {"free", "bound"}:
        raise ValueError("Film model supports TUF/LNF and free/bound states.")
    if form == "free":
        try:
            diffusivity_targets = {
                "IAA": "Indole3AceticAcid",
                "Indole3AceticAcid": "Indole3AceticAcid",
                "Zeatin": "Zeatin",
                "ZeatinRiboside": "ZeatinRiboside",
            }
            diffusivity_target = diffusivity_targets[str(solute_id)]
            diffusivity = _parameter_value("Diffusivity_Dm", diffusivity_target)
        except (KeyError, ValueError) as error:
            raise ValueError(f"No free-state diffusivity is registered for {solute_id}.") from error
    else:
        if bound_diffusivity_m2_s is None:
            raise ValueError("Bound-state diffusivity is missing; supply a measured or documented value.")
        diffusivity = float(bound_diffusivity_m2_s)
    flux = float(flux_L_m2_h)
    if not math.isfinite(flux) or flux <= 0.0:
        raise ValueError("flux_L_m2_h must be finite and positive.")
    if not math.isfinite(diffusivity) or diffusivity <= 0.0:
        raise ValueError("Diffusivity must be finite and positive.")
    flux_m_s = flux / 3.6e6
    delta = _parameter_value("Boundary_Delta", "Polarization_Layer")
    sigma = _parameter_value("Reflection_Sigma", f"{form.title()}_Hormone_{technology}", technology)
    peclet = flux_m_s * delta / diffusivity
    exp_term = math.exp(-peclet)
    retention = sigma * (1.0 - exp_term) / (1.0 - sigma * exp_term)
    return {
        "technology_id": technology,
        "solute_id": str(solute_id),
        "state": form,
        "peclet_number": peclet,
        "reflection_coefficient": sigma,
        "predicted_retention_fraction": retention,
    }


def compare_empirical_and_film_retention(
    technology_id: str,
    flux_L_m2_h: float,
) -> dict[str, object]:
    """Compare supplied analyte retention inputs with free-solute film predictions.

    The sigma/Peclet equation predicts free solute only. TUF process splitting
    recalculates free-state retention at the selected flux; empirical bound
    retention remains fixed. LNF empirical free-state values are applied to
    the split, with film-model results retained as a diagnostic.
    """
    technology = str(technology_id).strip().upper()
    if technology not in {"TUF", "LNF"}:
        return {
            "technology_id": technology,
            "status": "not_available_for_membrane_class",
            "applied_to_process_split": False,
            "reason": "The supplied sigma/Peclet parameters are registered for TUF and LNF only.",
            "analytes": [],
        }
    rows = _load_benchmarks()
    results = []
    for row in rows:
        film = calculate_film_retention(
            technology, row["solute_id"], "free", flux_L_m2_h
        )
        free_fraction = float(row["free_fraction"])
        bound_fraction = float(row["bound_fraction"])
        bound_retention = float(row[f"retention_{technology}_bound_fraction"])
        applied_free = (
            float(film["predicted_retention_fraction"])
            if technology == "TUF"
            else float(row[f"retention_{technology}_free_fraction"])
        )
        weighted_retention = free_fraction * applied_free + bound_fraction * bound_retention
        results.append({
            "solute_id": row["solute_id"],
            "weighted_state_retention_fraction": weighted_retention,
            "process_split_free_retention_fraction": applied_free,
            "process_split_bound_retention_fraction": bound_retention,
            "film_free_retention_fraction": float(film["predicted_retention_fraction"]),
            "film_free_peclet_number": float(film["peclet_number"]),
            "reflection_coefficient": float(film["reflection_coefficient"]),
            "bound_film_retention_fraction": None,
            "bound_prediction_status": "missing_bound_payload_diffusivity",
        })
    return {
        "technology_id": technology,
        "status": "state_specific_screening_and_film_diagnostic",
        "flux_L_m2_h": float(flux_L_m2_h),
        "applied_to_process_split": technology == "TUF",
        "comparison_basis": (
            "TUF free-state process retention is recalculated with the sigma/Peclet equation at selected flux; "
            "supplied analyte-specific factors apply to carrier-associated pools. LNF applies supplied "
            "free-analyte values and 99% protein co-retention to bound payload; its film estimate is diagnostic. "
            "All values remain screening assumptions."
        ),
        "analytes": results,
    }


def calculate_membrane_area_and_revenue(
    feed_volume_m3_year: float,
    technology_id: str,
    *,
    operating_hours_year: float,
    concentration_factor: float | None = None,
    price_EUR_L: float | None = None,
    flux_L_m2_h: float | None = None,
) -> MembraneScreeningResult:
    """Calculate screening area and gross sales at a specified concentration factor.

    Area assumes steady feed, permeate = feed*(1 - 1/VCF), and no downtime,
    hydraulic hold-up, or cleaning-time penalty. Revenue is gross product sales.
    """

    technology = str(technology_id).strip().upper()
    if technology not in FLUX_BASELINE_L_M2_H:
        raise ValueError("technology_id must be TUF, LNF, or MEUF.")
    feed_volume = float(feed_volume_m3_year)
    hours = float(operating_hours_year)
    vcf = (
        _parameter_value("Concentration_Factor", "Retentate")
        if concentration_factor is None else float(concentration_factor)
    )
    price = (
        _parameter_value("Product_Price_Nominal", "Concentrate_Bulk")
        if price_EUR_L is None else float(price_EUR_L)
    )
    flux = FLUX_BASELINE_L_M2_H[technology] if flux_L_m2_h is None else float(flux_L_m2_h)
    if any(not math.isfinite(value) for value in (feed_volume, hours, vcf, price, flux)):
        raise ValueError("Feed volume, operating hours, VCF, price, and flux must be finite.")
    if feed_volume < 0.0 or price < 0.0 or hours <= 0.0 or vcf <= 1.0 or flux <= 0.0:
        raise ValueError("Operating hours and flux must be positive; concentration_factor must exceed 1.")
    feed_L_year = feed_volume * 1000.0
    product_L_year = feed_L_year / vcf
    permeate_L_year = feed_L_year - product_L_year
    area = permeate_L_year / hours / flux
    flux_basis = (
        "caller-supplied override"
        if flux_L_m2_h is not None
        else (
            "midpoint of user-supplied MEUF flux range"
            if technology == "MEUF"
            else "user-supplied nominal baseline flux"
        )
    )
    option_rows = {
        row["technology_id"]: row
        for row in _load_csv_rows("biostimulant_membrane_options.csv")
    }
    parameter_rows = {
        row["parameter_id"]: row
        for row in _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
    }
    option = option_rows[technology]
    fx = _usd_to_eur_rate()
    capex_low = area * float(option["membrane_price_min_EUR_m2"])
    capex_high = area * float(option["membrane_price_max_EUR_m2"])
    lifetime_low = float(parameter_rows["Membrane_Lifetime_Low"]["value"])
    lifetime_high = float(parameter_rows["Membrane_Lifetime_High"]["value"])
    return MembraneScreeningResult(
        technology_id=technology,
        feed_volume_m3_year=feed_volume,
        concentration_factor=vcf,
        product_volume_L_year=product_L_year,
        permeate_volume_L_year=permeate_L_year,
        flux_L_m2_h=flux,
        flux_basis=flux_basis,
        operating_hours_year=hours,
        membrane_area_m2=area,
        price_EUR_L=price,
        gross_revenue_EUR_year=product_L_year * price,
        membrane_module_capex_low_EUR=capex_low,
        membrane_module_capex_high_EUR=capex_high,
        annualized_replacement_low_EUR_year=capex_low / lifetime_high,
        annualized_replacement_high_EUR_year=capex_high / lifetime_low,
        fx_eur_per_usd=float(fx["eur_per_usd"]),
        fx_date=str(fx["fx_date"]),
        fx_source=str(fx["fx_source"]),
    )


def calculate_membrane_module_cost_range(
    technology_id: str,
    membrane_area_m2: float,
) -> dict[str, float | str]:
    """Return membrane CAPEX and replacement ranges in EUR.

    Provenance retains source quotations in the input register; calculated
    monetary outputs from this function are EUR only. The result is a module-
    only screen and excludes installation and the complete skid.
    """
    technology = str(technology_id).strip().upper()
    area = float(membrane_area_m2)
    if technology not in {"TUF", "LNF", "MEUF"}:
        raise ValueError("technology_id must be TUF, LNF, or MEUF.")
    if not math.isfinite(area) or area < 0.0:
        raise ValueError("membrane_area_m2 must be finite and non-negative.")
    option = next(
        row for row in _load_csv_rows("biostimulant_membrane_options.csv")
        if row["technology_id"] == technology
    )
    parameters = _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
    lifetimes = [
        float(row["value"])
        for row in parameters
        if row["parameter_id"] in {"Membrane_Lifetime_Low", "Membrane_Lifetime_High"}
    ]
    lifetime_min, lifetime_max = min(lifetimes), max(lifetimes)
    fx = _usd_to_eur_rate()
    capex_low = area * float(option["membrane_price_min_EUR_m2"])
    capex_high = area * float(option["membrane_price_max_EUR_m2"])
    return {
        "technology_id": technology,
        "area_m2": area,
        "module_capex_low_EUR": capex_low,
        "module_capex_high_EUR": capex_high,
        "module_replacement_low_EUR_year": capex_low / lifetime_max,
        "module_replacement_high_EUR_year": capex_high / lifetime_min,
        "lifetime_min_year": lifetime_min,
        "lifetime_max_year": lifetime_max,
        "currency_basis": "EUR; source quotation converted at dated ECB reference rate",
        "fx_eur_per_usd": fx["eur_per_usd"],
        "fx_date": fx["fx_date"],
        "fx_source": fx["fx_source"],
        "cost_boundary": "membrane module only; installation/skid/CIP/controls excluded",
    }


def _usd_to_eur_rate() -> dict[str, str | float]:
    """Load the dated USD-to-EUR reference-rate basis from screening inputs."""
    row = next(
        item for item in _load_csv_rows("biostimulant_membrane_gated_parameters.csv")
        if item["parameter_id"] == "FX_USD_EUR"
    )
    rate = float(row["value"])
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("FX_USD_EUR must be finite and positive.")
    return {
        "eur_per_usd": rate,
        "fx_date": row["source_date"],
        "fx_source": row["source_reference"],
    }


def split_component_flows(
    component_flows_kg_hr: dict[str, float],
    technology_id: str,
    *,
    flux_L_m2_h: float | None = None,
    component_retention_overrides: dict[str, float] | None = None,
    concentration_factor: float | None = None,
) -> dict[str, object]:
    """Apply the supplied class matrix and conserve unmapped pools separately.

    The supplied matrix covers only named classes. Any non-zero component not
    covered by those classes is returned in ``unresolved_kg_hr``. The mass
    split remains balanced, but downstream product composition, membrane area,
    and complete TEA/LCA require documented retentions or explicit overrides.
    Bulk water hold-up is derived from the target VCF so the retentate remains
    a liquid; it is not membrane rejection data.
    """

    technology = str(technology_id).strip().upper()
    if technology not in {"TUF", "LNF", "MEUF"}:
        raise ValueError("technology_id must be TUF, LNF, or MEUF.")
    flux = FLUX_BASELINE_L_M2_H[technology] if flux_L_m2_h is None else float(flux_L_m2_h)
    if not math.isfinite(flux) or flux <= 0.0:
        raise ValueError("flux_L_m2_h must be finite and positive.")
    vcf = (
        _parameter_value("Concentration_Factor", "Retentate")
        if concentration_factor is None else float(concentration_factor)
    )
    if not math.isfinite(vcf) or vcf <= 1.0:
        raise ValueError("concentration_factor must be finite and greater than one.")
    component_class = {}
    for ID in ("SolubleProtein", "SuspendedProtein", "PrecipitatedProtein", "HeatCoagulatedProtein", "DegradedProtein"):
        component_class[ID] = "crude_proteins"
    for ID in ("Peptides", "AminoAcids"):
        component_class[ID] = "peptides_amino_acids"
    for ID in ("Glucose", "Fructose", "Sucrose"):
        component_class[ID] = "sugars"
    for ID in ("MagnesiumIon", "CalciumIon", "Orthophosphate", "DissolvedPhosphorus", "OrganicPhosphorus"):
        component_class[ID] = "divalent_salts"
    for ID in ("PotassiumIon", "SodiumIon", "ChlorideIon", "Ammonium", "HydrogenIon", "HydroxideIon", "NitrateIon", "NitriteIon"):
        component_class[ID] = "monovalent_salts"
    for ID in ("Indole3AceticAcid", "ProteinBoundIAA", "Zeatin", "PeptideBoundZeatin", "ZeatinRiboside", "BoundZeatinRiboside"):
        component_class[ID] = "hormones"
    component_class["Water"] = "water"

    # Model chemical phase is explicit evidence about particulate state. The
    # screening rule below applies complete membrane retention to solid-phase
    # pools; it is flagged as an assumption because actual colloid capture,
    # solids loading, and fouling need feed-specific measurements.
    from Greenhub.chemicals import chemicals as model_chemicals
    solid_phase_ids = set()
    for ID in model_chemicals.IDs:
        if ID in component_class:
            continue
        try:
            chemical = model_chemicals[ID]
            phase = (
                getattr(chemical, "phase", None)
                or getattr(chemical, "phase_ref", None)
                or getattr(chemical, "locked_state", None)
            )
        except (KeyError, AttributeError):
            phase = None
        if phase == "s":
            component_class[ID] = "solid_particles"
            solid_phase_ids.add(ID)

    retention_by_class: dict[str, float] = {}
    for row in _load_csv_rows("biostimulant_membrane_component_retention.csv"):
        raw_retention = row[f"{technology}_retention_nominal"].strip()
        if raw_retention:
            retention_by_class[row["component_class"]] = float(raw_retention)
    # The supplied water row describes water as the permeate carrier, but a
    # liquid product at VCF=10 necessarily retains an aqueous heel. Treat the
    # VCF as the bulk-volume constraint, not as a molecular water rejection.
    retention_by_class["water"] = 1.0 / vcf
    overrides = dict(component_retention_overrides or {})
    for ID, fraction in overrides.items():
        value = float(fraction)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"Retention override for {ID} must be in [0, 1].")

    hormone_retention = {}
    with DATA_PATH.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            hormone_retention[row["solute_id"]] = {
                "free": float(row[f"retention_{technology}_free_fraction"]),
                "bound": float(row[f"retention_{technology}_bound_fraction"]),
            }
    hormone_component_to_solute = {
        "Indole3AceticAcid": ("IAA", "free"), "ProteinBoundIAA": ("IAA", "bound"),
        "Zeatin": ("Zeatin", "free"), "PeptideBoundZeatin": ("Zeatin", "bound"),
        "ZeatinRiboside": ("ZeatinRiboside", "free"), "BoundZeatinRiboside": ("ZeatinRiboside", "bound"),
    }

    retentate = {}
    permeate = {}
    unresolved = {}
    unmapped = []
    for ID, flow_value in component_flows_kg_hr.items():
        flow = float(flow_value)
        if not math.isfinite(flow) or flow < -1e-12:
            raise ValueError(f"Component flow for {ID} must be finite and non-negative.")
        flow = max(0.0, flow)
        if ID in overrides:
            fraction = overrides[ID]
        elif ID in hormone_component_to_solute:
            solute_id, state = hormone_component_to_solute[ID]
            if technology == "TUF" and state == "free":
                fraction = float(
                    calculate_film_retention(technology, solute_id, "free", flux)[
                        "predicted_retention_fraction"
                    ]
                )
            else:
                fraction = hormone_retention[solute_id][state]
        elif ID in component_class and component_class[ID] in retention_by_class:
            fraction = retention_by_class[component_class[ID]]
        elif flow > 1e-12:
            unmapped.append(ID)
            unresolved[ID] = flow
            continue
        else:
            fraction = 0.0
        retentate[ID] = flow * fraction
        permeate[ID] = flow - retentate[ID]
    retentate_by_class: dict[str, float] = {}
    permeate_by_class: dict[str, float] = {}
    for ID in retentate:
        category = component_class.get(ID, "explicit_overrides")
        retentate_by_class[category] = retentate_by_class.get(category, 0.0) + retentate[ID]
        permeate_by_class[category] = permeate_by_class.get(category, 0.0) + permeate[ID]
    screening_assumptions = (
        f"Bulk water hold-up is derived from target VCF={vcf:g} (fraction {1.0 / vcf:g}); this is not membrane water-rejection data.",
        (
            f"TUF free-hormone retention uses the sigma/Peclet equation at selected flux {flux:g} L/(m2 h); bound-payload retention uses the registered screening factors."
            if technology == "TUF"
            else "Hormone free/bound retention uses the registered state-specific screening factors for this membrane class."
        ),
    )
    if any(ID in solid_phase_ids and float(component_flows_kg_hr.get(ID, 0.0)) > 1e-12 for ID in component_flows_kg_hr):
        screening_assumptions += (
            "Unclassified model solid-phase components are assigned complete retention for membrane sieving; validate actual particulate/colloid capture and fouling with feed-specific tests.",
        )
    return {
        "technology_id": technology,
        "flux_L_m2_h": flux,
        "target_concentration_factor": vcf,
        "water_hold_up_fraction": retention_by_class["water"],
        "retentate_kg_hr": retentate,
        "permeate_kg_hr": permeate,
        "unresolved_kg_hr": unresolved,
        "retentate_by_class_kg_hr": retentate_by_class,
        "permeate_by_class_kg_hr": permeate_by_class,
        "unmapped_component_ids": tuple(sorted(unmapped)),
        "assumed_solid_phase_component_ids": tuple(
            sorted(ID for ID in solid_phase_ids if ID in component_flows_kg_hr and float(component_flows_kg_hr[ID]) > 1e-12)
        ),
        "screening_assumptions": screening_assumptions,
        "complete_mass_split": not unmapped,
        "mass_error_kg_hr": sum(float(value) for value in component_flows_kg_hr.values())
        - sum(retentate.values()) - sum(permeate.values()) - sum(unresolved.values()),
    }


def simulate_biostimulant_membrane_unit(
    component_flows_kg_hr: dict[str, float],
    technology_id: str,
    *,
    operating_hours_year: float,
    flux_L_m2_h: float | None = None,
    component_retention_overrides: dict[str, float] | None = None,
    concentration_factor: float | None = None,
) -> dict[str, object]:
    """Run the PR7 membrane unit in an isolated BioSTEAM flowsheet.

    The unit simulates mapped clarified-juice splits and carries unmapped
    components in a separate unresolved outlet. Pumping,
    cleaning, installed cost, and downstream conditioning are not represented.
    """
    import biosteam as bst
    from Greenhub.chemicals import chemicals as chemical_set, thermo
    from Greenhub.phase4_units import BiostimulantMembraneRecovery

    hours = float(operating_hours_year)
    if not math.isfinite(hours) or hours <= 0.0:
        raise ValueError("operating_hours_year must be finite and positive.")
    technology = str(technology_id).strip().upper()
    if technology not in FLUX_BASELINE_L_M2_H:
        raise ValueError("technology_id must be TUF, LNF, or MEUF.")
    from Greenhub.chemicals import chemicals as chemical_set
    unknown_ids = sorted(set(component_flows_kg_hr) - set(chemical_set.IDs))
    if unknown_ids:
        raise ValueError("Unknown GreenHub component IDs: " + ", ".join(unknown_ids))
    selected_flux = FLUX_BASELINE_L_M2_H[technology] if flux_L_m2_h is None else float(flux_L_m2_h)
    # Fail on missing mappings before constructing the temporary flowsheet.
    split_component_flows(
        component_flows_kg_hr, technology_id,
        flux_L_m2_h=selected_flux,
        component_retention_overrides=component_retention_overrides,
        concentration_factor=concentration_factor,
    )
    flowsheet_id = f"greenhub_pr7_screen_{uuid4().hex[:12]}"
    with _BIOSTEAM_SCREEN_LOCK:
        flowsheet = bst.Flowsheet(flowsheet_id)
        try:
            with flowsheet:
                feed = bst.Stream("pr7_juice_feed", thermo=thermo, units="kg/hr")
                for component_id, flow in component_flows_kg_hr.items():
                    feed.imass[component_id] = float(flow)
                analyte_feed = bst.Stream("pr7_analyte_screen_addition", thermo=thermo)
                retentate = bst.Stream("pr7_biostimulant_product", thermo=thermo)
                permeate = bst.Stream("pr7_membrane_permeate", thermo=thermo)
                unresolved = bst.Stream("pr7_membrane_unresolved", thermo=thermo)
                unit = BiostimulantMembraneRecovery(
                    ID="PR7_M101", ins=(feed, analyte_feed), outs=(retentate, permeate, unresolved),
                    technology_id=technology_id, flux_L_m2_h=selected_flux,
                    component_retention_overrides=component_retention_overrides,
                    concentration_factor=concentration_factor,
                )
                system = bst.main_flowsheet.create_system(
                    ID="pr7_membrane_screen_system",
                    ends=(retentate, permeate, unresolved),
                    operating_hours=hours,
                )
                system.simulate()
                return {
                    "status": (
                        "BioSTEAM unit simulated; component fate incomplete at unresolved outlet"
                        if not unit.component_split.get("complete_mass_split")
                        else "BioSTEAM unit simulated; screening scope only"
                    ),
                    "technology_id": unit.technology_id,
                    "operating_hours_year": hours,
                    "flux_L_m2_h": unit.flux_L_m2_h,
                    "membrane_area_m2": unit.design_results.get("Membrane area"),
                    "minimum_membrane_area_m2": unit.design_results.get("Minimum membrane area"),
                    "maximum_membrane_area_m2": unit.design_results.get("Maximum membrane area"),
                    "target_concentration_factor": unit.design_results.get("Target concentration factor"),
                    "actual_volume_concentration_factor": unit.design_results.get("Actual volume concentration factor"),
                    "feed_volume_m3_hr": unit.design_results.get("Feed volumetric flow"),
                    "product_volume_m3_hr": unit.design_results.get("Retentate volumetric flow"),
                    "product_stream_id": "pr7_biostimulant_product",
                    "permeate_stream_id": "pr7_membrane_permeate",
                    "unresolved_stream_id": "pr7_membrane_unresolved",
                    "unresolved_components_kg_hr": {
                        ID: float(unresolved.imass[ID]) for ID in chemical_set.IDs
                        if float(unresolved.imass[ID]) > 1e-12
                    },
                    "unresolved_mass_kg_hr": float(unresolved.F_mass),
                    "product_kg_hr": {
                        ID: float(retentate.imass[ID]) for ID in chemical_set.IDs
                        if float(retentate.imass[ID]) > 1e-12
                    },
                    "permeate_kg_hr": {
                        ID: float(permeate.imass[ID]) for ID in chemical_set.IDs
                        if float(permeate.imass[ID]) > 1e-12
                    },
                    "product_kg_year": float(retentate.F_mass) * hours,
                    "permeate_kg_year": float(permeate.F_mass) * hours,
                    "unresolved_kg_year": float(unresolved.F_mass) * hours,
                    "mass_closure_error_kg_hr": float(feed.F_mass - retentate.F_mass - permeate.F_mass - unresolved.F_mass),
                    "component_balance": unit.component_balance,
                    "warnings": tuple(unit.warnings) + (
                        "BioSTEAM unit excludes pumping, CIP, membrane replacement cost, and product conditioning.",
                    ),
                }
        finally:
            registry = bst.Flowsheet.flowsheet.__dict__
            if registry.get(flowsheet_id) is flowsheet and bst.main_flowsheet.get_flowsheet() is not flowsheet:
                registry.pop(flowsheet_id, None)


def calculate_component_split_balance(
    component_flows_kg_hr: dict[str, float],
    technology_id: str,
    *,
    flux_L_m2_h: float | None = None,
    component_retention_overrides: dict[str, float] | None = None,
    concentration_factor: float | None = None,
) -> dict[str, object]:
    """Return conservation and C/N/P/K diagnostics for the membrane split.

    Unknown-retention components are routed to an explicit unresolved outlet.
    Total mass and elemental closure are preserved, but product/permeate fate
    and membrane sizing remain incomplete until their retention is supplied.
    """

    from Greenhub.analytical import calculate_elemental_flows

    split = split_component_flows(
        component_flows_kg_hr,
        technology_id,
        flux_L_m2_h=flux_L_m2_h,
        component_retention_overrides=component_retention_overrides,
        concentration_factor=concentration_factor,
    )
    if not split["complete_mass_split"]:
        from Greenhub.component_metadata import COMPONENT_METADATA
        unresolved_flows = {
            ID: float(value) for ID, value in split["unresolved_kg_hr"].items()
            if abs(float(value)) > 1e-12
        }
        unresolved_elements = (
            calculate_elemental_flows(unresolved_flows)
            if set(unresolved_flows).issubset(COMPONENT_METADATA) else None
        )
        return {
            "complete": False,
            "unmapped_component_ids": split["unmapped_component_ids"],
            "assumed_solid_phase_component_ids": split["assumed_solid_phase_component_ids"],
            "screening_assumptions": split["screening_assumptions"],
            "feed_mass_kg_hr": sum(float(value) for value in component_flows_kg_hr.values()),
            "retentate_mass_kg_hr": sum(float(value) for value in split["retentate_kg_hr"].values()),
            "permeate_mass_kg_hr": sum(float(value) for value in split["permeate_kg_hr"].values()),
            "unresolved_mass_kg_hr": sum(unresolved_flows.values()),
            "mass_error_kg_hr": split["mass_error_kg_hr"],
            "unresolved_elements_kg_hr": unresolved_elements,
            "elements_kg_hr": None,
            "elemental_balance_status": "unresolved_outlet_balanced_but_membrane_fate_incomplete",
        }
    from Greenhub.component_metadata import COMPONENT_METADATA

    active_feed = {
        ID: float(value) for ID, value in component_flows_kg_hr.items()
        if abs(float(value)) > 1e-12
    }
    if not set(active_feed).issubset(COMPONENT_METADATA):
        return {
            "complete": True,
            "unmapped_component_ids": (),
            "assumed_solid_phase_component_ids": split["assumed_solid_phase_component_ids"],
            "screening_assumptions": split["screening_assumptions"],
            "feed_mass_kg_hr": sum(float(value) for value in component_flows_kg_hr.values()),
            "retentate_mass_kg_hr": sum(float(value) for value in split["retentate_kg_hr"].values()),
            "permeate_mass_kg_hr": sum(float(value) for value in split["permeate_kg_hr"].values()),
            "mass_error_kg_hr": split["mass_error_kg_hr"],
            "elements_kg_hr": None,
            "elemental_balance_status": "blocked_by_missing_component_metadata",
        }
    feed_elements = calculate_elemental_flows(active_feed)
    retentate_elements = calculate_elemental_flows({
        ID: float(value) for ID, value in split["retentate_kg_hr"].items() if abs(float(value)) > 1e-12
    })
    permeate_elements = calculate_elemental_flows({
        ID: float(value) for ID, value in split["permeate_kg_hr"].items() if abs(float(value)) > 1e-12
    })
    selected_elements = ("carbon", "nitrogen", "phosphorus", "potassium")
    return {
        "complete": True,
        "unmapped_component_ids": (),
        "assumed_solid_phase_component_ids": split["assumed_solid_phase_component_ids"],
        "screening_assumptions": split["screening_assumptions"],
        "feed_mass_kg_hr": sum(float(value) for value in component_flows_kg_hr.values()),
        "retentate_mass_kg_hr": sum(float(value) for value in split["retentate_kg_hr"].values()),
        "permeate_mass_kg_hr": sum(float(value) for value in split["permeate_kg_hr"].values()),
        "mass_error_kg_hr": split["mass_error_kg_hr"],
        "elemental_balance_status": "calculated",
        "elements_kg_hr": {
            element: {
                "feed": feed_elements[element],
                "retentate": retentate_elements[element],
                "permeate": permeate_elements[element],
                "closure_error": feed_elements[element] - retentate_elements[element] - permeate_elements[element],
            }
            for element in selected_elements
        },
    }

