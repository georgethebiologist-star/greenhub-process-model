"""Generate comparison and correlation figures for the current KPI-table candidates."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Greenhub" / "results" / "pareto_rvo_2026" / "latest.json"
OUT = ROOT / "results" / "report_figures" / "11_kpi_candidate_correlations"
OUT.mkdir(parents=True, exist_ok=True)

BG = "#efebe6"
INK = "#0c3338"
GREEN = "#408f4d"
BLUE = "#729ad2"
YELLOW = "#d1a520"
ROSE = "#d277a3"
GREY = "#8d9996"
CASE_COLORS = {"C30": BLUE, "C45": GREEN, "C60": YELLOW, "C0": ROSE}
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
    "ytick.color": INK, "axes.edgecolor": INK, "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 15, "axes.labelsize": 12,
    "legend.fontsize": 9, "figure.dpi": 300, "savefig.dpi": 300,
})

BASELINE = [
    {"feed":1000,"npv":-4146509,"carbon":-139.20,"label":"Baseline"},
    {"feed":5000,"npv":-4845145,"carbon":-696.27,"label":"Baseline"},
    {"feed":10000,"npv":-5634749,"carbon":-1392.70,"label":"Baseline"},
    {"feed":20000,"npv":-7128698,"carbon":-2785.65,"label":"Baseline"},
    {"feed":30000,"npv":-8570081,"carbon":-4178.66,"label":"Baseline"},
]
BANDS = [(5000,10000,"5–10k"),(10000,15000,"10–15k"),(15000,20000,"15–20k"),(20000,25000,"20–25k"),(25000,30001,"25–30k")]


def metric(row, name):
    return float(row["objectives"][name]["value"])


def feed_t(row):
    return float(row["annual"]["feed_processed"]["value"]) / 1000.0


def by_id(data):
    return {row["sample_id"]: row for group in data["groups_payload"].values() for row in group["samples"]}


def select_candidates(data):
    rows = [row for group in data["groups_payload"].values() for row in group["samples"]
            if row.get("status") == "evaluated" and not row.get("baseline_reference")
            and metric(row, "npv") > 0]
    selected = {}
    for low, high, band in BANDS:
        subset = [row for row in rows if low <= feed_t(row) < high]
        if not subset:
            continue
        picks = (
            ("Highest NPV", max(subset, key=lambda row: metric(row, "npv"))),
            ("Lowest support", min(subset, key=lambda row: metric(row, "subsidy_granted"))),
            ("Lowest net carbon", min(subset, key=lambda row: metric(row, "net_carbon"))),
        )
        for tag, row in picks:
            labels = selected.setdefault(row["sample_id"], {"row": row, "band": band, "tags": []})
            labels["tags"].append(tag)
    return list(selected.values())


def axes_style(ax):
    ax.grid(axis="both", color="#aebbb6", alpha=.22, linewidth=.55)
    ax.spines[["top", "right"]].set_visible(False)


def save(fig, name):
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    all_rows = [row for group in data["groups_payload"].values() for row in group["samples"]
                if row.get("status") == "evaluated" and not row.get("baseline_reference")]
    selected = select_candidates(data)

    # Selected alternatives against the five no-support baseline scales.
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))
    ax = axes[0]
    ax.plot([r["feed"] for r in BASELINE], [r["npv"]/1e6 for r in BASELINE],
            color=INK, marker="o", linewidth=1.8, label="Baseline")
    markers = {"Highest NPV":"^", "Lowest support":"s", "Lowest net carbon":"D"}
    colors = {"Highest NPV":BLUE, "Lowest support":GREEN, "Lowest net carbon":ROSE}
    shown = set()
    for item in selected:
        row = item["row"]
        for tag in item["tags"]:
            ax.scatter(feed_t(row), metric(row,"npv")/1e6, marker=markers[tag], s=88,
                       color=colors[tag], edgecolor="white", linewidth=.8, zorder=4,
                       label=tag if tag not in shown else "")
            shown.add(tag)
    ax.axhline(0, color=INK, linewidth=.8)
    ax.set_xlabel("Wet grass (t/year)"); ax.set_ylabel("NPV (€ million)")
    ax.set_title("NPV by scale", loc="left", fontweight="bold"); axes_style(ax)

    ax = axes[1]
    ax.plot([r["feed"] for r in BASELINE], [r["carbon"] for r in BASELINE],
            color=INK, marker="o", linewidth=1.8, label="Baseline")
    shown = set()
    for item in selected:
        row = item["row"]
        for tag in item["tags"]:
            ax.scatter(feed_t(row), metric(row,"net_carbon"), marker=markers[tag], s=88,
                       color=colors[tag], edgecolor="white", linewidth=.8, zorder=4,
                       label=tag if tag not in shown else "")
            shown.add(tag)
    ax.set_xlabel("Wet grass (t/year)"); ax.set_ylabel("Net carbon (t C/year)")
    ax.set_title("Net carbon by scale", loc="left", fontweight="bold"); axes_style(ax)
    fig.suptitle("Baseline and selected candidates", x=.07, ha="left", fontweight="bold", fontsize=17)
    handles=[
        Line2D([0],[0],color=INK,marker="o",lw=1.6,label="Baseline"),
        Line2D([0],[0],color=BLUE,marker="^",lw=0,label="Highest NPV"),
        Line2D([0],[0],color=GREEN,marker="s",lw=0,label="Lowest support"),
        Line2D([0],[0],color=ROSE,marker="D",lw=0,label="Lowest net carbon"),
    ]
    fig.legend(handles=handles,frameon=False,ncols=4,loc="upper center",bbox_to_anchor=(.54,.91))
    fig.tight_layout(rect=(0,0,1,.87))
    save(fig,"baseline_and_candidate_kpis_by_scale.png")

    # Sampled trade-off between positive/negative NPV and present-value support.
    fig, ax = plt.subplots(figsize=(8.5,6.2))
    for case, color in CASE_COLORS.items():
        subset = [r for r in all_rows if r["support_case"] == case]
        ax.scatter([metric(r,"subsidy_granted")/1e6 for r in subset],
                   [metric(r,"npv")/1e6 for r in subset], s=20, alpha=.22,
                   color=color, edgecolor="none", label=case)
    ax.scatter([0]*len(BASELINE), [r["npv"]/1e6 for r in BASELINE], marker="*", s=100,
               color=INK, label="Baseline", zorder=5)
    for item in selected:
        row=item["row"]
        ax.scatter(metric(row,"subsidy_granted")/1e6,metric(row,"npv")/1e6,
                   s=115,marker="o",facecolor="none",edgecolor=INK,linewidth=1.25,zorder=6)
    ax.axhline(0,color=INK,linewidth=.8)
    ax.set_xlabel("Total support PV (€ million) · minimize")
    ax.set_ylabel("NPV (€ million) · maximize")
    ax.set_title("NPV and support trade-off",loc="left",fontweight="bold")
    axes_style(ax); ax.legend(frameon=False,ncols=3)
    ax.text(.01,.015,"All sampled designs shown; outlined points are the scale-band selections.",
            transform=ax.transAxes,fontsize=8,color=INK,ha="left",va="bottom")
    fig.tight_layout()
    save(fig,"pareto_npv_vs_support_pv.png")

    # Throughput correlations with four decision-relevant outputs.
    panels = [
        ("npv", "NPV (€ million)", lambda r: metric(r,"npv")/1e6),
        ("carbon", "Net carbon (t C/year)", lambda r: metric(r,"net_carbon")),
        ("biomethane", "Biomethane (Nm³/year)", lambda r: float(r.get("biomethane_support",{}).get("biomethane_nm3_per_year",0))),
        ("support", "Total support PV (€ million)", lambda r: metric(r,"subsidy_granted")/1e6),
    ]
    fig, axes = plt.subplots(2,2,figsize=(12,8.4))
    for ax,(key,label,get_y) in zip(axes.ravel(),panels):
        y=np.array([get_y(r) for r in all_rows],dtype=float)
        x=np.array([feed_t(r) for r in all_rows],dtype=float)
        rho=float(spearmanr(x,y).statistic) if len(x)>1 else float("nan")
        for case,color in CASE_COLORS.items():
            mask=np.array([r["support_case"]==case for r in all_rows])
            ax.scatter(x[mask],y[mask],s=12,alpha=.22,color=color,edgecolor="none",label=case)
        ax.set_xlabel("Wet grass (t/year)");ax.set_ylabel(label)
        ax.set_title(f"Throughput vs {key.replace('_',' ')}",loc="left",fontweight="bold")
        ax.text(.98,.97,f"Spearman ρ = {rho:.2f}",transform=ax.transAxes,ha="right",va="top",
                fontsize=9,bbox={"facecolor":BG,"edgecolor":"none","alpha":.85})
        axes_style(ax)
    fig.suptitle("Scale correlations across sampled routes",x=.07,ha="left",fontweight="bold",fontsize=17)
    handles=[Line2D([0],[0],marker="o",linestyle="none",color=color,label=case) for case,color in CASE_COLORS.items()]
    fig.legend(handles=handles,frameon=False,ncols=4,loc="upper center",bbox_to_anchor=(.55,.93))
    fig.tight_layout(rect=(0,0,1,.88))
    save(fig,"throughput_kpi_correlations.png")

    # Spearman matrix across candidate route/support combinations.
    vars_ = [
        ("Wet grass",lambda r:feed_t(r)),
        ("Revenue",lambda r:float(r["tea_totals"].get("annual_revenue_eur") or 0)),
        ("Partial profit",lambda r:float(r["tea_totals"].get("partial_operating_margin_eur_per_year") or 0)),
        ("NPV",lambda r:metric(r,"npv")),
        ("Support PV",lambda r:metric(r,"subsidy_granted")),
        ("Biomethane",lambda r:float(r.get("biomethane_support",{}).get("biomethane_nm3_per_year",0))),
        ("Net carbon",lambda r:metric(r,"net_carbon")),
    ]
    matrix=np.array([[fn(r) for _,fn in vars_] for r in all_rows],dtype=float)
    corr=np.empty((len(vars_),len(vars_)))
    for i in range(len(vars_)):
        for j in range(len(vars_)):
            corr[i,j]=spearmanr(matrix[:,i],matrix[:,j]).statistic
    fig,ax=plt.subplots(figsize=(9,7.2))
    im=ax.imshow(corr,cmap="RdYlBu_r",vmin=-1,vmax=1)
    labels=[name for name,_ in vars_]
    ax.set_xticks(range(len(labels)),labels,rotation=35,ha="right")
    ax.set_yticks(range(len(labels)),labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j,i,f"{corr[i,j]:.2f}",ha="center",va="center",fontsize=8,color=INK)
    ax.set_title("KPI rank correlations",loc="left",fontweight="bold")
    cb=fig.colorbar(im,ax=ax,fraction=.04,pad=.03);cb.set_label("Spearman ρ")
    fig.tight_layout()
    save(fig,"candidate_kpi_spearman_matrix.png")

    print(f"Generated 4 PNGs in {OUT}; selected positive-NPV candidates: {len(selected)}; sampled candidate-case rows: {len(all_rows)}")


if __name__ == "__main__":
    main()
