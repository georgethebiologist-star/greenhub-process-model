"""Illustrative operating economics and emissions, separate from process calculations.

No defaults below are sourced market prices or validated emission factors.
Positive emissions are burdens; displacement credits are negative.
"""
from __future__ import annotations

import math

# name: (illustrative value, unit). Explicitly adjustable through scenario-summary.
FACTOR_DEFAULTS = {
    "protein_price": (2.0, "EUR/kg dried product"),
    "biomethane_price": (0.8, "EUR/m3 product gas"),
    "fertilizer_price": (0.1, "EUR/kg candidate product"),
    "press_cake_credit": (0.03, "EUR/kg external press cake"),
    "electricity_price": (0.18, "EUR/kWh"),
    "heat_price": (16.0, "EUR/GJ"),
    "reagent_cost": (0.0, "EUR/tonne feed"),
    "other_utility_cost": (0.0, "EUR/tonne feed"),
    "natural_gas_displacement": (2.0, "kg CO2e/m3 recovered CH4"),
    "electricity_emissions": (0.4, "kg CO2e/kWh"),
    "heat_emissions": (56.0, "kg CO2e/GJ"),
    "fertilizer_displacement": (0.5, "kg CO2e/kg candidate product"),
    "methane_gwp": (28.0, "kg CO2e/kg CH4"),
    "unrecovered_methane_emitted_fraction": (1.0, "fraction"),
}


def resolve_factors(overrides=None):
    overrides = {} if overrides is None else overrides
    if not isinstance(overrides, dict) or set(overrides) - set(FACTOR_DEFAULTS):
        raise ValueError("analysis_factors must contain only supported factor names from /options.")
    values, evidence = {}, []
    for name, (default, unit) in FACTOR_DEFAULTS.items():
        value = overrides.get(name, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Analysis factor {name} must be a finite non-negative number.")
        if name.endswith("_fraction") and value > 1:
            raise ValueError(f"{name} must be in [0, 1].")
        values[name] = value
        evidence.append(dict(name=name, value=value, unit=unit, policy_id=f"ANALYSIS-{name.upper()}",
                             source_status="user_input" if name in overrides else "engineering_assumption",
                             certainty_class="unvalidated illustrative scenario factor", source_file="",
                             source_id=f"analysis_factors.{name}",
                             warning="No external source attached; illustrative placeholder, not a market quote or validated LCA factor."))
    return values, evidence


def analyze_dynamic_complete_report(report, overrides=None):
    factors, evidence = resolve_factors(overrides)
    warnings = [
        "Preliminary operating proxy only: excludes CAPEX, labor, maintenance, logistics, financing and taxes.",
        "Not a validated TEA or LCA; excludes cultivation, transport, equipment, reagent production and land-use effects.",
        "Fertilizer candidate wet mass is credited illustratively; nutrient content, quality, marketability and displacement are unvalidated.",
        "CHP production is shown separately; no assumed self-consumption or export credits are netted from gross utility demand.",
        "Zero reagent/other utility prices mean omitted costs, not free inputs; front-end and recovery utilities remain incomplete.",
        "Methane slip uses tracked reject/conditioning methane only; AD fugitives and CHP exhaust methane are not modeled.",
    ]
    if report["scenario"].get("drying_method") == "mass_only":
        warnings.append("Mass-only drying omits dryer utilities; cost and emissions are incomplete.")
    if not report["readiness"]["can_drive_complete_biosteam_proxy"] or not report["scenario"]["allow_assumptions"]:
        return dict(proxy_analysis_ready=False, validated_tea_ready=False, validated_lca_ready=False,
                    economic=None, environmental=None, assumptions=evidence,
                    warnings=warnings + ["Blocked process scenario: analysis totals withheld; factors shown for inspection only."])
    annual = report["annual_summary"]
    def qty(key, unit):
        return annual[key][unit]
    def kg(key):
        return qty(key, "tonnes_per_year") * 1000
    feed = qty("feed_processed", "tonnes_per_year")
    protein, gas = kg("dried_protein_product"), qty("biomethane", "m3_per_year")
    fertilizer = sum(kg(key) for key in ("ammonium_product", "struvite_candidate", "potassium_concentrate"))
    electricity = qty("electricity_demand", "MWh_per_year") * 1000
    heat = qty("heat_demand", "GJ_per_year")
    revenue = {
        "protein_product": protein * factors["protein_price"],
        "biomethane": gas * factors["biomethane_price"],
        "fertilizer_candidates": fertilizer * factors["fertilizer_price"],
        "external_press_cake": kg("press_cake") * factors["press_cake_credit"],
    }
    costs = {"electricity": electricity * factors["electricity_price"], "heat": heat * factors["heat_price"],
             "reagents": feed * factors["reagent_cost"], "other_utilities": feed * factors["other_utility_cost"]}
    total_cost, total_revenue = sum(costs.values()), sum(revenue.values())
    def divide(numerator, denominator):
        return numerator / denominator if denominator else None
    # Credit methane content, not CO2-containing product volume.
    emissions = {
        "avoided_natural_gas": -qty("biomethane_methane", "m3_per_year") * factors["natural_gas_displacement"],
        "electricity": electricity * factors["electricity_emissions"],
        "heat": heat * factors["heat_emissions"],
        "fertilizer_displacement": -fertilizer * factors["fertilizer_displacement"],
        "methane_slip": kg("methane_slip") * factors["unrecovered_methane_emitted_fraction"] * factors["methane_gwp"],
    }
    net = sum(emissions.values())
    return dict(proxy_analysis_ready=True, validated_tea_ready=False, validated_lca_ready=False,
                economic=dict(revenue_eur_per_year=revenue, costs_eur_per_year=costs,
                              total_revenue_eur_per_year=total_revenue, total_cost_eur_per_year=total_cost,
                              net_operating_margin_eur_per_year=total_revenue - total_cost,
                              cost_eur_per_tonne_feed=divide(total_cost, feed),
                              cost_eur_per_kg_dried_protein=divide(total_cost, protein),
                              cost_eur_per_m3_biomethane=divide(total_cost, gas),
                              allocation_note="Each intensity divides the same gross included cost by one output; no coproduct allocation."),
                environmental=dict(contributions_kg_co2e_per_year=emissions, net_kg_co2e_per_year=net,
                                   kg_co2e_per_tonne_feed=divide(net, feed), kg_co2e_per_kg_dried_protein=divide(net, protein)),
                assumptions=evidence, warnings=warnings)
