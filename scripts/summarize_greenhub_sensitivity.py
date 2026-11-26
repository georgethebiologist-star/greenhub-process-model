"""Create supplementary summaries from a completed GreenHub sensitivity run.

This postprocessor reads the run folder's dynamically discovered endpoint
catalog; it does not rerun or alter model calculations. Example:
    .venv/Scripts/python scripts/summarize_greenhub_sensitivity.py results/sensitivity_analysis/seasonal_mc_monthly_20261106
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from Greenhub.sensitivity_archive import iter_report_records, report_archives


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_folder", type=Path)
    parser.add_argument("--seed", type=int, default=20261106)
    args = parser.parse_args()
    root = args.run_folder.resolve()
    summaries_path = root / "endpoint_summaries.json"
    units_path = root / "endpoint_units.json"
    if not summaries_path.exists():
        parser.error(f"Missing endpoint summary: {summaries_path}")
    summaries = json.loads(summaries_path.read_text(encoding="utf-8"))
    units = json.loads(units_path.read_text(encoding="utf-8")) if units_path.exists() else {}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit(f"matplotlib is required: {exc}")

    out = root / "figures"
    out.mkdir(exist_ok=True)
    palette = {"ink": "#0b3b3e", "green": "#3f9456", "blue": "#6b9bd2",
               "rose": "#cf6a9b", "gold": "#d5a61a", "orange": "#b97635"}
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 11, "axes.labelsize": 9,
                         "savefig.dpi": 180, "figure.dpi": 120})

    # Count all numeric endpoints represented in each report branch. Array
    # indices are grouped back into their parent branch for a readable chart.
    branches: Counter[str] = Counter()
    for path in summaries:
        head = path.split(".", 1)[0]
        head = head.split("[", 1)[0]
        branches[head] += 1
    ordered = branches.most_common()
    fig, ax = plt.subplots(figsize=(8.5, max(3.6, .33 * len(ordered))), constrained_layout=True)
    labels = [name.replace("_", " ").title() for name, _ in ordered]
    values = [count for _, count in ordered]
    ax.barh(labels[::-1], values[::-1], color=palette["green"])
    ax.set_xlabel("Numeric endpoints summarized")
    ax.set_title("Endpoint coverage by report section", color=palette["ink"], fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=.16)
    fig.savefig(out / "endpoint_coverage_by_section.png", bbox_inches="tight")
    plt.close(fig)

    # Identify variable endpoints by coefficient of variation. This is a
    # screening descriptor only; values near zero and signed values can make
    # CV misleading, so those endpoints are excluded and the CSV preserves all
    # remaining numeric summaries for review.
    rows = []
    for path, item in summaries.items():
        mean = item.get("mean")
        sd = item.get("sd")
        if not isinstance(mean, (int, float)) or not isinstance(sd, (int, float)):
            continue
        magnitude = max(abs(item.get("min", 0)), abs(item.get("max", 0)))
        if magnitude <= 0 or abs(mean) <= magnitude * 1e-8:
            continue
        cv = abs(sd / mean)
        if not math.isfinite(cv):
            continue
        rows.append((path, cv, mean, sd, item.get("min"), item.get("max"), units.get(path, "")))
    rows.sort(key=lambda row: row[1], reverse=True)
    import csv
    with (root / "endpoint_variability_summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["endpoint", "coefficient_of_variation", "mean", "sd", "min", "max", "unit", "interpretation"])
        writer.writerows([(*row, "CV is descriptive; signed or near-zero means are excluded from the figure") for row in rows])

    # Closure residuals can be numerically tiny while varying around zero,
    # which makes their coefficient of variation enormous and uninformative.
    # Keep every numeric endpoint in the CSV, but exclude balance-closure
    # residuals from this descriptive variability figure.
    detail_tokens = ("state_outputs", "source_traceability", "financial_assumptions",
                     "capex_lines", "opex_lines", "revenue_lines", "cash_flow",
                     "cash flow", "annual.monthly", "lca.inventory", "lca.factors",
                     "candidate_economics.assumptions")
    def figure_endpoint(path: str) -> bool:
        lower = path.lower()
        if "residual" in lower or any(token in lower for token in detail_tokens):
            return False
        if path.startswith(("objectives.", "carbon_assessment.", "annual.products.",
                            "annual.utilities.", "annual.feed_processed.")):
            return True
        return path in {
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
    figure_rows = [row for row in rows if figure_endpoint(row[0]) and row[1] > 0]
    selected = figure_rows[:24]
    if selected:
        fig, ax = plt.subplots(figsize=(10, max(5.0, .32 * len(selected))), constrained_layout=True)
        y = list(range(len(selected)))
        ax.barh(y, [row[1] for row in selected], color=palette["blue"])
        ax.set_yticks(y, [row[0].replace("_", " ") for row in selected], fontsize=7)
        ax.invert_yaxis()
        ax.set_xlabel("Coefficient of variation (SD / |mean|)")
        ax.set_title("Most variable process endpoints", color=palette["ink"], fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", alpha=.16)
        fig.savefig(out / "endpoint_variability_top24.png", bbox_inches="tight")
        plt.close(fig)

    note = {
        "endpoint_count": len(summaries),
        "section_counts": dict(ordered),
        "variability_rows": len(rows),
        "variability_figure_rule": "Top 24 by descriptive coefficient of variation; near-zero means and mass/element balance residuals excluded from the figure. All endpoint summaries remain in CSV. This is not a causal sensitivity ranking.",
        "figures": ["endpoint_coverage_by_section.png", "endpoint_variability_top24.png"],
    }
    (root / "endpoint_postprocessing_summary.json").write_text(json.dumps(note, indent=2), encoding="utf-8")

    # The configured preview carries a user-defined grass-use bonus at its
    # maximum €50/t, while the model contract documents a €0–50/t interval.
    # This is an important economic uncertainty omitted from the main sampler
    # so that the core physical/economic run remains comparable to its source
    # configuration. Recalculate only the support/tax cash-flow overlay on
    # each saved, simulated report; do not rerun or alter process outputs.
    if report_archives(root):
        import csv
        rng = random.Random(args.seed)
        additional = []
        input_kpis: dict[str, list[tuple[float, float]]] = {}
        for record in iter_report_records(root):
            if not isinstance(record, dict):
                continue
            report = record.get("report") or {}
            config = record.get("configuration") or {}
            tea = report.get("tea") or {}
            annual = report.get("annual") or {}
            base_npv = ((tea.get("financial_kpis") or {}).get("npv_eur"))
            cash_rows = tea.get("cash_flow") or []
            econ = config.get("candidate_economics") or {}
            feed_kg = ((annual.get("feed_processed") or {}).get("value"))
            if not isinstance(base_npv, (int, float)) or not isinstance(feed_kg, (int, float)) or not cash_rows:
                continue
            feed_t = float(feed_kg) / 1000.0
            old_rate = float(econ.get("grass_utilization_bonus_eur_per_t_feed", 0.0) or 0.0)
            years = max(0, int(econ.get("grass_utilization_bonus_years", 0) or 0))
            lifetime = max(1, int(econ.get("project_lifetime_years", 20) or 20))
            discount = max(0.0, float(econ.get("discount_rate", .08) or 0.0))
            tax_rate = max(0.0, min(1.0, float(econ.get("tax_rate", .258) or 0.0)))
            rate = rng.uniform(0.0, 50.0)
            delta_npv = 0.0
            for cash_row in cash_rows:
                year = int(cash_row.get("year", 0) or 0)
                if year <= 0 or year > lifetime:
                    continue
                op_profit = float(cash_row.get("operating_profit_before_support_eur", 0.0) or 0.0)
                other_support = sum(float(cash_row.get(key, 0.0) or 0.0) for key in (
                    "legacy_operating_support_eur", "biomethane_bonus_eur", "additional_operating_support_eur"))
                old_grass = feed_t * old_rate if year <= years else 0.0
                new_grass = feed_t * rate if year <= years else 0.0
                old_tax = max(0.0, op_profit + other_support + old_grass) * tax_rate
                new_tax = max(0.0, op_profit + other_support + new_grass) * tax_rate
                delta_cash = (new_grass - old_grass) - (new_tax - old_tax)
                delta_npv += delta_cash / ((1.0 + discount) ** year)
            adjusted = float(base_npv) + delta_npv
            annuity = years if discount == 0 else (1 - (1 + discount) ** (-years)) / discount
            summary = record.get("summary") or {}
            additional.append({
                "sample": record.get("sample"), "grass_utilization_bonus_eur_per_t_feed": rate,
                "adjusted_npv_eur": adjusted, "npv_delta_eur": delta_npv,
                "grass_logistics_bonus_pv_eur": feed_t * rate * annuity,
                "public_support_pv_eur": float(summary.get("public_support_pv_eur") or 0.0),
                "ghg_kg_co2e_y": summary.get("ghg_kg_co2e_y"),
                "operating_income_overlay_only": True,
            })
            for key in ("juice_yield", "protein_multiplier", "carbohydrate_multiplier", "nitrogen_g_kg_dm",
                        "phosphorus_g_kg_dm", "potassium_g_kg_dm", "capex_grant_fraction",
                        "biomethane_bonus_eur_per_m3"):
                x = summary.get(key)
                if isinstance(x, (int, float)):
                    input_kpis.setdefault(key, []).append((float(x), adjusted))
            input_kpis.setdefault("grass_utilization_bonus_eur_per_t_feed", []).append((rate, adjusted))
        if additional:
            with (root / "grass_use_bonus_sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(additional[0]))
                writer.writeheader(); writer.writerows(additional)
            fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), constrained_layout=True)
            base_values = [float(row["adjusted_npv_eur"] - row["npv_delta_eur"]) for row in additional]
            adjusted_values = [float(row["adjusted_npv_eur"]) for row in additional]
            axes[0].hist(base_values, bins=28, alpha=.62, color=palette["blue"], label="Preview bonus")
            axes[0].hist(adjusted_values, bins=28, alpha=.62, color=palette["green"], label="€0–50/t range")
            axes[0].axvline(0, color=palette["ink"], lw=.9)
            axes[0].set_xlabel("NPV (€)"); axes[0].set_ylabel("Monte Carlo cases")
            axes[0].set_title("NPV distribution")
            axes[0].legend(frameon=False, fontsize=8)
            axes[1].scatter([row["grass_utilization_bonus_eur_per_t_feed"] for row in additional], adjusted_values,
                            s=12, alpha=.55, color=palette["rose"], edgecolors="none")
            axes[1].axhline(0, color=palette["ink"], lw=.9)
            axes[1].set_xlabel("Grass-use bonus (€/t feed)"); axes[1].set_ylabel("Adjusted NPV (€)")
            axes[1].set_title("Bonus and NPV")
            for ax in axes:
                ax.spines[["top", "right"]].set_visible(False); ax.grid(alpha=.15)
            fig.suptitle("Supplementary support sensitivity", color=palette["ink"], fontweight="bold")
            fig.savefig(out / "grass_use_bonus_npv_sensitivity.png", bbox_inches="tight")
            plt.close(fig)
            try:
                from scipy.stats import spearmanr
                corr = []
                for key, pairs in input_kpis.items():
                    if len(pairs) < 3:
                        continue
                    rho = float(spearmanr([x for x, _ in pairs], [y for _, y in pairs]).statistic)
                    if math.isfinite(rho):
                        corr.append((key, rho))
                corr.sort(key=lambda x: abs(x[1]))
                fig, ax = plt.subplots(figsize=(8.5, max(4.0, .38 * len(corr))), constrained_layout=True)
                labels = [key.replace("_", " ").title() for key, _ in corr]
                vals = [value for _, value in corr]
                ax.barh(labels, vals, color=[palette["green"] if value >= 0 else palette["rose"] for value in vals])
                ax.axvline(0, color=palette["ink"], lw=.8)
                ax.set_xlim(-1, 1); ax.set_xlabel("Spearman ρ with NPV")
                ax.set_title("Global NPV sensitivity with grass-use support", color=palette["ink"], fontweight="bold")
                ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="x", alpha=.16)
                fig.savefig(out / "global_npv_rank_correlations_with_grass_bonus.png", bbox_inches="tight")
                plt.close(fig)
            except ImportError:
                pass
            with (root / "grass_use_bonus_sensitivity_method.md").open("w", encoding="utf-8") as stream:
                stream.write("# Supplementary grass-use bonus analysis\n\n")
                stream.write("The configured preview includes a user-defined bonus of €50 per wet tonne processed; the backend enforces a €0–50/t range. To represent this documented input without rerunning process physics, this postprocessor draws a transparent uniform screening value on that range for each saved global Monte Carlo case and recalculates only the financial support, tax and NPV overlay using its archived annual report. This is range coverage, not a probability distribution or program award. Mass, energy, products, and GHG remain those of the corresponding saved model simulation. The calculation mirrors the backend cash-flow formula and applies the sampled bonus only during configured support years.\n")
    print(f"Summarized {len(summaries)} numeric endpoints in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
