"""Render saved baseline stream masses per tonne of grass."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch, Rectangle

out = Path(__file__).resolve().parents[1] / "Greenhub" / "results"
with (out / "baseline_mass_balance_streams.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
feed = next(float(r["mass_kg_h"]) for r in rows if r["stream_id"] == "roadside_grass")
for row in rows:
    row["mass_kg_per_t_grass"] = float(row["mass_kg_h"]) * 1000 / feed
outputs = [r for r in rows if r["boundary"] == "output"]
aux = sum(r["mass_kg_per_t_grass"] for r in rows if r["boundary"] == "input") - 1000
labels = ["Fibre", "Residual liquid", "Sludge", "Water vapour", "Dry protein", "Nutrient solids",
          "Rejects", "Off-gas", "Biomethane", "Wastewater", "Struvite", "Gas losses", "Spent media"]
colors = ["#469c58", "#459fc3", "#a99270", "#86b9cb", "#b75d7f", "#63a591",
          "#989898", "#af83a2", "#d6a43a", "#50a9b3", "#b38c41", "#ad7979", "#7a7a7a"]
fig, ax = plt.subplots(figsize=(16, 10), facecolor="white")
fig.subplots_adjust(left=.02, right=.99, bottom=.025, top=.94)
ax.set(xlim=(0,1), ylim=(0,1)); ax.axis("off")
scale = .57 / (1000 + aux)
gap = .030
top = (.99 + sum(r["mass_kg_per_t_grass"] for r in outputs)*scale + gap*(len(outputs)-1))/2
center_top = .77

def ribbon(x0,x1,y0,y1,h,color):
    points=[(x0,y0),(x0+.18,y0),(x1-.18,y1),(x1,y1),(x1,y1-h),
            (x1-.18,y1-h),(x0+.18,y0-h),(x0,y0-h),(x0,y0)]
    codes=[1,4,4,4,2,4,4,4,79]
    ax.add_patch(PathPatch(PlotPath(points,codes),facecolor=color,alpha=.48,lw=0))

for value,y,color,label,text_y in [(1000,center_top,"#349646","Grass",center_top-500*scale),
                                  (aux,center_top-1000*scale,"#c29b4e","Added inputs",.13)]:
    h=value*scale
    ribbon(.18,.42,y,y,h,color)
    ax.add_patch(Rectangle((.173,y-h),.009,h,color=color,lw=0))
    ax.annotate(f"{label}\n{value:,.2f}",xy=(.177,y-h/2),xytext=(.16,text_y),
                ha="right",va="center",fontsize=19,
                arrowprops=dict(arrowstyle="-",color=color,lw=1.2) if label=="Added inputs" else None)
ax.add_patch(Rectangle((.42,center_top-(1000+aux)*scale),.011,(1000+aux)*scale,color="#887ca3",lw=0))
cursor=center_top
for row,label,color in zip(outputs,labels,colors):
    value=row["mass_kg_per_t_grass"];h=value*scale
    ribbon(.431,.735,cursor,top,h,color)
    ax.add_patch(Rectangle((.735,top-h),.009,max(h,.0006),color=color,lw=0))
    ax.text(.76,top-h/2,label,fontsize=17,ha="left",va="center")
    ax.text(.985,top-h/2,f"{value:,.2f}",fontsize=17,ha="right",va="center")
    cursor-=h;top-=h+gap
fig.text(.755,.97,"kg / tonne grass",ha="left",va="center",fontsize=15,color="#555555")
fig.savefig(out / "baseline_mass_balance_per_tonne.png",dpi=200)
fig.savefig(out / "baseline_mass_balance_per_tonne.svg")
with (out / "baseline_mass_balance_per_tonne.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=["boundary","stream_id","mass_kg_per_t_grass"],extrasaction="ignore")
    writer.writeheader();writer.writerows(rows)
