"""Render the empirical structural baseline boundary mass balance."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch, Rectangle

from Greenhub.integration import create_integrated_greenhub_system

root = Path(__file__).resolve().parents[1]
out = root / "Greenhub" / "results"
out.mkdir(exist_ok=True)
model = create_integrated_greenhub_system(
    feed_preparation_scenario_id="F2", protein_recovery_scenario_id="PR1",
    anaerobic_digestion_scenario_id="AD1", biogas_upgrading_scenario_id="BG2",
    scenario_id="NR2", selected_month="July", process_order="A",
).simulate()
unique = {id(s): s for s in model.streams.values()}.values()
inputs = [s for s in unique if s.source is None and s.sink is not None and s.F_mass > 1e-9]
outputs = sorted([s for s in unique if s.source is not None and s.sink is None and s.F_mass > 1e-9], key=lambda s: -s.F_mass)
total_in = sum(s.F_mass for s in inputs)
total_out = sum(s.F_mass for s in outputs)
labels = {
    "pressed_fibre_cake": "Fibre cake", "struvite_mother_liquor": "Residual nutrient liquor",
    "primary_sludge": "Primary sludge", "dryer_exhaust": "Dryer exhaust / water vapour",
    "dry_protein_product": "Dried protein product", "nutrient_rich_digestate_solids": "Nutrient-rich solids",
    "preparation_rejects": "Preparation rejects", "water_scrubber_reject_gas": "Upgrading reject gas",
    "water_scrubber_biomethane": "Biomethane", "phase6_wastewater": "Gas-cleaning wastewater",
    "struvite_product": "Struvite product", "uncaptured_biogas": "Uncaptured biogas",
    "phase6_spent_material": "Spent cleaning media",
}
fig, ax = plt.subplots(figsize=(17, 11), facecolor="white")
fig.subplots_adjust(left=.025, right=.98, top=.85, bottom=.14)
ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
colors = ["#539c59", "#429fc2", "#a68b65", "#94bbcc", "#ba6682", "#76ad9b", "#9b9b9b", "#ba9aaf", "#dbad4e", "#5db7bf", "#c09552", "#b68484", "#888888"]
scale = .67 / total_in
gap = .023
height = total_out * scale + gap * (len(outputs)-1)
top = (1+height)/2
center_top = .5 + total_in*scale/2
cursor = center_top

def ribbon(x0, x1, y0, y1, h, color):
    verts = [(x0,y0),(x0+.19,y0),(x1-.19,y1),(x1,y1),
             (x1,y1-h),(x1-.19,y1-h),(x0+.19,y0-h),(x0,y0-h),(x0,y0)]
    codes = [MPath.MOVETO,MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.LINETO,
             MPath.CURVE4,MPath.CURVE4,MPath.CURVE4,MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts,codes), facecolor=color, alpha=.48, linewidth=0))

feed = next(s for s in inputs if s.ID == "roadside_grass")
aux = total_in - feed.F_mass
for value, y, color, label in [(feed.F_mass, center_top,"#3a9b4c","Roadside grass"),
                              (aux, center_top-feed.F_mass*scale,"#d0a34c","Water, reagents & media")]:
    h=value*scale
    ribbon(.19,.43,y,y,h,color)
    ax.add_patch(Rectangle((.183,y-h),.009,h,color=color))
    text_y = y-h/2 if value == feed.F_mass else .12
    ax.annotate(f"{label}\n{value:,.3f} kg/h",xy=(.187,y-h/2),xytext=(.17,text_y),
                ha="right",va="center",fontsize=11,
                arrowprops=dict(arrowstyle="-",color=color) if value != feed.F_mass else None)

ax.add_patch(Rectangle((.43,center_top-total_in*scale),.013,total_in*scale,color="#8574a5"))
for i,s in enumerate(outputs):
    h=s.F_mass*scale
    color=colors[i%len(colors)]
    ribbon(.443,.77,cursor,top,h,color)
    ax.add_patch(Rectangle((.77,top-h),.009,max(h,.0007),color=color))
    ax.text(.79,top-h/2,f"{labels.get(s.ID,s.ID.replace('_',' ').capitalize())}   {s.F_mass:,.3f}",va="center",fontsize=10.5)
    cursor-=h; top-=h+gap
ax.text(.437,.5,"Integrated\nprocess route",ha="center",va="center",fontsize=10,
        bbox=dict(facecolor="white",alpha=.9,edgecolor="none",pad=5))
fig.text(.06,.95,"GreenHub | Baseline mass balance",fontsize=23,weight="bold")
fig.text(.06,.91,"Empirical structural baseline  |  F2 / PR1 / AD1 / BG2 / NR2  |  Order A  |  July",fontsize=12,color="#555555")
fig.text(.06,.085,f"Total inputs: {total_in:,.3f} kg/h     Total outputs: {total_out:,.3f} kg/h     Residual (in - out): {total_in-total_out:.2e} kg/h",fontsize=11)
fig.text(.06,.05,"Ribbon widths show total wet-stream mass, not pure-component yields. Values at right are kg/h.\nProvisional structural parameters remain in use; this is not a validated design prediction.",fontsize=10,color="#666666")
fig.savefig(out / "baseline_mass_balance_sankey.png",dpi=180)
fig.savefig(out / "baseline_mass_balance_sankey.svg")
with (out / "baseline_mass_balance_streams.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.writer(f);writer.writerow(["boundary","stream_id","mass_kg_h"])
    for kind,streams in [("input",inputs),("output",outputs)]:
        writer.writerows((kind,s.ID,float(s.F_mass)) for s in streams)
print(json.dumps({"inputs_kg_h":total_in,"outputs_kg_h":total_out,"residual_kg_h":total_in-total_out,"png":str(out / "baseline_mass_balance_sankey.png")}))
