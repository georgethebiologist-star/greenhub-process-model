"""Generate PR7 benchmark figures and one full-route BioSTEAM output figure.

Benchmark figures are distinguished from the simulated full-route mass split.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "Greenhub" / "data" / "Protein recovery" / "Membrane"
OUT = ROOT / "results" / "report_figures" / "12_biostimulant_screening"
OUT.mkdir(parents=True, exist_ok=True)
INDEX = OUT / "figure_index.csv"
MASTER_INDEX = ROOT / "results" / "report_figures" / "figure_index.csv"

BG = "#efebe6"
PANEL = "#f8f5f1"
INK = "#0c3338"
GREEN = "#408f4d"
BLUE = "#729ad2"
YELLOW = "#d1a520"
ROSE = "#d277a3"
SAND = "#e4b839"
GREY = "#687977"
TECH_COLORS = {"TUF": GREEN, "LNF": BLUE, "MEUF": ROSE}

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "savefig.facecolor": BG,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.edgecolor": INK,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})


def read_rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fx_eur_per_usd() -> tuple[float, str]:
    row = next(r for r in read_rows("biostimulant_membrane_gated_parameters.csv") if r["parameter_id"] == "FX_USD_EUR")
    return float(row["value"]), row["source_date"]


def style(ax, *, grid_axis="x"):
    ax.grid(axis=grid_axis, color=GREY, alpha=0.22, linewidth=0.55)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GREY)


def save(fig, filename: str):
    output = OUT / filename
    fig.savefig(output, dpi=300, bbox_inches="tight", facecolor=BG)
    # Keep a consistent publication export width while preserving the chart's
    # palette, layout, and 300-DPI metadata.
    with Image.open(output) as image:
        if image.width > 2400:
            height = round(image.height * 2400 / image.width)
            image = image.resize((2400, height), Image.Resampling.LANCZOS)
            image.save(output, dpi=(300, 300), optimize=True)
    plt.close(fig)


def hormone_content_figure(hormones: list[dict[str, str]]):
    labels = ["IAA", "Zeatin", "Zeatin riboside"]
    rows = {row["solute_id"]: row for row in hormones}
    IDs = ["IAA", "Zeatin", "ZeatinRiboside"]
    totals = np.array([float(rows[key]["total_concentration_ug_L"]) for key in IDs])
    free = totals * np.array([float(rows[key]["free_fraction"]) for key in IDs])
    bound = totals * np.array([float(rows[key]["bound_fraction"]) for key in IDs])
    fig, ax = plt.subplots(figsize=(7.7, 4.8), constrained_layout=True)
    y = np.arange(len(labels))
    ax.barh(y, free, color=BLUE, height=0.58, label="Free pool")
    ax.barh(y, bound, left=free, color=GREEN, height=0.58, label="Bound pool")
    for index, total in enumerate(totals):
        ax.text(total + max(totals) * 0.018, index, f"{total:g}", va="center", color=INK, fontsize=9)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Concentration (µg/L clarified juice)")
    ax.set_title("Hormone content split", loc="left", fontweight="bold")
    ax.set_xlim(0, max(totals) * 1.23)
    style(ax)
    ax.legend(frameon=False, ncol=2, loc="lower right")
    save(fig, "pr7_hormone_content_split.png")


def hormone_retention_figure(hormones: list[dict[str, str]]):
    from Greenhub.biostimulant_screening import calculate_film_retention

    labels = ["IAA", "Zeatin", "Zeatin riboside"]
    IDs = ["IAA", "Zeatin", "ZeatinRiboside"]
    rows = {row["solute_id"]: row for row in hormones}
    technologies = ["TUF", "LNF", "MEUF"]
    values = {
        technology: [
            100 * (
                float(rows[key]["free_fraction"])
                * (
                    float(calculate_film_retention(technology, key, "free", 22.0)["predicted_retention_fraction"])
                    if technology == "TUF"
                    else float(rows[key][f"retention_{technology}_free_fraction"])
                )
                + float(rows[key]["bound_fraction"])
                * float(rows[key][f"retention_{technology}_bound_fraction"])
            )
            for key in IDs
        ]
        for technology in technologies
    }
    x = np.arange(len(labels))
    width = 0.23
    fig, ax = plt.subplots(figsize=(7.7, 4.8), constrained_layout=True)
    for index, technology in enumerate(technologies):
        bars = ax.bar(
            x + (index - 1) * width,
            values[technology],
            width,
            color=TECH_COLORS[technology],
            label=technology,
        )
        labels_for_bars = [f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}" for value in values[technology]]
        ax.bar_label(bars, labels=labels_for_bars, padding=2, fontsize=8, color=INK)
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Weighted analyte retention (%)")
    ax.set_title("Hormone retention", loc="left", fontweight="bold")
    style(ax, grid_axis="y")
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.text(
        0.99, 0.99, "TUF free-state uses σ/Peclet at 22 L/(m²·h); MEUF is a generic midpoint.",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color=GREY,
        bbox={"facecolor": PANEL, "edgecolor": "none", "alpha": 0.9, "pad": 2},
    )
    save(fig, "pr7_hormone_retention.png")


def film_retention_check_figure(hormones: list[dict[str, str]]):
    """Show the supplied retention basis beside the independent film model."""
    from Greenhub.biostimulant_screening import calculate_film_retention

    labels = ["IAA", "Zeatin", "Zeatin riboside"]
    IDs = ["IAA", "Zeatin", "ZeatinRiboside"]
    rows = {row["solute_id"]: row for row in hormones}
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 4.8), sharey=True, constrained_layout=True)
    for ax, technology, flux in zip(axes, ("TUF", "LNF"), (22.0, 12.0)):
        empirical = [100 * float(rows[key][f"retention_{technology}_free_fraction"]) for key in IDs]
        film = [100 * calculate_film_retention(technology, key, "free", flux)["predicted_retention_fraction"] for key in IDs]
        x = np.arange(len(labels))
        width = 0.34
        applied_label = "Applied free retention" if technology == "TUF" else "Empirical free retention"
        a = ax.bar(x - width / 2, empirical, width, color=TECH_COLORS[technology], label=applied_label)
        b = ax.bar(x + width / 2, film, width, color=ROSE, label="Free film prediction")
        ax.bar_label(a, labels=[f"{value:.1f}" for value in empirical], padding=2, fontsize=7.5, color=INK)
        ax.bar_label(b, labels=[f"{value:.1f}" for value in film], padding=2, fontsize=7.5, color=INK)
        ax.set_xticks(x, labels)
        ax.set_title(f"{technology} · {flux:g} L/(m²·h)", loc="left", fontweight="bold")
        ax.set_ylim(0, 112)
        style(ax, grid_axis="y")
    axes[0].set_ylabel("Retention (%)")
    fig.suptitle("Retention model check", x=0.02, ha="left", fontsize=13, fontweight="bold", color=INK)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.04))
    fig.text(
        0.5, -0.02,
        "TUF free-state σ/Peclet term is applied to the split; LNF film result is diagnostic. Bound film prediction unavailable.",
        ha="center", va="top", fontsize=7.5, color=GREY,
    )
    save(fig, "pr7_retention_model_check.png")


def hormone_capture_figure(hormones: list[dict[str, str]]):
    """Compare free and bound analyte capture per 1,000 m³ feed."""
    from Greenhub.biostimulant_screening import calculate_film_retention
    labels = ["IAA", "Zeatin", "Zeatin riboside"]
    IDs = ["IAA", "Zeatin", "ZeatinRiboside"]
    rows = {row["solute_id"]: row for row in hormones}
    technologies = ["TUF", "LNF", "MEUF"]
    # ug/L × 1,000 m³ × 1,000 L/m³ × 1e-3 mg/ug = mg per 1,000 m³
    values = {
        technology: {
            state: [
                float(rows[key]["total_concentration_ug_L"])
                * 1_000_000
                * float(rows[key][f"{state}_fraction"])
                * (
                    float(calculate_film_retention(technology, key, "free", 22.0)["predicted_retention_fraction"])
                    if technology == "TUF" and state == "free"
                    else float(rows[key][f"retention_{technology}_{state}_fraction"])
                )
                / 1000
                for key in IDs
            ]
            for state in ("free", "bound")
        }
        for technology in technologies
    }
    x = np.arange(len(labels))
    width = 0.23
    fig, ax = plt.subplots(figsize=(7.6, 4.8), constrained_layout=True)
    for index, technology in enumerate(technologies):
        free_values = values[technology]["free"]
        bound_values = values[technology]["bound"]
        ax.bar(
            x + (index - 1) * width,
            free_values,
            width,
            color=TECH_COLORS[technology],
            label=technology,
        )
        ax.bar(
            x + (index - 1) * width,
            bound_values,
            width,
            bottom=free_values,
            color=TECH_COLORS[technology],
            hatch="///",
            edgecolor=PANEL,
            linewidth=0.4,
        )
        totals = [a + b for a, b in zip(free_values, bound_values)]
        for xpos, total in zip(x + (index - 1) * width, totals):
            ax.text(xpos, total + max(totals) * 0.025, f"{total:,.0f}", ha="center", va="bottom", fontsize=7, color=INK)
    all_totals = [
        values[technology]["free"][idx] + values[technology]["bound"][idx]
        for technology in technologies for idx in range(len(IDs))
    ]
    ax.set_ylim(0, max(all_totals) * 1.22)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Captured analyte (mg / 1,000 m³ feed)")
    ax.set_title("Hormone capture", loc="left", fontweight="bold")
    ax.text(
        0.99, 0.99,
        "Solid = free; hatched = bound.",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color=GREY,
        bbox={"facecolor": PANEL, "edgecolor": "none", "alpha": 0.9, "pad": 2},
    )
    style(ax, grid_axis="y")
    ax.legend(frameon=False, ncol=3, loc="upper left")
    save(fig, "pr7_hormone_capture_by_technology.png")


def membrane_windows_figure(options: list[dict[str, str]], flux_records: list[dict[str, str]]):
    rows = {row["technology_id"]: row for row in options}
    comparator = next(
        (row for row in flux_records if row["parameter_id"] == "FLUX-001" and row["data_status"] == "measured"),
        None,
    )
    comparator_pressure = None
    if comparator is not None:
        match = re.search(
            r"TMP\s*([0-9.]+)\s*[–-]\s*([0-9.]+)\s*bar",
            comparator["operating_conditions"],
            re.IGNORECASE,
        )
        if match:
            comparator_pressure = (float(match.group(1)), float(match.group(2)))
    technologies = ["TUF", "LNF", "MEUF"]
    definitions = [
        ("Permeate flux", "permeate_flux_min_L_m2_h", "permeate_flux_max_L_m2_h", "L/(m²·h)"),
        ("Operating pressure", "tmp_min_bar", "tmp_max_bar", "bar"),
        ("Module price", "membrane_price_min_EUR_m2", "membrane_price_max_EUR_m2", "EUR/m²"),
        ("Scaling exponent", "scaling_exponent_min", "scaling_exponent_max", "dimensionless"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 6.4))
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.18, top=0.87, wspace=0.58, hspace=0.38)
    for ax, (title, low_key, high_key, unit) in zip(axes.flat, definitions):
        labels = list(technologies)
        lows = [float(rows[tech][low_key]) for tech in technologies]
        highs = [float(rows[tech][high_key]) for tech in technologies]
        direct_comparator = comparator is not None and (
            title == "Permeate flux" or (title == "Operating pressure" and comparator_pressure is not None)
        )
        if direct_comparator and title == "Permeate flux":
            labels.append("Grass 60 nm UF")
            lows.append(float(comparator["flux_value"]))
            highs.append(float(comparator["flux_value"]))
        elif direct_comparator and title == "Operating pressure":
            labels.append("Grass 60 nm UF")
            lows.append(comparator_pressure[0])
            highs.append(comparator_pressure[1])
        y = np.arange(len(labels))
        for index, technology in enumerate(technologies):
            color = TECH_COLORS[technology]
            ax.plot([lows[index], highs[index]], [index, index], color=color, linewidth=5, solid_capstyle="round")
            ax.scatter([(lows[index] + highs[index]) / 2], [index], color=INK, marker="D", s=24, zorder=3)
            label = f"{lows[index]:.0f}–{highs[index]:.0f}" if "Module price" in title else f"{lows[index]:g}–{highs[index]:g}"
            ax.annotate(label, (highs[index], index), xytext=(9, 0), textcoords="offset points",
                        va="center", ha="left", fontsize=9, color=INK)
        if direct_comparator:
            index = len(labels) - 1
            ax.plot([lows[index], highs[index]], [index, index], color=GREY, linewidth=4, solid_capstyle="round")
            ax.scatter([(lows[index] + highs[index]) / 2], [index], color=INK, marker="D", s=28, zorder=3)
            value_label = f"{lows[index]:g}" if lows[index] == highs[index] else f"{lows[index]:g}–{highs[index]:g}"
            ax.annotate(value_label, (highs[index], index), xytext=(9, 0), textcoords="offset points",
                        va="center", ha="left", fontsize=9, color=INK)
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        ax.set_xlabel(unit)
        ax.set_title(title, loc="left", fontweight="bold", fontsize=11)
        ax.set_xlim(0, max(highs) * 1.62)
        style(ax)
    fig.suptitle("Membrane design ranges", x=0.02, ha="left", y=0.98, fontsize=14, fontweight="bold", color=INK)
    if comparator is not None:
        fig.text(
            0.02, 0.025,
            "Measured clover-grass 60 nm UF comparator; not a validation of the PR7 1–3 kDa TUF option.",
            ha="left", va="bottom", fontsize=7.5, color=GREY,
        )
    save(fig, "pr7_membrane_design_ranges.png")


def component_retention_figure(retentions: list[dict[str, str]]):
    display_labels = {
        "water": "Water hold-up",
        "crude_proteins": "Crude proteins",
        "peptides_amino_acids": "Peptides / amino acids",
        "sugars": "Sugars",
        "divalent_salts": "Divalent salts",
        "monovalent_salts": "Monovalent salts",
        "solid_particles": "Other solid phase pools",
    }
    labels = [display_labels.get(row["component_class"], row["component_class"].replace("_", " ").title()) for row in retentions]
    columns = ["TUF_retention_nominal", "LNF_retention_nominal", "MEUF_retention_nominal"]
    names = ["TUF", "LNF", "MEUF"]
    values = np.array([
        [float(row[column]) if row[column].strip() else np.nan for column in columns]
        for row in retentions
    ])
    fig, ax = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "greenhub_retention", [PANEL, "#d6c77e", GREEN]
    )
    cmap.set_bad("#d8d5d1")
    image = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(names)), names)
    ax.set_yticks(np.arange(len(labels)), labels)
    ax.set_title("Component co-retention", loc="left", fontweight="bold")
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            text_color = PANEL if np.isfinite(value) and value >= 0.72 else INK
            label = f"{value:.2f}" if np.isfinite(value) else "n/a"
            ax.text(col, row, label, ha="center", va="center", color=text_color, fontsize=9)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    colorbar.set_label("Retained fraction")
    colorbar.outline.set_visible(False)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(
        0.0, -0.19,
        "Water hold-up is VCF-derived; solid capture is assumed; MEUF class retentions were not supplied.",
        transform=ax.transAxes, ha="left", va="top", fontsize=7.5, color=GREY,
    )
    save(fig, "pr7_component_coretention.png")


def protein_retention_evidence_figure():
    """Contextual comparison; the literature membrane/feed differ from PR7."""
    labels = ["PR7 TUF · supplied", "PR7 LNF · supplied", "Grass-juice 60 nm UF"]
    centers = np.array([88.5, 99.0, 52.0])
    lows = np.array([85.0, 99.0, 52.0])
    highs = np.array([92.0, 99.0, 52.0])
    colors = [GREEN, BLUE, ROSE]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.barh(y, centers, color=colors, height=0.56)
    ax.errorbar(
        centers, y, xerr=np.vstack((centers - lows, highs - centers)),
        fmt="none", ecolor=INK, elinewidth=1.2, capsize=4,
    )
    for yi, value, low, high in zip(y, centers, lows, highs):
        label = f"{low:.0f}–{high:.0f}%" if high != low else f"{value:.0f}%"
        ax.text(high + 1.3, yi, label, va="center", ha="left", fontsize=9, color=INK)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 116)
    ax.set_xlabel("Crude protein rejection (%)")
    ax.set_title("Protein retention evidence", loc="left", fontweight="bold")
    style(ax, grid_axis="x")
    fig.subplots_adjust(left=0.31, right=0.98, top=0.84, bottom=0.25)
    fig.text(
        0.5, 0.045,
        "Comparator: fresh clover juice, 60 nm UF; membrane and feed differ from PR7.",
        ha="center", va="center", fontsize=7.8, color=GREY,
    )
    save(fig, "pr7_protein_retention_evidence.png")


def replacement_cost_figure(options: list[dict[str, str]]):
    """Show module-only quote ranges and lifetime-normalized replacement rates."""
    parameters = {row["parameter_id"]: float(row["value"]) for row in read_rows("biostimulant_membrane_gated_parameters.csv") if row["value"]}
    life_min = parameters["Membrane_Lifetime_Low"]
    life_max = parameters["Membrane_Lifetime_High"]
    fx, fx_date = fx_eur_per_usd()
    technologies = ["TUF", "LNF", "MEUF"]
    colors = [TECH_COLORS[technology] for technology in technologies]
    by_technology = {row["technology_id"]: row for row in options}
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 4.4), constrained_layout=True)
    panels = [
        ("Module purchase", "membrane_price_min_EUR_m2", "membrane_price_max_EUR_m2", "EUR/m²"),
    ]
    for ax, (title, low_key, high_key, unit) in zip(axes, panels):
        for index, technology in enumerate(technologies):
            row = by_technology[technology]
            low, high = float(row[low_key]), float(row[high_key])
            ax.plot([low, high], [index, index], color=TECH_COLORS[technology], linewidth=7, solid_capstyle="round")
            ax.scatter([low, high], [index, index], color=INK, s=22, zorder=3)
            ax.text(high + max(float(by_technology[t][high_key]) for t in technologies) * .035, index,
                    f"{low:.0f}–{high:.0f}", va="center", fontsize=9, color=INK)
        ax.set_yticks(np.arange(len(technologies)), technologies)
        ax.invert_yaxis()
        ax.set_xlabel(unit)
        ax.set_title(title, loc="left", fontweight="bold", fontsize=11)
        ax.set_xlim(0, max(float(by_technology[t][high_key]) for t in technologies) * 1.38)
        style(ax)
    ax = axes[1]
    for index, technology in enumerate(technologies):
        row = by_technology[technology]
        low = float(row["membrane_price_min_EUR_m2"]) / life_max
        high = float(row["membrane_price_max_EUR_m2"]) / life_min
        ax.plot([low, high], [index, index], color=TECH_COLORS[technology], linewidth=7, solid_capstyle="round")
        ax.scatter([low, high], [index, index], color=INK, s=22, zorder=3)
        ax.text(high + 8, index, f"{low:.0f}–{high:.0f}", va="center", fontsize=9, color=INK)
    ax.set_yticks(np.arange(len(technologies)), technologies)
    ax.invert_yaxis()
    ax.set_xlabel("EUR/(m²·year)")
    ax.set_title("Replacement allowance", loc="left", fontweight="bold", fontsize=11)
    ax.set_xlim(0, max(float(by_technology[t]["membrane_price_max_EUR_m2"]) / life_min for t in technologies) * 1.35)
    style(ax)
    fig.suptitle("Membrane cost screen", x=.02, ha="left", fontsize=14, fontweight="bold", color=INK)
    fig.text(.02, -.01, f"Source USD quotes converted at ECB {fx_date} rate ({1/fx:.4f} USD/EUR); replacement assumes {life_min:g}–{life_max:g} year life; module only.", fontsize=7.5, color=GREY)
    save(fig, "pr7_membrane_replacement_cost.png")


def capital_reference_figure(options: list[dict[str, str]]):
    """Separate PR7 media quotes from non-equivalent grass-biorefinery analogs."""
    references = {row["reference_id"]: row for row in read_rows("biostimulant_membrane_cost_references.csv")}
    analogs = [
        ("RISE press module\n8–20 m³/h", references["GRASS_PROTEIN_EXTRACTION_RISE_2024"], YELLOW),
        ("Grassa mobile plant\n5 t/h", references["GRASSA_MOBILE_BIOREFINERY_2018"], BLUE),
        ("Press-refining complex\n~1,700 ha", references["GRASSA_PRESS_REFINING_COMPLEX_2025"], ROSE),
    ]
    fig, (ax, module_ax) = plt.subplots(
        1, 2, figsize=(7.5, 5.0), gridspec_kw={"width_ratios": [1.45, 1.0]},
        constrained_layout=False,
    )
    fig.subplots_adjust(left=.16, right=.985, bottom=.25, top=.83, wspace=.32)
    for index, (label, row, color) in enumerate(analogs):
        raw = str(row["value_eur"]).replace("€", "").strip()
        parts = [float(value.replace(",", "")) / 1e6 for value in re.split(r"[-–]", raw)]
        low, high = min(parts), max(parts)
        ax.hlines(index, low, high, color=color, linewidth=8, alpha=0.88)
        ax.scatter([low, high] if low != high else [low], [index] * (2 if low != high else 1), color=INK, s=22, zorder=3)
        display = f"€{low:.2f}–{high:.2f}M" if low != high else f"€{high:.2f}M"
        ax.text(high + 0.45, index, display, va="center", fontsize=8, color=INK)
    ax.set_yticks(np.arange(len(analogs)), [label for label, _, _ in analogs], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Reported investment (EUR million)")
    ax.set_title("Grass-biorefinery context", loc="left", fontweight="bold", fontsize=11)
    ax.set_xlim(0, 30)
    style(ax)

    technologies = ["TUF", "LNF", "MEUF"]
    by_technology = {row["technology_id"]: row for row in options}
    for index, technology in enumerate(technologies):
        row = by_technology[technology]
        low = float(row["membrane_price_min_EUR_m2"])
        high = float(row["membrane_price_max_EUR_m2"])
        module_ax.hlines(index, low, high, color=TECH_COLORS[technology], linewidth=8, alpha=0.88)
        module_ax.scatter([low, high], [index, index], color=INK, s=22, zorder=3)
        module_ax.text(high + 12, index, f"€{low:.0f}–{high:.0f}", va="center", fontsize=8, color=INK)
    module_ax.set_yticks(np.arange(len(technologies)), technologies)
    module_ax.invert_yaxis()
    module_ax.set_xlabel("Membrane media (EUR/m²)")
    module_ax.set_title("PR7 module media", loc="left", fontweight="bold", fontsize=11)
    module_ax.set_xlim(0, 660)
    style(module_ax)
    fig.suptitle("Capital references", x=.02, y=.97, ha="left", fontsize=14, fontweight="bold", color=INK)
    fig.text(.02, .025, "Grass-biorefinery examples have different scopes and are context only; none is scaled into PR7 CAPEX.\nPR7 prices cover membrane media only; no installed-skid quote is available.", fontsize=7.2, color=GREY)
    save(fig, "pr7_capital_reference_context.png")


def cip_frequency_figure(evidence: list[dict[str, str]], parameters: list[dict[str, str]]):
    """Show PR7's supplied cleaning interval beside unlike literature cases."""
    interval = float(next(row["value"] for row in parameters if row["parameter_id"] == "CIP_Interval"))
    user_frequency = 8760.0 / interval
    nl_nf = next(row for row in evidence if row["evidence_id"] == "NL_NF_CIP_2021")
    nl_ro = next(row for row in evidence if row["evidence_id"] == "NL_RO_CIP_2021")
    nf_low, nf_high = nl_nf["reported_cip_frequency"].split(" events/")[0].split("-")
    ro_low, ro_high = nl_ro["reported_cip_frequency"].split(" events/")[0].split("-")
    cases = [
        (f"GreenHub · {interval:g} h", user_frequency, user_frequency, GREEN),
        ("Dutch NF", float(nf_low), float(nf_high), BLUE),
        ("Dutch RO", float(ro_low), float(ro_high), ROSE),
    ]
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True)
    positions = np.arange(len(cases))
    for y, (label, low, high, color) in zip(positions, cases):
        ax.hlines(y, low, high, color=color, linewidth=7, alpha=0.85)
        ax.plot((low + high) / 2, y, "o", color=color, markersize=8)
        shown = f"{low:,.1f}" if low == high else f"{low:g}–{high:g}"
        ax.text(high * 1.16, y, shown, va="center", color=INK, fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(0.4, user_frequency * 3.2)
    ax.set_yticks(positions, [case[0] for case in cases])
    ax.invert_yaxis()
    ax.set_xlabel("CIP events per year (GreenHub assumes 8,760 operating h/year)")
    ax.set_title("CIP frequency", loc="left", fontweight="bold")
    style(ax, grid_axis="x")
    save(fig, "pr7_cip_frequency_context.png")


def cip_lca_factor_figure():
    """Plot opt-in reagent factors; no annual CIP activity is implied."""
    from Greenhub.application.lca_service import screening_lca_factors

    factors = screening_lca_factors()
    items = [
        ("Active NaOH", factors["pr7_cip_naoh_active"], GREEN),
        ("Citric acid", factors["pr7_cip_citric_acid"], BLUE),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    positions = np.arange(len(items))
    values = [factor.value for _, factor, _ in items]
    bars = ax.barh(positions, values, color=[color for _, _, color in items], height=0.52)
    ax.bar_label(bars, labels=[f"{value:.2f}" for value in values], padding=5, fontsize=9, color=INK)
    ax.set_yticks(positions, [label for label, _, _ in items])
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.32)
    ax.set_xlabel("Climate factor (kg CO₂-eq/kg reagent)")
    ax.set_title("CIP reagent factors", loc="left", fontweight="bold")
    style(ax)
    ax.text(
        0.0, -0.23,
        "Opt-in screening factors · NaOH: Euro Chlor EU average · citric acid: Citribel Belgium cradle-to-gate · GWP vintage differs from IPCC AR6 utilities",
        transform=ax.transAxes, ha="left", va="top", fontsize=7.2, color=GREY,
    )
    save(fig, "pr7_cip_reagent_climate_factors.png")


def meuf_surfactant_figure(parameters: list[dict[str, str]]):
    """Plot nominal SDS dose and unrecovered make-up per m³ of feed."""
    values = {row["parameter_id"]: float(row["value"]) for row in parameters if row["value"].strip()}
    cmc_mol_L = values["SDS_CMC"] / 1000.0
    mw_g_mol = values["SDS_Molecular_Weight"]
    recovery = values["MEUF_Surfactant_Recovery"]
    multiples = [values["MEUF_Surfactant_Dose_Low"], values["MEUF_Surfactant_Dose_High"]]
    labels = [f"{multiple:g}× CMC" for multiple in multiples]
    gross = [cmc_mol_L * multiple * mw_g_mol for multiple in multiples]
    net = [quantity * (1.0 - recovery) for quantity in gross]
    x = np.arange(2)
    width = 0.32
    fig, ax = plt.subplots(figsize=(7.8, 4.5), constrained_layout=True)
    bars_gross = ax.bar(x - width / 2, gross, width, color=BLUE, label="Gross SDS dose")
    bars_net = ax.bar(x + width / 2, net, width, color=ROSE, label="Unrecovered make-up")
    ax.bar_label(bars_gross, labels=[f"{value:.2f}" for value in gross], padding=3, fontsize=8, color=INK)
    ax.bar_label(bars_net, labels=[f"{value:.2f}" for value in net], padding=3, fontsize=8, color=INK)
    ax.set_xticks(x, labels)
    ax.set_ylabel("SDS (kg/m³ feed)")
    ax.set_title("MEUF surfactant use", loc="left", fontweight="bold")
    ax.set_ylim(0, max(gross) * 1.22)
    style(ax, grid_axis="y")
    ax.legend(frameon=False, ncol=2, loc="upper left")
    ax.text(0.99, 0.98, f"CMC {cmc_mol_L * 1000:g} mmol/L · recovery {recovery:.1%}",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color=GREY)
    save(fig, "pr7_meuf_surfactant_use.png")


def meuf_sds_price_context_figure(parameters: list[dict[str, str]]):
    """Show public catalogue references without treating them as bulk prices."""
    selected = [
        row for row in parameters
        if row["parameter_id"] in {"MEUF_SDS_Price_20kg_Pack", "MEUF_SDS_Price_LabGrade"}
    ]
    labels = []
    values = []
    colors = []
    for row in selected:
        if row["parameter_id"] == "MEUF_SDS_Price_20kg_Pack":
            labels.append("Ph. Eur. · 20 kg pack")
            colors.append(BLUE)
        else:
            labels.append("Ultra-pure · 1 kg pack")
            colors.append(ROSE)
        values.append(float(row["value"]))
    fig, ax = plt.subplots(figsize=(7.2, 2.6), constrained_layout=True)
    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, height=0.38)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Listed price (€/kg)")
    ax.set_title("SDS price context", loc="left", fontweight="bold")
    ax.set_xlim(0, max(values) * 1.22)
    ax.bar_label(bars, labels=[f"€{value:,.2f}" for value in values], padding=4, fontsize=9, color=INK)
    style(ax)
    save(fig, "pr7_sds_price_context.png")


def parameter_readiness_figure(parameters: list[dict[str, str]]):
    """Split the input register into two readable, source-status panels."""
    rows = [row for row in parameters if row["model_use"] not in {"screening_tea_range", "screening_tea_nominal"}]
    rows.sort(key=lambda row: (row["membrane_class"], row["parameter_id"], row["component_target"]))
    midpoint = (len(rows) + 1) // 2
    for part, selected in enumerate((rows[:midpoint], rows[midpoint:]), start=1):
        states = [
            "excluded" if row["parameter_id"] == "Viscosity_Mu" and row["component_target"] == "Grass_Juice"
            else "not_required" if row["model_use"].startswith("not_required_")
            else "entered" if row["value"].strip() and row["source_status"] != "user_missing"
            else "gate"
            for row in selected
        ]
        labels = [f"{row['parameter_id']} · {row['component_target']} [{row['units']}]" for row in selected]
        fig_height = max(6.2, 0.34 * len(selected) + 1.5)
        fig, ax = plt.subplots(figsize=(8.0, fig_height))
        y = np.arange(len(selected))
        state_color = {"entered": GREEN, "gate": ROSE, "not_required": GREY, "excluded": GREY}
        ax.scatter([0.02] * len(states), y,
                   c=[state_color[state] for state in states], s=58, zorder=3)
        ax.set_yticks(y, labels)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.0)
        ax.set_xticks([])
        ax.tick_params(axis="y", labelsize=8.1, length=0, pad=8)
        for index, (row, state) in enumerate(zip(selected, states)):
            value = (
                "Excluded · fermented-juice value; no fermentation in PR7" if state == "excluded"
                else _readiness_value(row) if state == "entered"
                else "Not required if Cf/C0 ratio is given" if state == "not_required"
                else "Missing input"
            )
            if row["source_status"] == "equation_incomplete":
                value = "Equation needed before use"
            if state == "entered" and row["source_status"] == "official_reference_rate":
                value += " · official ref."
            elif state == "entered" and row["source_status"] == "indicative_internet_price_not_applied":
                value += " · ref. only"
            elif state == "entered" and row["source_status"] != "measured":
                value += " · unverified"
            ax.text(0.055, index, f"{state.replace('_', ' ').title()} · {value}",
                    va="center", fontsize=8.4, color=INK)
        ax.set_title(f"Membrane parameter readiness · {part}/2", loc="left", fontweight="bold")
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.subplots_adjust(left=0.48, right=0.98, top=0.92, bottom=0.04)
        save(fig, f"pr7_parameter_readiness_{part}.png")


def _readiness_value(row: dict[str, str]) -> str:
    """Format registered numbers compactly without altering stored precision."""
    raw = row["value"].strip()
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return raw
    units = row.get("units", "")
    if units == "EUR/USD":
        return f"{number:.4f}"
    if units.startswith("EUR/"):
        return f"{number:,.1f}"
    return f"{number:.3g}"


def model_mass_split_figure():
    """Simulate the configured no-fermentation PR7 route and plot its actual split."""
    from Greenhub.application.contracts.requests import (
        BiostimulantRouteOptions, SCHEMA_VERSION, ScenarioSelection, SimulationRequest,
    )
    from Greenhub.application.simulation_service import SimulationService
    from Greenhub.component_groups import COMPONENT_GROUPS
    from Greenhub.phase4_validation import PROTEIN_POOL_IDS
    from tempfile import TemporaryDirectory

    request = SimulationRequest(
        schema_version=SCHEMA_VERSION,
        request_id="pr7-figure-model-run",
        project_id="greenhub-report-figures",
        scenarios=ScenarioSelection(protein_recovery="PR7"),
        biostimulant_route=BiostimulantRouteOptions(
            technology_id="TUF",
            retention_matrix_source="GreenHub PR7 component co-retention register",
            flux_L_m2_h=22.0,
            flux_source="GreenHub PR7 supplied baseline TUF flux",
        ),
        strict_validation=False,
    )
    with TemporaryDirectory(prefix="greenhub-pr7-figure-") as temp_dir:
        service = SimulationService(run_root=Path(temp_dir))
        run_id = service.create_run(request)
        result = service.execute_run(run_id)

    streams = {alias: item for item in result.streams for alias in item.aliases}
    stream_aliases = (
        ("clarified_protein_rich_liquid", "Clarified juice"),
        ("biostimulant_product", "Retentate"),
        ("biostimulant_permeate", "Permeate"),
        ("biostimulant_unresolved", "Unresolved outlet"),
    )
    selected_streams = [(alias, label, streams[alias]) for alias, label in stream_aliases if alias in streams]
    unresolved_ids = set(streams.get("biostimulant_unresolved").components) if "biostimulant_unresolved" in streams else set()
    group_sets = [
        ("Hormones", set(COMPONENT_GROUPS["biostimulant_hormones"])),
        ("Protein", set(PROTEIN_POOL_IDS)),
        ("Peptides + amino acids", set(COMPONENT_GROUPS["peptides"] | COMPONENT_GROUPS["amino_acids"])),
        ("Sugars", set(COMPONENT_GROUPS["soluble_sugars"] | COMPONENT_GROUPS["entrapped_sugars"])),
        ("Salts + minerals", set(COMPONENT_GROUPS["dissolved_minerals"] | COMPONENT_GROUPS["major_cations"] | COMPONENT_GROUPS["major_anions"])),
        ("Structural + other organics", set(COMPONENT_GROUPS["structural_carbohydrates"] | COMPONENT_GROUPS["non_biodegradable_organics"] | {"Lipids", "OtherBiodegradableOrganics", "ParticulateBiodegradableOrganics", "SuspendedSolids"})),
    ]
    category_names = ["Water", *(name for name, _ in group_sets), "Other mapped", "Unresolved pools"]
    colors = {
        "Water": BLUE,
        "Hormones": ROSE,
        "Protein": GREEN,
        "Peptides + amino acids": YELLOW,
        "Sugars": SAND,
        "Salts + minerals": "#8b79b8",
        "Structural + other organics": GREY,
        "Other mapped": "#497277",
        "Unresolved pools": "#c65f57",
    }
    rows = []
    component_rows = []
    for alias, label, stream in selected_streams:
        amounts = {name: 0.0 for name in category_names}
        for component_id, value in stream.components.items():
            mass = float(value.value or 0.0)
            if alias == "biostimulant_unresolved" or component_id in unresolved_ids:
                category = "Unresolved pools"
            elif component_id == "Water":
                category = "Water"
            else:
                category = next((name for name, members in group_sets if component_id in members), "Other mapped")
            amounts[category] += mass
            component_rows.append((alias, label, component_id, category, mass))
        rows.append((alias, label, amounts, float(stream.total_mass.value or 0.0)))

    csv_path = OUT / "pr7_model_mass_split.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["stream_alias", "stream_label", "component_id", "category", "mass_kg_hr", "simulation_run_id", "scenario", "technology", "flux_L_m2_h", "fermentation"])
        for alias, label, component_id, category, mass in component_rows:
            writer.writerow([alias, label, component_id, category, f"{mass:.12g}", result.run_id, "PR7 full-plant structural steady-state", "TUF", 22, "excluded"])

    fig, (mass_ax, share_ax) = plt.subplots(1, 2, figsize=(7.5, 4.8), gridspec_kw={"width_ratios": [1.2, 1.0]})
    fig.subplots_adjust(left=0.22, right=0.98, bottom=0.34, top=0.83, wspace=0.5)
    positions = np.arange(len(rows))
    totals = [row[3] for row in rows]
    left_mass = np.zeros(len(rows))
    left_share = np.zeros(len(rows))
    for category in category_names:
        values = [row[2][category] for row in rows]
        shares = [100 * amount / total if total > 0 else 0 for amount, total in zip(values, totals)]
        mass_ax.barh(positions, values, left=left_mass, color=colors[category], label=category, height=0.64)
        share_ax.barh(positions, shares, left=left_share, color=colors[category], label=category, height=0.64)
        left_mass += np.asarray(values)
        left_share += np.asarray(shares)
    mass_ax.set_yticks(positions, [f"{label}\n{total:,.2f} kg/h" for (_, label, _, total) in rows])
    share_ax.set_yticks(positions, [label for _, label, _, _ in rows])
    mass_ax.invert_yaxis()
    share_ax.invert_yaxis()
    mass_ax.set_xlabel("Mass flow (kg/h)")
    share_ax.set_xlabel("Stream composition (%)")
    share_ax.set_xlim(left=0)
    share_ax.set_xlim(0, 100)
    mass_ax.set_title("Absolute flow", loc="left", fontweight="bold")
    share_ax.set_title("Outlet composition", loc="left", fontweight="bold")
    fig.suptitle("PR7 mass distribution", x=0.22, ha="left", fontsize=13, fontweight="bold", color=INK)
    for ax in (mass_ax, share_ax):
        style(ax, grid_axis="x")
        ax.tick_params(axis="y", length=0)
    handles, labels = mass_ax.get_legend_handles_labels()
    fig.legend(
        handles, labels, frameon=False, loc="lower center", ncol=2,
        bbox_to_anchor=(0.55, 0.005), fontsize=7.5, columnspacing=0.8,
        handletextpad=0.45, labelspacing=0.25,
    )
    save(fig, "pr7_model_mass_split.png")


def model_technology_comparison_figure():
    """Compare actual full-plant PR7 BioSTEAM outlet and area screens by membrane."""
    from Greenhub.application.contracts.requests import (
        BiostimulantRouteOptions, SCHEMA_VERSION, ScenarioSelection, SimulationRequest,
    )
    from Greenhub.application.simulation_service import SimulationService
    from tempfile import TemporaryDirectory

    records = []
    with TemporaryDirectory(prefix="greenhub-pr7-technology-figure-") as temp_dir:
        service = SimulationService(run_root=Path(temp_dir))
        for technology, flux in (("TUF", 22.0), ("LNF", 12.0), ("MEUF", 22.5)):
            request = SimulationRequest(
                schema_version=SCHEMA_VERSION,
                request_id=f"pr7-figure-{technology.lower()}",
                project_id="greenhub-pr7-technology-comparison",
                scenarios=ScenarioSelection(protein_recovery="PR7"),
                biostimulant_route=BiostimulantRouteOptions(
                    technology_id=technology,
                    retention_matrix_source="GreenHub PR7 component co-retention register",
                    flux_L_m2_h=flux,
                    flux_source="GreenHub PR7 supplied nominal membrane flux",
                ),
                strict_validation=False,
            )
            run_id = service.create_run(request)
            result = service.execute_run(run_id)
            streams = {alias: item for item in result.streams for alias in item.aliases}
            unit = next(item for item in result.units if item.unit_id == "PR7_M101")
            get_design = lambda name: unit.design_results[name].value
            maximum_area = get_design("Maximum membrane area")
            records.append({
                "technology": technology,
                "flux_L_m2_h": flux,
                "retentate_kg_h": float(streams["biostimulant_product"].total_mass.value or 0.0),
                "unresolved_kg_h": float(streams["biostimulant_unresolved"].total_mass.value or 0.0),
                "retentate_m3_h": get_design("Retentate volumetric flow"),
                "minimum_area_m2": float(get_design("Minimum membrane area") or 0.0),
                "maximum_area_m2": None if maximum_area is None else float(maximum_area),
                "mass_closure_error_kg_h": get_design("Mass closure error"),
                "validation_passed": result.validation.passed,
                "run_id": result.run_id,
            })

    with (OUT / "pr7_model_technology_comparison.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    technologies = [row["technology"] for row in records]
    x = np.arange(len(records))
    fig, (outlet_ax, area_ax) = plt.subplots(1, 2, figsize=(7.5, 4.8), constrained_layout=True)
    width = 0.34
    retentate = [row["retentate_kg_h"] for row in records]
    unresolved = [row["unresolved_kg_h"] for row in records]
    bars_product = outlet_ax.bar(x - width / 2, retentate, width, color=GREEN, label="Retentate")
    bars_unresolved = outlet_ax.bar(x + width / 2, unresolved, width, color=ROSE, label="Unresolved")
    outlet_ax.bar_label(bars_product, labels=[f"{v:.2f}" for v in retentate], padding=2, fontsize=7.5)
    outlet_ax.bar_label(bars_unresolved, labels=[f"{v:.2f}" for v in unresolved], padding=2, fontsize=7.5)
    outlet_ax.set_xticks(x, technologies)
    outlet_ax.set_ylabel("Outlet mass (kg/h)")
    outlet_ax.set_title("Outlet mass", loc="left", fontweight="bold")
    outlet_ax.set_ylim(0, max(retentate) * 1.20)
    outlet_ax.legend(frameon=False, loc="upper right")
    style(outlet_ax, grid_axis="y")

    minima = [row["minimum_area_m2"] for row in records]
    area_ax.bar(x, minima, color=BLUE, width=0.52)
    for index, row in enumerate(records):
        area_ax.text(index, row["minimum_area_m2"] * 1.03, f"≥{row['minimum_area_m2']:.1f}", ha="center", va="bottom", fontsize=7.5)
    area_ax.set_xticks(x, technologies)
    area_ax.set_ylabel("Known-stream area floor (m²)")
    area_ax.set_title("Area lower bound", loc="left", fontweight="bold")
    area_ax.set_ylim(0, max(minima) * 1.22)
    style(area_ax, grid_axis="y")
    fig.suptitle("PR7 membrane comparison", x=0.02, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.text(
        0.5, -0.015,
        "Full-plant steady-state · no pre-membrane fermentation · area floor covers mapped permeate; unresolved pools leave upper area unknown.",
        ha="center", va="top", fontsize=7.5, color=GREY,
    )
    save(fig, "pr7_model_technology_comparison.png")


def seasonal_operation_figure():
    """Show actual monthly PR7 production, unresolved mass and whole-plant utilities."""
    from Greenhub.application.contracts.requests import (
        BiostimulantRouteOptions, BiomassSchedule, SCHEMA_VERSION, ScenarioSelection, SimulationRequest,
    )
    from Greenhub.application.simulation_service import SimulationService
    from Greenhub.parameters.enums import ResolutionMode
    from tempfile import TemporaryDirectory

    request = SimulationRequest(
        schema_version=SCHEMA_VERSION,
        request_id="pr7-seasonal-profile",
        project_id="greenhub-pr7-seasonal-figure",
        scenarios=ScenarioSelection(protein_recovery="PR7"),
        resolution_mode=ResolutionMode.QUASI_DYNAMIC,
        start_date="2026-01-01",
        end_date="2026-12-31",
        time_step="monthly",
        biomass_schedule=BiomassSchedule(),
        biostimulant_route=BiostimulantRouteOptions(
            technology_id="TUF",
            retention_matrix_source="GreenHub PR7 component co-retention register",
            flux_L_m2_h=22.0,
            flux_source="GreenHub PR7 supplied nominal TUF flux",
        ),
        strict_validation=False,
    )
    with TemporaryDirectory(prefix="greenhub-pr7-seasonal-figure-") as temp_dir:
        service = SimulationService(run_root=Path(temp_dir))
        run_id = service.create_run(request)
        result = service.execute_run(run_id)

    throughput = {str(row["time"]): row for row in result.throughput_series}
    product = {str(row["time"]): row for row in result.product_series}
    utility = {str(row["time"]): row for row in result.utility_series}
    months = [str(row["time"]) for row in result.product_series]
    records = []
    for month in months:
        t = throughput.get(month, {})
        p = product.get(month, {})
        u = utility.get(month, {})
        products = p.get("products_kg", {})
        volumes = p.get("volumetric_products_m3", {})
        records.append({
            "month": month,
            "wet_grass_processed_t": float(t.get("actual_throughput_kg", 0.0) or 0.0) / 1000.0,
            "wet_retentate_t": float(products.get("biostimulant_product", 0.0) or 0.0) / 1000.0,
            "unresolved_mass_t": float(p.get("pr7_unresolved_mass_kg", 0.0) or 0.0) / 1000.0,
            "membrane_feed_volume_m3": float(p.get("pr7_feed_volume_m3", 0.0) or 0.0),
            "retentate_volume_m3": float(volumes.get("biostimulant_product", 0.0) or 0.0),
            "whole_plant_electricity_mwh": float(u.get("electricity_kwh", 0.0) or 0.0) / 1000.0,
            "whole_plant_heat_mwh": float(u.get("heating_kwh", 0.0) or 0.0) / 1000.0,
            "whole_plant_cooling_mwh": float(u.get("cooling_kwh", 0.0) or 0.0) / 1000.0,
            "simulation_run_id": result.run_id,
            "validation_passed": result.validation.passed,
        })

    csv_path = OUT / "pr7_seasonal_operating_profile.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    fig, axes = plt.subplots(2, 2, figsize=(7.8, 6.2))
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.11, top=0.84, wspace=0.30, hspace=0.42)
    month_labels = [row["month"][5:] for row in records]
    x = np.arange(len(records))
    width = 0.36

    feed = [row["wet_grass_processed_t"] for row in records]
    axes[0, 0].bar(x, feed, color=BLUE, width=0.68)
    axes[0, 0].set_title("Feed throughput", loc="left", fontweight="bold", fontsize=10)
    axes[0, 0].set_ylabel("Grass (t/month)")

    retentate = [row["wet_retentate_t"] for row in records]
    unresolved = [row["unresolved_mass_t"] for row in records]
    axes[0, 1].bar(x - width / 2, retentate, color=GREEN, width=width, label="Wet retentate")
    axes[0, 1].bar(x + width / 2, unresolved, color=ROSE, width=width, label="Unresolved mass")
    axes[0, 1].set_title("Membrane outlets", loc="left", fontweight="bold", fontsize=10)
    axes[0, 1].set_ylabel("Mass (t/month)")
    axes[0, 1].set_ylim(0, max(max(retentate, default=0.0), max(unresolved, default=0.0), 1e-9) * 1.45)
    axes[0, 1].legend(frameon=True, framealpha=0.92, edgecolor="none", fontsize=7, ncol=2, loc="upper left")

    feed_volume = [row["membrane_feed_volume_m3"] for row in records]
    retentate_volume = [row["retentate_volume_m3"] for row in records]
    axes[1, 0].bar(x - width / 2, feed_volume, color=BLUE, width=width, label="Membrane feed")
    axes[1, 0].bar(x + width / 2, retentate_volume, color=GREEN, width=width, label="Retentate")
    axes[1, 0].set_title("Liquid volume", loc="left", fontweight="bold", fontsize=10)
    axes[1, 0].set_ylabel("Volume (m³/month)")
    axes[1, 0].set_ylim(0, max(max(feed_volume, default=0.0), max(retentate_volume, default=0.0), 1e-9) * 1.45)
    axes[1, 0].legend(frameon=True, framealpha=0.92, edgecolor="none", fontsize=7, ncol=2, loc="upper left")

    electricity = np.asarray([row["whole_plant_electricity_mwh"] for row in records])
    heat = np.asarray([row["whole_plant_heat_mwh"] for row in records])
    cooling = np.asarray([row["whole_plant_cooling_mwh"] for row in records])
    axes[1, 1].bar(x, electricity, color=BLUE, width=0.68, label="Electricity")
    axes[1, 1].bar(x, heat, bottom=electricity, color=YELLOW, width=0.68, label="Heat")
    axes[1, 1].bar(x, cooling, bottom=electricity + heat, color=ROSE, width=0.68, label="Cooling")
    axes[1, 1].set_title("Whole-plant utilities", loc="left", fontweight="bold", fontsize=10)
    axes[1, 1].set_ylabel("Energy (MWh/month)")
    total_utility = electricity + heat + cooling
    axes[1, 1].set_ylim(0, max(float(total_utility.max(initial=0.0)), 1e-9) * 1.45)
    axes[1, 1].legend(frameon=True, framealpha=0.92, edgecolor="none", fontsize=7, ncol=3, loc="upper left")

    for ax in axes.flat:
        ax.set_xticks(x, month_labels)
        ax.set_xlim(-0.55, len(x) - 0.45)
        style(ax, grid_axis="y")
        ax.tick_params(axis="x", labelsize=8, length=0)
    fig.suptitle(
        "PR7 seasonal profile",
        x=0.05, y=0.975, ha="left", fontsize=13, fontweight="bold", color=INK,
    )
    fig.text(
        0.05, 0.925,
        "Default biomass schedule · TUF · no pre-membrane fermentation",
        ha="left", va="top", fontsize=8, color=GREY,
    )
    save(fig, "pr7_seasonal_operating_profile.png")


def membrane_lca_reference_figure():
    """Keep incompatible published membrane GWP functional units separate."""
    rows = read_rows("biostimulant_membrane_lca_references.csv")
    area_rows = [row for row in rows if row["normalized_GWP_kg_CO2e_per_m2"]]
    module_rows = [row for row in rows if row["reported_GWP_kg_CO2e_per_module"]]
    fig, axes = plt.subplots(1, 2, figsize=(7.7, 3.8), constrained_layout=True)

    area_values = [float(row["normalized_GWP_kg_CO2e_per_m2"]) for row in area_rows]
    area_labels = [f"{row['polymer']} / {row['solvent']}" for row in area_rows]
    axes[0].barh(np.arange(len(area_rows)), area_values, color=[GREY, SAND][:len(area_rows)], height=0.68)
    axes[0].set_yticks(np.arange(len(area_rows)), area_labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("kg CO₂-eq/m²")
    axes[0].set_title("Hollow-fiber fabrication", loc="left", fontweight="bold")
    for i, value in enumerate(area_values):
        axes[0].text(value + max(area_values) * 0.035, i, f"{value:g}", va="center", fontsize=9, color=INK)
    axes[0].set_xlim(0, max(area_values) * 1.28)
    style(axes[0])

    module_values = [float(row["reported_GWP_kg_CO2e_per_module"]) for row in module_rows]
    module_labels = ["NF · PA-TFC", "UF · polymeric"]
    axes[1].barh(np.arange(len(module_rows)), module_values, color=[BLUE, GREEN][:len(module_rows)], height=0.68)
    axes[1].set_yticks(np.arange(len(module_rows)), module_labels)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("kg CO₂-eq/module")
    axes[1].set_title("Spiral-wound module", loc="left", fontweight="bold")
    for i, value in enumerate(module_values):
        axes[1].text(value + max(module_values) * 0.035, i, f"{value:g}", va="center", fontsize=9, color=INK)
    axes[1].set_xlim(0, max(module_values) * 1.28)
    style(axes[1])

    fig.suptitle("Membrane GWP references", x=0.02, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.text(
        0.5, -0.02,
        "Different materials, geometries and scopes; reference context only, excluded from PR7 LCA totals.",
        ha="center", va="center", fontsize=7.8, color=GREY,
    )
    save(fig, "pr7_membrane_lca_reference_context.png")


def write_index():
    sources = {
        "pr7_hormone_content_split.png": (
            "Hormone concentration separated by supplied free/bound fractions",
            "biostimulant_hormone_benchmarks.csv; Bákonyi et al. 2025, DOI 10.1038/s41598-025-03896-7",
            "User-supplied PR7 clarified-grass-juice screen; free/bound split is described for a 14-day anaerobic state and is unvalidated for this no-fermentation feed; alfalfa brown-juice IAA is contextual only",
            "concentration: µg/L clarified juice",
        ),
        "pr7_hormone_retention.png": (
            "Weighted analyte retention; TUF free-state uses sigma/Peclet at nominal flux",
            "biostimulant_hormone_benchmarks.csv; Bákonyi et al. 2025, DOI 10.1038/s41598-025-03896-7",
            "PR7 user-supplied clarified-grass-juice screening retention; free/bound split is described for a 14-day anaerobic state and unvalidated here; MEUF generic midpoint",
            "retention: %",
        ),
        "pr7_retention_model_check.png": (
            "Free-state retention factors compared with sigma/Peclet predictions at nominal TUF/LNF fluxes",
            "biostimulant_hormone_benchmarks.csv; biostimulant_membrane_gated_parameters.csv; calculate_film_retention",
            "TUF free-state prediction drives the split; LNF film result is diagnostic; bound prediction gated by missing diffusivity",
            "retention: %; flux: L/(m²·h); Peclet: dimensionless",
        ),
        "pr7_hormone_capture_by_technology.png": (
            "Free and bound captured IAA, zeatin and zeatin-riboside equivalents by membrane option, normalized to 1,000 m³ clarified juice",
            "biostimulant_hormone_benchmarks.csv; Bákonyi et al. 2025, DOI 10.1038/s41598-025-03896-7",
            "PR7 no-fermentation screen; free/bound split is described for a 14-day anaerobic state and unvalidated for clarified fresh juice; cytokinin concentrations are user-supplied; TUF free-state uses sigma/Peclet; MEUF generic midpoint",
            "captured analyte: mg per 1,000 m³ feed",
        ),
        "pr7_membrane_design_ranges.png": (
            "Supplied membrane-option ranges plus a measured grass-juice flux and pressure comparator on a different 60 nm membrane",
            "biostimulant_membrane_options.csv; flux_time_series.csv",
            "PR7 user-supplied membrane ranges; separate direct clover-grass 60 nm UF comparator, not transferred to TUF",
            "flux: L/(m²·h); TMP: bar; module price: EUR/m² (converted from USD); scaling exponent: dimensionless",
        ),
        "pr7_component_coretention.png": (
            "Nominal co-retention by membrane option; MEUF class values are unavailable; water hold-up is derived from target VCF 10",
            "biostimulant_membrane_component_retention.csv",
            "PR7 screening matrix; MEUF protein/peptide/sugar/salt retentions are missing; water hold-up from VCF=10; solids assumed retained",
            "retained fraction: dimensionless",
        ),
        "pr7_protein_retention_evidence.png": (
            "User-supplied PR7 crude-protein co-retention beside a direct grass-juice 60 nm UF literature comparator",
            "biostimulant_membrane_component_retention.csv; biostimulant_unmapped_pool_evidence.csv",
            "PR7 supplied TUF/LNF screening assumptions compared with fresh clover-grass juice 60 nm UF; different membrane and feed, context only",
            "crude protein rejection: %",
        ),
        "pr7_membrane_replacement_cost.png": (
            "Supplied membrane module purchase ranges and deterministic annual replacement allowance using the stated lifetime bounds",
            "biostimulant_membrane_options.csv; biostimulant_membrane_gated_parameters.csv",
            "PR7 user-supplied module price and 2.5–3.0 year lifetime ranges",
            "module: EUR/m²; replacement allowance: EUR/(m²·year); ECB rate dated 2026-11-02",
        ),
        "pr7_capital_reference_context.png": (
            "Contextual EUR investment ranges for grass-biorefinery modules beside PR7 membrane-media prices; no analog is scaled into the model",
            "biostimulant_membrane_cost_references.csv; biostimulant_membrane_options.csv",
            "RISE 2024 press module and public Grassa investment analogs have different scopes; PR7 prices are user-supplied module media quotes converted to EUR",
            "grass-biorefinery context: EUR per reported module/complex; PR7 membrane media: EUR/m²",
        ),
        "pr7_cip_frequency_context.png": (
            "User-supplied 48 operating-hour screen beside Dutch full-scale water NF and RO case frequencies",
            "biostimulant_membrane_gated_parameters.csv; biostimulant_cip_evidence.csv",
            "PR7 frequency at 8,760 operating h/year; Dutch drinking-water NF and RO literature comparators, not transferable to grass juice",
            "CIP events/year",
        ),
        "pr7_cip_reagent_climate_factors.png": (
            "Opt-in upstream climate-factor intensities for active NaOH and citric-acid CIP reagents; no annual chemical activity is assumed",
            "Greenhub.application.lca_service.screening_lca_factors; biostimulant_chemical_lca_factors.csv",
            "PR7 screening climate factors; Euro Chlor European average and Citribel Belgian producer proxy; GWP vintage differs from IPCC AR6 utilities",
            "kg CO₂-eq/kg active reagent",
        ),
        "pr7_meuf_surfactant_use.png": (
            "Gross SDS dose and unrecovered make-up per clarified-juice volume using the supplied CMC, dose range and recovery",
            "biostimulant_membrane_gated_parameters.csv; PubChem SDS molecular weight",
            "PR7 MEUF screening basis; 8 mmol/L CMC, 1.2–1.5× dose and 94.5% recovery; material screen only",
            "kg SDS/m³ feed",
        ),
        "pr7_sds_price_context.png": (
            "Public SDS price references by listed grade and pack size; neither is applied to PR7 TEA",
            "biostimulant_membrane_gated_parameters.csv; biostimulant_membrane_cost_references.csv",
            "EUR catalog references accessed 2026-11-03; Ph. Eur. 20 kg listing and 1 kg ultra-pure laboratory listing; no process-grade bulk quote",
            "listed price: EUR/kg",
        ),
        "pr7_parameter_readiness_1.png": (
            "Entered, missing and conditionally unnecessary PR7 parameters, first half; no values imputed",
            "biostimulant_membrane_gated_parameters.csv",
            "PR7 model-input readiness register; pre-membrane fermentation excluded",
            "parameter value with source-status label; units shown per row",
        ),
        "pr7_parameter_readiness_2.png": (
            "Entered, missing and conditionally unnecessary PR7 parameters, second half; no values imputed",
            "biostimulant_membrane_gated_parameters.csv",
            "PR7 model-input readiness register; pre-membrane fermentation excluded",
            "parameter value with source-status label; units shown per row",
        ),
        "pr7_model_mass_split.png": (
            "BioSTEAM full-route clarified-juice mass by component class through retentate, permeate and unresolved outlets",
            "GreenHub SimulationService result; biostimulant_membrane_component_retention.csv",
            "PR7 structural steady-state, no pre-membrane fermentation; TUF at 22 L/(m²·h); unresolved pools preserved without imputed retention",
            "absolute flow: kg/h; composition: %",
        ),
        "pr7_model_technology_comparison.png": (
            "Actual BioSTEAM retentate/unresolved outlet masses and known-stream membrane area floors from separate full-plant PR7 runs",
            "GreenHub SimulationService results; biostimulant_membrane_component_retention.csv; biostimulant_membrane_options.csv",
            "PR7 steady-state no-fermentation TUF/LNF/MEUF comparison; same upstream model; nominal supplied fluxes; incomplete component-fate gates remain active",
            "outlet mass: kg/h; retentate volume: m³/h; known-stream membrane area floor: m²; flux: L/(m²·h)",
        ),
        "pr7_seasonal_operating_profile.png": (
            "Actual monthly PR7 feed throughput, wet retentate, unresolved mass, membrane volumes, and whole-plant utility demand",
            "GreenHub monthly SimulationService result; default BiomassSchedule; biostimulant_membrane_component_retention.csv",
            "PR7 monthly quasi-dynamic run, 2026 default biomass schedule; TUF at 22 L/(m²·h); strict validation disabled to preserve and display unresolved pools; no pre-membrane fermentation",
            "grass, retentate and unresolved mass: t/month; liquid volume: m³/month; utilities: MWh/month",
        ),
        "pr7_membrane_lca_reference_context.png": (
            "Published polymeric-membrane fabrication and module GWP values shown in separate functional-unit panels",
            "biostimulant_membrane_lca_references.csv; Yadav et al. 2021; Urper-Bayram et al. 2022 review",
            "Reference-only literature systems; materials, geometry and scopes differ from PR7 PES-TUF and PA-TFC-LNF; excluded from model totals",
            "left: kg CO₂-eq/m² hollow-fiber fabrication; right: kg CO₂-eq/module spiral-wound reference",
        ),
    }
    new_rows = []
    with INDEX.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["figure_name", "description", "source_dataset", "scenario", "units", "file_location"])
        for filename, values in sources.items():
            row = [filename.removesuffix(".png"), *values, f"results/report_figures/12_biostimulant_screening/{filename}"]
            writer.writerow(row)
            new_rows.append(dict(zip(["figure_name", "description", "source_dataset", "scenario", "units", "file_location"], row)))

    # Keep the repository-wide index intact and replace only rows with these figure names.
    existing = []
    fields = ["figure_name", "description", "source_dataset", "scenario", "units", "file_location"]
    if MASTER_INDEX.exists():
        with MASTER_INDEX.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or fields
            replaced_names = {item["figure_name"] for item in new_rows} | {"pr7_parameter_readiness"}
            existing = [row for row in reader if row.get("figure_name") not in replaced_names]
    existing.extend(new_rows)
    with MASTER_INDEX.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing)


def write_readme():
    (OUT / "README.md").write_text(
        "# PR7 biostimulant screening figures\n\n"
        "Benchmark PNGs visualize supplied hormone and membrane tables and are screening inputs, not full-route results. "
        "The cited 2025 alfalfa brown-juice paper reports non-fermented IAA in a different stream; it does not validate the PR7 clarified-grass-juice concentrations or free/bound fractions, and it did not assess cytokinins. Those remain user-supplied screening values. The supplied free/bound fractions are discussed in a 14-day anaerobic context and are unvalidated for the current no-fermentation PR7 boundary. "
        "The PR7 mass-distribution PNG is generated from an actual BioSTEAM SimulationService run; it shows the clarified-juice "
        "mass split and explicit unresolved outlet. The technology-comparison PNG and CSV contain separate actual full-plant "
        "TUF, LNF and MEUF runs, including unresolved outlets and the known-permeate area floor. The seasonal-operation PNG and CSV "
        "come from a 12-month quasi-dynamic PR7 run and report actual modelled monthly feed, product, unresolved, volume, and utility flows. "
        "The membrane feed boundary is clarified "
        "grass juice with no 14-day pre-membrane fermentation/storage; downstream digestion remains controlled by the separate AD scenario. MEUF hormone retention is shown using the generic "
        "midpoint specified in the supplied data. TUF free-hormone retention uses the sigma/Peclet estimate at the nominal 22 L/(m²·h) flux, while TUF bound and LNF free/bound retentions use registered state-specific screening factors. Water hold-up is derived from the target VCF=10 to form a liquid retentate; it is not a measured membrane rejection.\n\n"
        "Regenerate with `.venv/Scripts/python.exe scripts/generate_biostimulant_figures.py`. "
        "Each PNG is exported at 300 DPI; figure dimensions are approximately 2400 px wide. The SDS price-context figure shows public catalog references only; they are excluded from process TEA. "
        "The capital-reference chart separates contextual grass-biorefinery investments from the PR7 membrane-media price basis; none of the analogs are used in modeled CAPEX. "
        "The membrane-GWP reference chart separates kg CO₂-eq/m² hollow-fiber fabrication values from kg CO₂-eq/module spiral-wound analogs; both are excluded from modeled LCA totals because materials, geometry and inventories do not match PR7. "
        "The local and report-wide figure indexes are updated reproducibly.\n",
        encoding="utf-8",
    )


def main():
    # Remove the superseded single-panel readiness image so regeneration does
    # not leave an unindexed stale chart beside the split versions.
    (OUT / "pr7_parameter_readiness.png").unlink(missing_ok=True)
    hormones = read_rows("biostimulant_hormone_benchmarks.csv")
    options = read_rows("biostimulant_membrane_options.csv")
    flux_records = read_rows("flux_time_series.csv")
    retentions = read_rows("biostimulant_membrane_component_retention.csv")
    parameters = read_rows("biostimulant_membrane_gated_parameters.csv")
    cip_evidence = read_rows("biostimulant_cip_evidence.csv")
    hormone_content_figure(hormones)
    hormone_retention_figure(hormones)
    film_retention_check_figure(hormones)
    hormone_capture_figure(hormones)
    membrane_windows_figure(options, flux_records)
    component_retention_figure(retentions)
    protein_retention_evidence_figure()
    replacement_cost_figure(options)
    capital_reference_figure(options)
    cip_frequency_figure(cip_evidence, parameters)
    cip_lca_factor_figure()
    meuf_surfactant_figure(parameters)
    meuf_sds_price_context_figure(parameters)
    parameter_readiness_figure(parameters)
    model_mass_split_figure()
    model_technology_comparison_figure()
    seasonal_operation_figure()
    membrane_lca_reference_figure()
    write_index()
    write_readme()
    print(f"Generated 16 PR7 screening/context figures and 3 BioSTEAM model figures in {OUT}")


if __name__ == "__main__":
    main()

