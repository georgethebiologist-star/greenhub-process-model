"""Generate dimensionally consistent SVG/PNG figures from saved model runs."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
BG, INK, GREEN, BLUE, YELLOW, ROSE = "#efebe6", "#0c3338", "#408f4d", "#729ad2", "#d1a520", "#d277a3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 15,
                     "axes.labelcolor": INK, "text.color": INK, "axes.edgecolor": INK,
                     "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})
baseline = json.loads((ROOT / "baseline_report.json").read_text(encoding="utf-8"))
with (ROOT / "route_comparison.csv").open(encoding="utf-8-sig", newline="") as f:
    routes = list(csv.DictReader(f))
labels = ["No targeted recovery", "P only", "N only", "P and N"]
order = [routes[1], routes[2], routes[3], routes[0]]
catalog = []

def save(fig, name, title, purpose, source, kpi, section):
    fig.tight_layout(pad=1.7)
    for ext in ("svg", "png"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)
    catalog.append({"figure_id": f"F{len(catalog)+1}", "title": title, "research_purpose": purpose,
                    "data_source": source, "kpi": kpi, "suggested_section": section,
                    "file_location": str(FIG / f"{name}.svg")})

def hbar(name, title, labs, vals, unit, purpose, source, section, color=GREEN):
    fig, ax = plt.subplots(figsize=(10, max(4, 0.55*len(labs)+1.4)))
    ax.barh(labs, vals, color=color)
    ax.invert_yaxis(); ax.set_xlabel(unit); ax.set_title(title, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    save(fig, name, title, purpose, source, unit, section)

products = baseline["annual"]["products"]
solid_keys = ["dry_protein_product", "phosphorus_product", "ammonium_product", "nutrient_rich_solids"]
hbar("baseline_products", "Annual solid products", ["Dry protein product", "Phosphorus stream", "Ammonium stream", "Nutrient rich solids"],
     [products[k]["value"]/1000 for k in solid_keys], "t/y (reported stream mass)", "Compare baseline product streams; wet product identity is not purity", "baseline_report.json", "Results 6.2")

stages = baseline["annual"]["process_pathway"]
hbar("electricity_by_stage", "Electricity by stage", [s["label"] for s in stages if s.get("power_kw") is not None],
     [s["power_kw"]*8760/1000 for s in stages if s.get("power_kw") is not None], "MWh/y", "Locate electrical demand", "baseline_report.json annual.process_pathway", "Results 6.2", BLUE)

fig, ax = plt.subplots(figsize=(10, 5))
x = list(range(4)); width=.35
ax.bar([v-width/2 for v in x], [float(r["electricity_kwh_year"])/1000 for r in order], width, label="Electricity", color=BLUE)
ax.bar([v+width/2 for v in x], [float(r["heating_kwh_year"])/1000 for r in order], width, label="Heating", color=ROSE)
ax.set_xticks(x, labels, rotation=15, ha="right"); ax.set_ylabel("MWh/y"); ax.set_title("Route utility demand", loc="left")
ax.legend(frameon=False); ax.spines[["top","right"]].set_visible(False); ax.grid(axis="y", alpha=.15); ax.set_axisbelow(True)
save(fig,"route_utilities","Route utility demand","Compare matched nutrient route utilities","route_comparison.csv","MWh/y","Results 6.4")

hbar("route_phosphorus_stream", "Phosphorus product stream", labels,
     [float(r["phosphorus_product_kg_year"])/1000 for r in order], "t/y (reported stream mass)",
     "Isolate phosphorus route output", "route_comparison.csv", "Results 6.3", YELLOW)
hbar("route_ammonium_stream", "Ammonium product stream", labels,
     [float(r["ammonium_product_kg_year"])/1000 for r in order], "t/y (reported stream mass)",
     "Isolate ammonia route output", "route_comparison.csv", "Results 6.3", GREEN)

hbar("account_readiness", "Evidence gaps", ["TEA missing input records", "LCA missing input records", "Model warnings"],
     [len(baseline["tea"]["missing_inputs"]),len(baseline["lca"]["missing_inputs"]),len(baseline["warnings"])],
     "Recorded items", "Show why investment and climate ranking is not supported", "baseline_report.json tea, lca, warnings", "Discussion 7.4", YELLOW)

warnings = baseline["warnings"]
groups=Counter("Structural parameters" if "quality class E" in w or "class E" in w or "structural" in w.lower() else
               "Equipment/cost" if "cost" in w or "dryer" in w else "Process assumptions" for w in warnings)
hbar("warning_categories","Model warnings",list(groups),list(groups.values()),"Warning count", "Summarize baseline warnings without suppressing them", "baseline_report.json warnings", "Discussion 7.5", ROSE)

def flow(name,title,steps,purpose,section):
    fig,ax=plt.subplots(figsize=(12,3.3));ax.set_xlim(0,12);ax.set_ylim(0,3.3);ax.axis('off')
    n=len(steps); gap=.22; width=(11.5-(n-1)*gap)/n
    for i,label in enumerate(steps):
        x=.25+i*(width+gap)
        ax.add_patch(FancyBboxPatch((x,1.1),width,1.1,boxstyle='round,pad=0.04,rounding_size=0.12',facecolor=GREEN if i in (2,3) else BLUE,edgecolor='none'))
        ax.text(x+width/2,1.65,label,ha='center',va='center',color='white',fontsize=10,wrap=True)
        if i<n-1:ax.annotate('',xy=(x+width+gap-.03,1.65),xytext=(x+width+.03,1.65),arrowprops={'arrowstyle':'->','color':INK,'lw':1.5})
    ax.set_title(title,loc='left')
    save(fig,name,title,purpose,'Greenhub application and integration code','Process topology',section)

flow('model_architecture','Model architecture',['Inputs','Feedstock','Process model','Balances','TEA and LCA','Decision support'],'Show calculation order','Methods 4.2')
flow('baseline_process_flow','Baseline process flow',['Grass and PEF','Press','Protein','Digestion','Water scrubber','P and N recovery'],'Show the active F2 PR3 AD1 BG2 NR4 A route','Methods 4.4')

with (ROOT/"figure_catalogue.csv").open("w",newline="",encoding="utf-8-sig") as f:
    writer=csv.DictWriter(f,fieldnames=list(catalog[0]));writer.writeheader();writer.writerows(catalog)
print(f"Generated {len(catalog)} figures")

if __name__ == "__main__": pass
