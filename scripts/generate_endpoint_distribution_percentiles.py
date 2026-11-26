"""Plot empirical distributions and 5th/95th percentiles for GreenHub MC outputs."""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results/sensitivity_analysis/seasonal_mc_monthly_20261106"
OUTPUT = RUN / "figures/global_endpoint_distributions_p05_p95.png"


def read_kpis() -> dict[str, np.ndarray]:
    with (RUN / "monte_carlo_kpis.csv").open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    rows = [row for row in rows if row.get("status") == "evaluated"]
    if not rows:
        raise RuntimeError("No evaluated Monte Carlo KPI rows found")
    numeric: dict[str, np.ndarray] = {}
    for key in rows[0]:
        try:
            numeric[key] = np.asarray([float(row[key]) for row in rows], dtype=float)
        except (TypeError, ValueError):
            continue
    return numeric


def read_product_and_utility_endpoints() -> tuple[dict[str, np.ndarray], float]:
    wanted = {
        "annual.products.biomethane.value": "Biomethane",
        "annual.products.ammonium_product.value": "Ammonium product",
        "annual.products.nutrient_rich_solids.value": "Nutrient-rich solids",
        "annual.utilities.electricity.value": "Electricity",
        "annual.utilities.heating.value": "Heat",
        "annual.utilities.cooling.value": "Cooling",
    }
    values: dict[str, list[float]] = {label: [] for label in wanted.values()}
    densities: list[float] = []
    archives = sorted(RUN.glob("all_endpoint_reports_*.jsonl.gz"))
    if not archives:
        raise FileNotFoundError("Global endpoint report shards are missing")
    for archive in archives:
        with gzip.open(archive, "rt", encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                endpoints = item.get("numeric_endpoints", {})
                for key, label in wanted.items():
                    value = endpoints.get(key)
                    if isinstance(value, (int, float)) and np.isfinite(value):
                        values[label].append(float(value))
                economics = item.get("configuration", {}).get("candidate_economics", {})
                density = economics.get("biomethane_density_kg_per_nm3")
                if isinstance(density, (int, float)) and density > 0:
                    densities.append(float(density))
    density = float(np.median(densities)) if densities else 0.716
    return {key: np.asarray(value, dtype=float) for key, value in values.items()}, density


def compact(value: float) -> str:
    magnitude = abs(value)
    if magnitude >= 1_000_000:
        return f"{value / 1_000_000:.2f}m"
    if magnitude >= 10_000:
        return f"{value / 1_000:.0f}k"
    if magnitude >= 1_000:
        return f"{value / 1_000:.1f}k"
    if magnitude >= 100:
        return f"{value:.0f}"
    if magnitude >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def make_metrics() -> list[tuple[str, str, np.ndarray, str]]:
    kpis = read_kpis()
    endpoints, density = read_product_and_utility_endpoints()
    metrics: list[tuple[str, str, np.ndarray, str]] = []

    def add(title: str, unit: str, values: np.ndarray, group: str, factor: float = 1.0) -> None:
        values = np.asarray(values, dtype=float) * factor
        values = values[np.isfinite(values)]
        if len(values) > 1 and np.ptp(values) > 1e-12:
            metrics.append((title, unit, values, group))

    add("Biomethane", "Nm³/year", endpoints["Biomethane"], "Products", 1 / density)
    add("Ammonium product", "t/year", endpoints["Ammonium product"], "Products", 1e-3)
    add("Nutrient-rich solids", "t/year", endpoints["Nutrient-rich solids"], "Products", 1e-3)
    add("Electricity", "MWh/year", endpoints["Electricity"], "Utilities", 1e-3)
    add("Heat", "MWh/year", endpoints["Heat"], "Utilities", 1e-3)
    add("Cooling", "MWh/year", endpoints["Cooling"], "Utilities", 1e-3)

    finance = [
        ("CAPEX", "capex_eur", "€"),
        ("OPEX", "opex_eur_y", "€/year"),
        ("Revenue", "revenue_eur_y", "€/year"),
        ("Operating profit", "operating_profit_eur_y", "€/year"),
        ("NPV · with support", "npv_eur", "€"),
        ("NPV · without support", "npv_without_public_support_or_grass_bonus_eur", "€"),
        ("Public support PV", "public_support_pv_eur", "€"),
    ]
    for label, key, unit in finance:
        if key in kpis:
            add(label, unit, kpis[key], "Economics")

    for label, key, unit, factor in (
        ("Attributional GHG", "ghg_kg_co2e_y", "t CO₂-eq/year", 1e-3),
        ("GHG intensity", "ghg_kg_co2e_per_t_feed", "kg CO₂-eq/t feed", 1.0),
        ("Net carbon", "net_carbon_t_c_y", "t C/year", 1.0),
    ):
        if key in kpis:
            add(label, unit, kpis[key], "Environment", factor)
    return metrics


def main() -> None:
    metrics = make_metrics()
    ncols = 4
    nrows = int(np.ceil(len(metrics) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 3.15 * nrows), constrained_layout=False)
    axes = np.asarray(axes).reshape(-1)
    colors = {"p05": "#3d9253", "median": "#173b43", "p95": "#d36f9d"}
    group_colors = {"Products": "#3d9253", "Utilities": "#d7a414", "Economics": "#6b96d2", "Environment": "#d36f9d"}

    for ax, (label, unit, data, group) in zip(axes, metrics):
        p05, p50, p95 = np.quantile(data, [0.05, 0.50, 0.95])
        ax.hist(data, bins="fd", color=group_colors[group], alpha=0.55, edgecolor="white", linewidth=0.45)
        ax.axvline(p05, color=colors["p05"], linewidth=1.8, linestyle="--")
        ax.axvline(p50, color=colors["median"], linewidth=1.8)
        ax.axvline(p95, color=colors["p95"], linewidth=1.8, linestyle="--")
        ax.set_title(label, loc="left", fontsize=14, fontweight="bold", color="#12383b", pad=8)
        ax.set_xlabel(unit, fontsize=14, labelpad=8)
        ax.set_ylabel("Density", fontsize=14, labelpad=8)
        ax.tick_params(axis="both", labelsize=12, pad=5)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: compact(value)))
        ax.grid(axis="y", color="#d8d7d4", linewidth=0.6, alpha=0.8)
        ax.spines[["top", "right"]].set_visible(False)

    for ax in axes[len(metrics):]:
        ax.set_visible(False)

    legend = [
        plt.Line2D([0], [0], color=colors["p05"], linestyle="--", linewidth=2, label="5th percentile"),
        plt.Line2D([0], [0], color=colors["median"], linewidth=2, label="Median"),
        plt.Line2D([0], [0], color=colors["p95"], linestyle="--", linewidth=2, label="95th percentile"),
    ]
    fig.suptitle("Global endpoint distributions", fontsize=25, fontweight="bold", color="#12383b", y=0.985)
    fig.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=3, frameon=False, fontsize=13)
    fig.tight_layout(rect=(0.015, 0.015, 0.995, 0.91), h_pad=2.2, w_pad=1.9)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {OUTPUT} with {len(metrics)} varying endpoints")


if __name__ == "__main__":
    main()
