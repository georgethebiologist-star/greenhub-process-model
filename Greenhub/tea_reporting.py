"""Reproducible scenario sampling and JSON/CSV screening-TEA KPI reports."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import random
from typing import Mapping, Sequence

from Greenhub.application.contracts import ScenarioSelection
from Greenhub.application.dynamic_complete_scenario import (
    DRYING_METHODS,
    GAS_ROUTES,
    PROTEIN_METHODS,
    RESOURCE_METHODS,
    DynamicCompleteScenario,
)
from Greenhub.application.scenario_service import ScenarioService


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = PACKAGE_ROOT / "results"
DEFAULT_DOCS_DIR = PACKAGE_ROOT.parent / "docs"

KPI_COLUMNS = (
    "scenario_label",
    "simulation_type",
    "selected_routes",
    "annual_feed_tonnes",
    "total_installed_capex_eur",
    "partial_direct_capex_eur",
    "capex_status",
    "opex_status",
    "profit_status",
    "annual_opex_eur",
    "annual_revenue_eur",
    "annual_profit_eur",
    "npv_eur",
    "irr",
    "simple_payback_years",
    "discounted_payback_years",
    "cost_per_tonne_feed_eur",
    "revenue_status",
    "missing_input_count",
    "warning_count",
    "confidence_summary",
)


def sample_valid_empirical_scenarios(
    count: int = 4,
    *,
    seed: int = 20260929,
) -> tuple[dict[str, object], ...]:
    """Select reproducible combinations only from active empirical scenarios."""

    if count < 0:
        raise ValueError("count must be non-negative.")
    service = ScenarioService()
    available = service.list_scenarios()
    pools: dict[str, tuple[str, ...]] = {}
    for group, rows in available.items():
        pools[group] = tuple(
            str(row["scenario_id"])
            for row in rows
            if row.get("active", True) is not False
        )
    rng = random.Random(seed)
    cases: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    attempts = 0
    while len(cases) < count and attempts < max(100, count * 50):
        attempts += 1
        selection = ScenarioSelection(
            feed_preparation=rng.choice(pools["feed_preparation"]),
            protein_recovery=rng.choice(pools["protein_recovery"]),
            anaerobic_digestion=rng.choice(pools["anaerobic_digestion"]),
            biogas_upgrading=rng.choice(pools["biogas_upgrading"]),
            nutrient_recovery=rng.choice(pools["nutrient_recovery"]),
            process_order=rng.choice(("A", "B", "C", "D")),
        )
        key = (*selection.scenario_ids, selection.process_order)
        if key in seen or any(
            issue.blocking for issue in service.validate_scenario_chain(selection)
        ):
            continue
        seen.add(key)
        cases.append(
            {
                "scenario_label": f"empirical_seed_{seed}_{len(cases) + 1}",
                "simulation_type": "empirical",
                "selected_routes": list(selection.scenario_ids),
                "process_order": selection.process_order,
                "selection": selection,
                "project_assumptions": {},
                "random_seed": seed,
            }
        )
    if len(cases) != count:
        raise RuntimeError(f"Could not select {count} unique active empirical scenarios.")
    return tuple(cases)


def sample_valid_dynamic_scenarios(
    count: int = 4,
    *,
    seed: int = 20260929,
) -> tuple[dict[str, object], ...]:
    """Build reproducible, validation-safe dynamic scenario configurations."""

    if count < 0:
        raise ValueError("count must be non-negative.")
    rng = random.Random(seed)
    cases: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    attempts = 0
    while len(cases) < count and attempts < max(100, count * 50):
        attempts += 1
        protein = rng.choice(PROTEIN_METHODS)
        resource_count = rng.randrange(len(RESOURCE_METHODS) + 1)
        resources = tuple(sorted(rng.sample(RESOURCE_METHODS, resource_count)))
        config = DynamicCompleteScenario(
            protein_method=protein,
            protein_recovery_fraction=0.34 if protein in {"heat", "generic"} else None,
            drying_method=rng.choice(DRYING_METHODS),
            gas_route=rng.choice(GAS_ROUTES),
            resource_recovery_methods=resources,
        )
        key = (
            config.protein_method,
            config.drying_method,
            config.gas_route,
            config.resource_recovery_methods,
        )
        if key in seen:
            continue
        seen.add(key)
        cases.append(
            {
                "scenario_label": f"dynamic_seed_{seed}_{len(cases) + 1}",
                "simulation_type": "dynamic",
                "selected_routes": [
                    config.protein_method,
                    config.drying_method,
                    config.gas_route,
                    *config.resource_recovery_methods,
                ],
                "config": config,
                "project_assumptions": {
                    "protein_recovery_fraction": config.protein_recovery_fraction,
                    "allow_assumptions": config.allow_assumptions,
                },
                "random_seed": seed,
            }
        )
    if len(cases) != count:
        raise RuntimeError(f"Could not select {count} unique dynamic scenarios.")
    return tuple(cases)


def build_tea_scenario_kpi_table(
    cases: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    """Flatten evaluated TEA reports into the requested JSON-safe KPI table."""

    rows: list[dict[str, object]] = []
    for case in cases:
        report = case.get("tea_report") or case.get("report")
        if report is None:
            raise ValueError("Each evaluated case requires tea_report or report.")
        payload = report.to_dict() if hasattr(report, "to_dict") else dict(report)
        route = payload["route_summary"]
        totals = payload["totals"]
        finance = payload.get("financial_kpis", {})
        selected = case.get("selected_routes")
        if selected is None:
            selected = route.get("scenario_ids") or _flatten_routes(
                (route.get("selected_methods") or {}).values()
            )
        rows.append(
            {
                "scenario_label": str(case["scenario_label"]),
                "simulation_type": str(case.get("simulation_type") or route.get("model_type")),
                "selected_routes": list(selected or ()),
                "annual_feed_tonnes": _divide(route.get("annual_throughput_kg"), 1000.0),
                "total_installed_capex_eur": totals.get("total_installed_capex_eur"),
                "partial_direct_capex_eur": totals.get("partial_direct_capex_eur"),
                "capex_status": totals.get("capex_status"),
                "opex_status": totals.get("opex_status"),
                "profit_status": totals.get("profit_status"),
                "annual_opex_eur": totals.get("annual_opex_eur"),
                "annual_revenue_eur": totals.get("annual_revenue_eur"),
                "annual_profit_eur": finance.get("annual_gross_profit_eur"),
                "npv_eur": finance.get("npv_eur"),
                "irr": finance.get("irr"),
                "simple_payback_years": finance.get("simple_payback_years"),
                "discounted_payback_years": finance.get("discounted_payback_years"),
                "cost_per_tonne_feed_eur": finance.get("cost_per_tonne_wet_feed_eur"),
                "revenue_status": totals.get("revenue_status"),
                "missing_input_count": len(payload.get("missing_inputs", ())),
                "warning_count": len(payload.get("warnings", ())),
                "confidence_summary": dict(payload.get("confidence_summary", {})),
            }
        )
    return tuple(rows)


def evaluate_tea_scenario_cases(
    cases: Sequence[Mapping[str, object]],
    *,
    empirical_runner,
    dynamic_runner,
    project_basis_by_label: Mapping[str, object] | None = None,
    financial_assumptions_by_label: Mapping[str, object] | None = None,
) -> tuple[dict[str, object], ...]:
    """Run supplied valid cases, then apply TEA strictly after each result exists.

    Callbacks keep this helper independent of repository/run-directory choices.
    They receive the case mapping and must return a completed empirical or
    dynamic result. Project and financial assumptions are recorded per label.
    """

    from Greenhub.application.tea_service import calculate_dynamic_tea, calculate_empirical_tea

    bases = project_basis_by_label or {}
    finances = financial_assumptions_by_label or {}
    evaluated: list[dict[str, object]] = []
    for case in cases:
        label = str(case["scenario_label"])
        simulation_type = str(case["simulation_type"])
        if simulation_type == "empirical":
            result = empirical_runner(case)
            tea = calculate_empirical_tea(
                result,
                project_basis=bases.get(label),
                financial_assumptions=finances.get(label),
            )
        elif simulation_type == "dynamic":
            result = dynamic_runner(case)
            tea = calculate_dynamic_tea(
                result,
                project_basis=bases.get(label),
                financial_assumptions=finances.get(label),
            )
        else:
            raise ValueError(f"Unsupported simulation_type '{simulation_type}'.")
        evaluated.append(
            {
                **dict(case),
                "tea_report": tea,
                "project_assumptions": _json_safe_assumptions(bases.get(label)),
                "financial_assumptions": _json_safe_assumptions(finances.get(label)),
            }
        )
    return tuple(evaluated)


def write_tea_scenario_kpi_reports(
    rows: Sequence[Mapping[str, object]],
    *,
    results_dir: str | Path | None = None,
    docs_dir: str | Path | None = None,
) -> dict[str, Path]:
    """Write stable CSV, JSON, and Markdown screening-report artifacts."""

    result_root = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    doc_root = Path(docs_dir) if docs_dir is not None else DEFAULT_DOCS_DIR
    result_root.mkdir(parents=True, exist_ok=True)
    doc_root.mkdir(parents=True, exist_ok=True)
    csv_path = result_root / "tea_scenario_kpis.csv"
    json_path = result_root / "tea_scenario_kpis.json"
    markdown_path = doc_root / "tea_screening_results.md"
    serializable = [dict(row) for row in rows]
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=KPI_COLUMNS)
        writer.writeheader()
        for row in serializable:
            writer.writerow(
                {
                    **row,
                    "selected_routes": json.dumps(row["selected_routes"], separators=(",", ":")),
                    "confidence_summary": json.dumps(
                        row["confidence_summary"], sort_keys=True, separators=(",", ":")
                    ),
                }
            )
    json_path.write_text(json.dumps(serializable, indent=2, allow_nan=False), encoding="utf-8")
    markdown_path.write_text(_markdown_report(serializable), encoding="utf-8")
    return {"csv": csv_path, "json": json_path, "markdown": markdown_path}


def _markdown_report(rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "# GreenHub screening TEA scenario results",
        "",
        "These post-simulation results are screening estimates, not investment-grade TEA. "
        "Blank investment KPIs indicate explicit missing inputs; no capacity, price, or operating basis was invented.",
        "",
        "| Scenario | Type | Routes | CAPEX (EUR) | OPEX/y (EUR) | Revenue/y (EUR) | NPV (EUR) | Revenue status | Missing |",
        "|---|---|---|---:|---:|---:|---:|---|---:|",
    ]
    for row in rows:
        routes = ", ".join(str(item) for item in row["selected_routes"])
        lines.append(
            "| {scenario_label} | {simulation_type} | {routes} | {capex} | {opex} | {revenue} | {npv} | {status} | {missing} |".format(
                scenario_label=row["scenario_label"],
                simulation_type=row["simulation_type"],
                routes=routes,
                capex=_format(row["total_installed_capex_eur"]),
                opex=_format(row["annual_opex_eur"]),
                revenue=_format(row["annual_revenue_eur"]),
                npv=_format(row["npv_eur"]),
                status=row["revenue_status"],
                missing=row["missing_input_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "NPV, IRR, and payback are calculated only when installed CAPEX, annual OPEX, required product revenue, project lifetime, and discount rate are complete. Revenue remains incomplete when a simulated saleable product lacks a traceable register or user-supplied price.",
            "",
        ]
    )
    return "\n".join(lines)


def _divide(value: object, divisor: float) -> float | None:
    return None if value is None else float(value) / divisor


def _flatten_routes(values) -> list[str]:
    routes: list[str] = []
    for value in values:
        if isinstance(value, (tuple, list)):
            routes.extend(str(item) for item in value if item)
        elif value:
            routes.append(str(value))
    return routes


def _format(value: object) -> str:
    return "" if value is None else f"{float(value):.6g}"


def _json_safe_assumptions(value: object) -> object:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return str(value)


__all__ = (
    "KPI_COLUMNS",
    "build_tea_scenario_kpi_table",
    "evaluate_tea_scenario_cases",
    "sample_valid_dynamic_scenarios",
    "sample_valid_empirical_scenarios",
    "write_tea_scenario_kpi_reports",
)
