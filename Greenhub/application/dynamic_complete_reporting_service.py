"""Opt-in reporting of the isolated complete BioSTEAM chain, never the empirical model."""
from __future__ import annotations

import calendar
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import PureWindowsPath
from threading import RLock

from .dynamic_complete_scenario import DynamicCompleteScenario, build_biomass_schedule, scenario_options
from Greenhub.dynamic_complete_proxy import DynamicCompleteProxyConfig, run_dynamic_complete_proxy_scenario_step
from Greenhub.dynamic_downstream_biosteam import build_dynamic_complete_biosteam_system
from Greenhub.dynamic_economic_environmental import FACTOR_DEFAULTS, analyze_dynamic_complete_report, resolve_factors
from Greenhub.time_grid import generate_time_grid

_REPORT_LOCK = RLock()
UNITS = {
    "mass": ("kg_per_hr", "tonnes_per_month", "tonnes_per_year", 1000),
    "gas": ("m3_per_hr", "m3_per_month", "m3_per_year", 1),
    "electricity": ("kWh_per_hr", "MWh_per_month", "MWh_per_year", 1000),
    "heat": ("MJ_per_hr", "GJ_per_month", "GJ_per_year", 1000),
}
METRIC_KINDS = {
    **{name: "mass" for name in ("feed_processed", "press_cake", "juice", "ad_feed", "dried_protein_product", "recovered_protein", "digestate", "ammonium_product", "struvite_candidate", "potassium_concentrate", "recovered_water", "nutrient_rich_solids", "ion_exchange_product", "final_residual_liquor", "methane_slip")},
    **{name: "gas" for name in ("raw_biogas", "methane", "biomethane", "biomethane_methane")},
    **{name: "electricity" for name in ("electricity_demand", "drying_electricity", "gas_upgrading_electricity", "resource_electricity", "chp_electricity_output")},
    **{name: "heat" for name in ("heat_demand", "ad_heat", "drying_heat", "gas_heat", "resource_heat", "chp_heat_output")},
}


def aggregate_rates(monthly_rates, *, year, annualize=False):
    """Rows contain time_label, operating_hours and rates; None propagates as unknown."""
    monthly, annual = [], {}
    hours = sum(row["operating_hours"] for row in monthly_rates)
    for row in monthly_rates:
        metrics = {}
        for name, kind in METRIC_KINDS.items():
            hourly_unit, monthly_unit, _, divisor = UNITS[kind]
            rate = row["rates"].get(name, 0.0)
            metrics[name] = {hourly_unit: rate, monthly_unit: None if rate is None else rate * row["operating_hours"] / divisor}
        monthly.append({**{k: v for k, v in row.items() if k != "rates"}, "metrics": metrics})
    for name, kind in METRIC_KINDS.items():
        hourly_unit, monthly_unit, annual_unit, divisor = UNITS[kind]
        values = [row["metrics"][name][monthly_unit] for row in monthly]
        total = None if any(v is None for v in values) else sum(values)
        annual[name] = {annual_unit: total, hourly_unit: None if total is None else total * divisor / hours if hours else 0.0}
    year_hours = (366 if calendar.isleap(year) else 365) * 24
    extrapolated = {name: {UNITS[kind][2]: None if annual[name][UNITS[kind][2]] is None else annual[name][UNITS[kind][2]] * year_hours / hours if hours else 0.0} for name, kind in METRIC_KINDS.items()} if annualize else None
    return {"monthly": monthly, "annual_summary": annual, "annualized_estimate": extrapolated,
            "basis": {"year": year, "modeled_operating_hours": hours, "calendar_year_hours": year_hours,
                      "annual_summary": "Sum of selected calendar periods; no off-season production added.",
                      "annualized_estimate": "Optional constant mean operating-rate extrapolation to full calendar year; not biomass-constrained."}}


def _rates(step):
    p, e = step.product_outputs, step.energy_summary
    preview = step.protein_result.protein_run.pathway_preview
    residual = step.resource_recovery[-1].outputs[-1] if step.resource_recovery else step.ad.outputs[-1]
    methane_slip = sum(s.components_kg_hr.get("Methane", 0.0) for s in step.gas_route.outputs if s.stream_id in ("reject_gas", "conditioning_residual"))
    rates = dict(feed_processed=step.config.basis_feed_kg_per_hr,
                 press_cake=p["press_cake_kg_hr"], dried_protein_product=p["dried_protein_product_kg_hr"],
                 recovered_protein=p["dried_product_protein_kg_hr"], digestate=p["digestate_kg_hr"],
                 juice=next(s.kg_per_kg_feed for s in preview.raw_press.outputs if s.stream_id == "brown_juice") * step.config.basis_feed_kg_per_hr,
                 ad_feed=step.ad.input_mass_kg_hr, final_residual_liquor=residual.mass_kg_hr,
                 methane=p["methane_m3_hr"], raw_biogas=step.ad.metrics["raw_biogas_m3_hr"],
                 biomethane=p.get("biomethane_m3_hr", 0.0),
                 biomethane_methane=p.get("biomethane_methane_kg_hr", 0.0) * 22.414 / 16.043,
                 methane_slip=methane_slip)
    for name, source in {"ammonium_product": "ammonium_product", "struvite_candidate": "struvite_product", "potassium_concentrate": "potassium_concentrate", "recovered_water": "recovered_water", "nutrient_rich_solids": "nutrient_rich_solids", "ion_exchange_product": "ammonium_ion_exchange_product"}.items():
        rates[name] = p.get(f"{source}_kg_hr", 0.0)
    for name, source, multiplier in (
        ("drying_electricity", "drying_electricity_kwh_hr", 1), ("gas_upgrading_electricity", "gas_electricity_kwh_hr", 1),
        ("resource_electricity", "resource_electricity_kwh_hr", 1), ("chp_electricity_output", "chp_electricity_output_kwh_hr", 1),
        ("drying_heat", "drying_heat_mj_hr", 1), ("ad_heat", "ad_heat_demand_kwh_hr", 3.6),
        ("gas_heat", "gas_heat_demand_kwh_hr", 3.6), ("resource_heat", "resource_heat_kwh_hr", 3.6), ("chp_heat_output", "chp_heat_output_kwh_hr", 3.6)):
        rates[name] = e[source] * multiplier
    rates["electricity_demand"] = sum(rates[k] for k in ("drying_electricity", "gas_upgrading_electricity", "resource_electricity"))
    rates["heat_demand"] = sum(rates[k] for k in ("drying_heat", "ad_heat", "gas_heat", "resource_heat"))
    return rates


def _record(name, value, unit, policy, status, source="", warning="Proxy assumption; not validated GreenHub performance.", source_id="", certainty="unvalidated proxy"):
    # Absolute paths never cross the reporting boundary.
    source = str(source).replace("\\", "/")
    if PureWindowsPath(source).is_absolute() or source.startswith("/"):
        source = PureWindowsPath(source).name
    return dict(name=name, value=value, unit=unit, policy_id=policy, source_status=status,
                certainty_class=certainty, source_file=source, source_id=source_id or name, warning=warning)


def _step_evidence(step):
    preview = step.protein_result.protein_run.pathway_preview
    records = [item.to_dict() for unit in (step.drying, step.ad, step.gas_route, *step.resource_recovery) for item in unit.evidence]
    # Retain complete closure registry, clearly distinguish selected unit evidence.
    used = {(r["policy_id"], r["name"]) for r in records}
    records += [{**v.to_dict(), "usage": "closure_registry"} for v in step.closure_policy.values if (v.policy_id, v.name) not in used]
    for field in preview.feedstock_bundle.fields:
        data = field.to_dict()
        prov = data["provenance"]
        records.append({**_record(data["canonical_field"], data["value"], data["unit"], data["selected_parameter_id"] or "FEED-FIELD",
                                  "direct_dataset" if data["certainty_class"] == "direct_literature" else "literature_proxy",
                                  prov.get("source_file", ""), data.get("assumption") or prov.get("limitation_note") or "Literature feedstock transferred to this scenario; not site validation.",
                                  data["selected_parameter_id"], data["certainty_class"]), "provenance": prov})
    # All upstream policy fields, their source evidence and engineering closures.
    for unit in (preview.raw_press, preview.first_centrifugation, preview.protein_extraction, preview.second_centrifugation, preview.drying, preview.biogas_mix_preparation):
        policy = unit.applied_policy
        prov = policy.get("provenance", {})
        classes = prov.get("field_evidence_class", {})
        for name, value in policy.items():
            if name in ("provenance", "warnings", "blockers", "policy_id", "activation_status", "status") or value is None:
                continue
            if isinstance(value, (float, int, dict)) and not isinstance(value, bool):
                certainty = classes.get(name, policy.get("proxy_class", "mixed upstream proxy"))
                status = "engineering_assumption" if "engineering" in certainty else "literature_proxy"
                records.append({**_record(name, value, "fraction" if "fraction" in name else "policy metadata", policy.get("policy_id", unit.unit_id), status,
                                          "Greenhub/dynamic_process.py", "; ".join(policy.get("warnings", ())) or "Upstream proxy policy; inspect source records.", certainty=certainty), "provenance": prov})
        for source in prov.get("evidence", []):
            records.append(_record(source.get("record_id", "source"), source.get("normalized_value", source.get("value")), source.get("normalized_unit") or source.get("unit", ""),
                                   policy.get("policy_id", unit.unit_id), "direct_dataset", source.get("source_file", ""),
                                   source.get("warning") or source.get("notes") or "Source observation transferred as a proxy.", source.get("source_id", "")))
    records.append(_record("feed_pool_policy", preview.feed_pools.provenance, "policy metadata", "FEED-POOL-PROXY", "literature_proxy", "Greenhub/dynamic_feedstock.py", "Whole-grass pooling and seasonal mapping are not site-validated."))
    closure = preview.provenance.get("proxy_closure_policy") or {}
    for name, value in closure.items():
        if isinstance(value, (int, float, dict)) and name != "provenance":
            records.append(_record(name, value, "fraction / policy metadata", closure["policy_id"], "engineering_assumption", "Greenhub/dynamic_process.py"))
    return records


def _deduplicate(records):
    import json
    unique = {}
    for record in records:
        key = json.dumps({k: v for k, v in record.items() if k != "time_label"}, sort_keys=True, default=str)
        if key not in unique:
            unique[key] = {**record, "time_labels": []}
            unique[key].pop("time_label", None)
        if record.get("time_label") and record["time_label"] not in unique[key]["time_labels"]:
            unique[key]["time_labels"].append(record["time_label"])
    return list(unique.values())


def build_scenario_summary(payload=None, analysis_factors=None):
    config = payload if isinstance(payload, DynamicCompleteScenario) else DynamicCompleteScenario.from_dict({} if payload is None else payload)
    resolve_factors(analysis_factors)  # Fail invalid factor inputs before running BioSTEAM.
    schedule = build_biomass_schedule(config)
    rows, records, validations = [], [], []
    warnings, blockers = Counter(), Counter()
    complete = config.allow_assumptions
    year = int(config.season_start[:4])
    for name, unit, value in (
        ("annual_available_biomass", "tonnes/year", config.annual_available_biomass_tonnes),
        ("annual_processed_target", "tonnes/year", config.annual_processed_biomass_tonnes),
        ("collection_refinery_fraction", "fraction", config.collection_refinery_fraction),
        ("season_start", "date", config.season_start), ("season_end", "date", config.season_end),
        ("peak_date", "date", config.peak_date), ("spread", "days", config.spread_days)):
        records.append(_record(name, value, unit, f"SCHEDULE-{name.upper()}", "user_input", source_id=f"scenario.{name}", warning="Scenario planning input; availability has not been measured."))
    records.append(_record("normal_supply_and_monthly_cap", "Gaussian integral / monthly ceiling / 24 hours per active day", "schedule policy", "SCHEDULE-CAP-001", "engineering_assumption", "Greenhub/application/dynamic_complete_scenario.py", "Fixed supply curve; no storage, downtime or capacity-dependent efficiency. Processing caps, not supply rescaling."))
    records.append(_record("unmodeled_utilities", 0, "kWh/h; MJ/h", "REPORT-UTILITIES-001", "engineering_assumption", "Greenhub/dynamic_complete_proxy.py", "Front-end and resource utility coverage is incomplete; zero means omitted demand, not measured zero."))
    if config.protein_recovery_fraction is not None:
        records.append(_record("protein_recovery_fraction", config.protein_recovery_fraction, "fraction", "SCENARIO-PROTEIN-RECOVERY", "user_input", warning="Explicit generic closure including heat method; not a measured extraction yield."))
    with _REPORT_LOCK:
        for supply in schedule["monthly"]:
            rates = {name: 0.0 for name in METRIC_KINDS}
            hours = supply["operating_hours"] if supply["processed_biomass_tonnes"] > 1e-12 else 0
            if hours:
                core = DynamicCompleteProxyConfig(
                    start_date=f"{year}-01-01", end_date=f"{year}-12-31", basis_feed_kg_per_hr=supply["basis_feed_kg_per_hr"],
                    protein_method="generic" if config.protein_method == "heat" and not config.allow_assumptions else config.protein_method,
                    drying_method=config.drying_method, upgrading_method=config.gas_route,
                    resource_recovery_methods=tuple(m for m in scenario_options()["resource_recovery_methods"] if m in config.resource_recovery_methods),
                    drying_target_moisture_fraction=config.target_product_moisture, allow_assumptions=config.allow_assumptions,
                    generic_protein_recovery_fraction=config.protein_recovery_fraction,
                    generic_protein_policy_id="SCENARIO-PROTEIN-RECOVERY" if config.protein_recovery_fraction is not None else "",
                    generic_protein_provenance_note="Explicit dashboard recovery closure" if config.protein_recovery_fraction is not None else "")
                step = run_dynamic_complete_proxy_scenario_step(core, supply["time_label"])
                warnings.update(step.warnings)
                warnings.update(step.protein_result.protein_run.pathway_preview.warnings)
                blockers.update(step.blockers)
                records.extend({**record, "time_label": supply["time_label"]} for record in _step_evidence(step))
                if config.allow_assumptions:
                    system = build_dynamic_complete_biosteam_system(step)
                    valid = system.can_drive_complete_biosteam_proxy
                    validations.append({"time_label": supply["time_label"], "parity_passed": system.validation.closes,
                                        "empirical_flowsheet_unchanged": system.validation.empirical_flowsheet_unchanged,
                                        "press_cake_boundary_valid": system.validation.press_cake_boundary_valid})
                    if not valid:
                        blockers.update(["biosteam_parity_or_proxy_readiness_failed"])
                    warnings.update(system.validation.warnings)
                else:
                    valid = False
                complete = complete and valid
                rates = _rates(step) if valid else {name: None for name in METRIC_KINDS}
                rates["feed_processed"] = supply["basis_feed_kg_per_hr"]
            rows.append({**supply, "operating_hours": hours, "rates": rates})
    if not config.allow_assumptions:
        blockers.update(["strict_mode_requires_validated_upstream_and_downstream_closures"])
    if schedule["unmet_target_tonnes"] > 1e-6:
        warnings.update(["Selected active months or hourly capacity cannot meet the requested processing target."])
    warnings.update(["Gross utility totals exclude unmodeled front-end and resource recovery demands.",
                     "Protein extraction heat and reagent demand are not included, including the generic closure of heat extraction.",
                     "Product candidates are not quality-certified; intermediate digestate must not be added to final recovery outputs."])
    evidence = _deduplicate(records)
    counts = dict(Counter(r["source_status"] for r in evidence))
    report = {**aggregate_rates(rows, year=year, annualize=config.annualize), "schema_version": "dynamic-complete-reporting-1.0",
              "scenario": config.to_dict(), "selected_methods": {name: getattr(config, name) for name in ("protein_method", "drying_method", "gas_route", "resource_recovery_methods")},
              "biomass_schedule": schedule, "assumptions": evidence, "assumption_counts": counts,
              "assumptions_count": len(evidence), "warning_counts": dict(warnings), "warnings_count": sum(warnings.values()),
              "blocker_counts": dict(blockers), "blockers_count": sum(blockers.values()),
              "top_assumptions": ["SCHEDULE-CAP-001", "engineering_proxy_closure_v1", "BMP_DFOS_VS", "ASSUMP-NUT-003", "ASSUMP-NUT-004", "REPORT-UTILITIES-001"],
              "readiness": {"status": "Proxy-complete model" if complete else "Blocked proxy scenario", "can_drive_complete_biosteam_proxy": complete,
                            "can_drive_simulation": False, "validated_simulation_ready": False, "assumptions_enabled": config.allow_assumptions},
              "biosteam_checks": validations, "press_cake_boundary": "external_system_output", "artifact_names": [],
              "chart_contract": {name: {"kind": kind, "hourly_unit": UNITS[kind][0], "monthly_unit": UNITS[kind][1], "annual_unit": UNITS[kind][2]} for name, kind in METRIC_KINDS.items()}}
    report["analysis"] = analyze_dynamic_complete_report(report, analysis_factors)
    report["analysis_assumptions_count"] = len(report["analysis"]["assumptions"])
    return report


def summarize_biosteam_grid(grid, *, annualize=False):
    """Report an existing May–November (or other monthly) grid without extending it."""
    if grid.config.time_step != "monthly":
        raise ValueError("Complete dashboard reporting requires a monthly grid.")
    time_grid = {s.label: s for s in generate_time_grid(grid.config.start_date, grid.config.end_date, "monthly")}
    rows, records = [], []
    for result in grid.steps:
        step = result.proxy_step
        rates = _rates(step) if result.can_drive_complete_biosteam_proxy else {name: None for name in METRIC_KINDS}
        rates["feed_processed"] = step.config.basis_feed_kg_per_hr
        rows.append(dict(time_label=step.time_label, operating_hours=time_grid[step.time_label].duration_hours, rates=rates))
        records.extend({**r, "time_label": step.time_label} for r in _step_evidence(step))
    return {**aggregate_rates(rows, year=int(grid.config.start_date[:4]), annualize=annualize),
            "assumptions": _deduplicate(records), "warning_counts": dict(grid.warning_counts), "blocker_counts": dict(grid.blocker_counts),
            "readiness": {"can_drive_complete_biosteam_proxy": grid.all_steps_complete_biosteam_ready,
                          "can_drive_simulation": False, "validated_simulation_ready": False}}


@lru_cache(maxsize=1)
def _default_summary():
    return build_scenario_summary()


def default_summary():
    return deepcopy(_default_summary())


def reporting_options():
    return {**scenario_options(), "analysis_factors": {name: {"value": value, "unit": unit, "source_status": "engineering_assumption"} for name, (value, unit) in FACTOR_DEFAULTS.items()}}
