"""Summarize global input associations across every archived GreenHub endpoint.

This is a read-only postprocessor for the endpoint-report gzip shards created
by ``run_greenhub_sensitivity.py``. It dynamically discovers endpoint paths in
each saved report instead of maintaining a fixed list of outputs.

Example:
    .venv/Scripts/python scripts/analyze_greenhub_endpoint_sensitivity.py \
      results/sensitivity_analysis/seasonal_mc_monthly_20261106
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Greenhub.sensitivity_archive import iter_report_records, report_archives


INPUTS = {
    "juice_yield_kg_per_kg_wet_feed": "Juice fraction (kg/kg wet feed)",
    "protein_g_kg_dm": "Crude protein (g/kg DM)",
    "cellulose_fraction_dm": "Cellulose (fraction DM)",
    "hemicellulose_fraction_dm": "Hemicellulose (fraction DM)",
    "nitrogen_g_kg_dm": "Nitrogen (g/kg DM)",
    "phosphorus_g_kg_dm": "Phosphorus (g/kg DM)",
    "potassium_g_kg_dm": "Potassium (g/kg DM)",
    "price_dry_protein_product": "Protein price (€/kg)",
    "price_press_cake": "Press cake price (€/kg)",
    "price_ammonium_product": "Ammonium price (€/kg)",
    "price_phosphorus_product": "Phosphorus product price (€/kg)",
    "price_potassium_concentrate": "Potassium price (€/kg)",
    "price_nutrient_rich_solids": "Nutrient solids price (€/kg)",
    "price_biomethane": "Biomethane price (€/m³)",
    "capex_grant_fraction": "CAPEX grant fraction",
    "biomethane_bonus_eur_per_m3": "Biomethane support (€/Nm³)",
    "grass_utilization_bonus_eur_per_t_feed": "Grass-use bonus (€/t feed)",
}

PALETTE = {"ink": "#0b3b3e", "green": "#3f9456", "blue": "#6b9bd2",
           "rose": "#cf6a9b", "gold": "#d5a61a", "orange": "#b97635"}


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def flatten_inputs(summary: dict[str, Any], grass_bonus: float | None) -> dict[str, float]:
    nested = summary.get("varta_nutrients_g_kg_dm") or {}
    values = {
        "juice_yield_kg_per_kg_wet_feed": summary.get("juice_yield_kg_per_kg_wet_feed"),
        "protein_g_kg_dm": summary.get("protein_g_kg_dm"),
        "cellulose_fraction_dm": summary.get("cellulose_fraction_dm"),
        "hemicellulose_fraction_dm": summary.get("hemicellulose_fraction_dm"),
        "nitrogen_g_kg_dm": nested.get("nitrogen_g_kg_dm"),
        "phosphorus_g_kg_dm": nested.get("phosphorus_g_kg_dm"),
        "potassium_g_kg_dm": nested.get("potassium_g_kg_dm"),
        "capex_grant_fraction": summary.get("capex_grant_fraction"),
        "biomethane_bonus_eur_per_m3": summary.get("biomethane_bonus_eur_per_m3"),
        "grass_utilization_bonus_eur_per_t_feed": grass_bonus,
    }
    values.update({key: summary.get(key) for key in INPUTS if key.startswith("price_")})
    return {key: number for key, raw in values.items() if (number := finite_number(raw)) is not None}


def report_branch(path: str) -> str:
    return path.split(".", 1)[0].split("[", 1)[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_folder", type=Path)
    args = parser.parse_args()
    root = args.run_folder.resolve()
    archives = report_archives(root)
    if not archives:
        parser.error(f"Missing full report archive in: {root}")
    try:
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from scipy.stats import spearmanr
    except ImportError as exc:
        raise SystemExit(f"numpy, scipy, and matplotlib are required: {exc}")

    input_values: dict[str, list[float | None]] = defaultdict(list)
    endpoint_values: dict[str, list[float | None]] = defaultdict(list)
    records = 0
    for rec in iter_report_records(root):
        summary = rec.get("summary") or {}
        flat_inputs = flatten_inputs(summary, None)
        for key in INPUTS:
            input_values[key].append(flat_inputs.get(key))
        numeric = {key: finite_number(value)
                   for key, value in (rec.get("numeric_endpoints") or {}).items()}
        # Keep index alignment even if routes expose different endpoint
        # paths. Missing values remain None; they are never imputed.
        for key in endpoint_values:
            if key not in numeric:
                endpoint_values[key].append(None)
        for key, value in numeric.items():
            if key not in endpoint_values:
                endpoint_values[key] = [None] * records
            endpoint_values[key].append(value)
        records += 1

    if records < 3:
        raise SystemExit(f"Need at least three saved cases; found {records}.")

    # Align every dynamic endpoint and sampled input by archived record index.
    # Missing endpoints are retained as missing, never imputed as zero.
    correlation_rows: list[dict[str, Any]] = []
    endpoint_peak: dict[str, float] = {}
    for endpoint, ys in endpoint_values.items():
        best = 0.0
        for input_key, xs in input_values.items():
            pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
            if len(pairs) < 3 or len({x for x, _ in pairs}) < 2 or len({y for _, y in pairs}) < 2:
                continue
            rho = float(spearmanr([x for x, _ in pairs], [y for _, y in pairs]).statistic)
            if not math.isfinite(rho):
                continue
            best = max(best, abs(rho))
            correlation_rows.append({
                "endpoint": endpoint,
                "report_section": report_branch(endpoint),
                "input": input_key,
                "input_label": INPUTS[input_key],
                "spearman_rho": rho,
                "absolute_rho": abs(rho),
                "paired_cases": len(pairs),
                "interpretation": "Rank association in the specified screening design; not causal and not a calibrated probability model.",
            })
        endpoint_peak[endpoint] = best

    out = root / "global_endpoint_sensitivity.csv"
    fields = ["endpoint", "report_section", "input", "input_label", "spearman_rho",
              "absolute_rho", "paired_cases", "interpretation"]
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(correlation_rows, key=lambda row: (row["endpoint"], row["absolute_rho"]), reverse=False))

    # Heatmap for the most responsive distinct endpoints, using all supported
    # input variables; complete data remain available in the CSV.
    matrix: dict[str, dict[str, float]] = defaultdict(dict)
    for row in correlation_rows:
        matrix[row["endpoint"]][row["input"]] = row["spearman_rho"]
    # The full correlation table is exhaustive. The heatmap uses interpretable
    # report-level KPIs only, avoiding duplicate aliases and time-step arrays.
    def figure_eligible(path: str) -> bool:
        lower = path.lower()
        if "residual" in lower or any(token in lower for token in (
                "state_outputs", "cash_flow", "cash flow", "timeline", "monthly",
                "weekly", "daily", "by_unit", "inventory[", "factors[", "source_traceability")):
            return False
        core_tea = {
            "tea.financial_kpis.npv_eur",
            "tea.financial_kpis.npv_without_public_support_eur",
            "tea.financial_kpis.operating_profit_before_support_eur_per_year",
            "tea.financial_kpis.operating_profit_including_operating_support_eur_per_year",
            "tea.financial_kpis.annual_operating_support_eur_per_year",
            "tea.financial_kpis.cost_per_tonne_wet_feed_eur",
            "tea.totals.total_direct_capex_eur",
            "tea.totals.annual_opex_eur",
            "tea.totals.annual_revenue_eur",
            "tea.totals.total_public_support_pv_eur",
            "tea.totals.capex_grant_fraction_applied",
            "tea.totals.opex_premium_eur_per_year",
        }
        return (path in core_tea or path.startswith("carbon_assessment.")
                or path.startswith("annual.feed_processed.")
                or path.startswith("annual.products.")
                or path.startswith("annual.volumetric_products.")
                or path.startswith("annual.utilities.")
                or path.startswith("annual.balance.overall_closure")
                or path in {"lca.totals.climate_kg_co2e_per_year",
                            "lca.totals.kg_co2e_per_tonne_wet_feed",
                            "lca.totals.kg_co2e_per_tonne_dry_feed"})
    selected = sorted((path for path in endpoint_peak if figure_eligible(path) and endpoint_peak[path] > 0),
                      key=lambda path: (report_branch(path), path))
    input_keys = [key for key in INPUTS if any(key in matrix[path] for path in selected)]
    out_dir = root / "figures"
    out_dir.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 8, "axes.titlesize": 11, "axes.labelsize": 9,
                         "savefig.dpi": 200, "figure.dpi": 120})
    fig, ax = plt.subplots(figsize=(max(10, .62 * len(input_keys)), max(9, .30 * len(selected))),
                           constrained_layout=True)
    grid = np.full((len(selected), len(input_keys)), np.nan)
    for yi, endpoint in enumerate(selected):
        for xi, key in enumerate(input_keys):
            if key in matrix[endpoint]:
                grid[yi, xi] = matrix[endpoint][key]
    image = ax.imshow(grid, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(input_keys)), [INPUTS[k] for k in input_keys], rotation=45, ha="right")
    labels = []
    for path in selected:
        pieces = path.split(".")
        branch = report_branch(path).replace("_", " ").title()
        if pieces[0] == "tea":
            label = pieces[-1].replace("_eur_per_year", "").replace("_eur", "").replace("_", " ")
            label = f"TEA · {label.title()}"
        elif pieces[0] == "annual":
            label = "Annual · " + " ".join(pieces[1:]).replace(".value", "").replace("_", " ").title()
        elif pieces[0] == "carbon_assessment":
            label = "Carbon · " + pieces[-1].replace("_t_c_per_year", "").replace("_t_co2e_per_year", "").replace("_", " ").title()
        elif pieces[0] == "lca":
            label = "LCA · " + pieces[-1].replace("_kg_co2e_per_year", "").replace("_kg_co2e_per_tonne_wet_feed", "").replace("_", " ").title()
        else:
            label = "Objective · " + pieces[1].replace("_", " ").title()
        if len(label) > 54:
            label = label[:51] + "…"
        labels.append(label)
    ax.set_yticks(range(len(selected)), labels, fontsize=8)
    ax.set_title("Global input–KPI sensitivity", color=PALETTE["ink"], fontweight="bold")
    colorbar = fig.colorbar(image, ax=ax, shrink=.82)
    colorbar.set_label("Spearman ρ")
    fig.savefig(out_dir / "global_endpoint_sensitivity_heatmap.png", bbox_inches="tight")
    plt.close(fig)

    # Which report branches have the strongest sampled-input association.
    branch_scores: dict[str, list[float]] = defaultdict(list)
    for row in correlation_rows:
        branch_scores[row["report_section"]].append(row["absolute_rho"])
    branch_rows = sorted(((key, max(vals), sum(vals) / len(vals), len(vals))
                          for key, vals in branch_scores.items()), key=lambda x: x[1], reverse=True)
    with (root / "global_endpoint_sensitivity_by_section.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["report_section", "maximum_absolute_rho", "mean_absolute_rho", "input_endpoint_pairs"])
        writer.writerows(branch_rows)

    metadata = {
        "cases": records,
        "dynamic_endpoint_paths": len(endpoint_values),
        "input_parameters": len(INPUTS),
        "correlations_written": len(correlation_rows),
        "endpoint_path_rule": "Discovered from archived numeric_endpoints for every successful report; missing values remain missing.",
        "statistics": "Spearman rank associations are descriptive screening sensitivities. They are not causal effects, probabilities, or uncertainty intervals.",
        "figure": "figures/global_endpoint_sensitivity_heatmap.png",
        "full_results": "global_endpoint_sensitivity.csv",
        "by_section": "global_endpoint_sensitivity_by_section.csv",
    }
    (root / "global_endpoint_sensitivity_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
