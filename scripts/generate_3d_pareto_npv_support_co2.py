"""Build a combined 3-objective Pareto PNG from the saved GreenHub RVO run."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'Greenhub' / 'results' / 'pareto_rvo_2026'
OUT = ROOT / 'results' / 'report_figures' / '07_optimization' / 'pareto_3d_npv_support_co2.png'
OUT.parent.mkdir(parents=True, exist_ok=True)

BG, INK, GRID = '#f4f0eb', '#0c3338', '#d8d1c9'
GROUP_STYLE = {
    'protein_enabled': {'label': 'Protein enabled', 'color': '#729ad2', 'marker': 'o'},
    'protein_bypass': {'label': 'Protein bypassed', 'color': '#b77436', 'marker': '^'},
}
ENDPOINT_COLORS = {'Economic optimum': '#d277a3', 'Lowest CO₂': '#408f4d'}


def read_rows(group: str) -> list[dict]:
    batch = json.loads((DATA / f'{group}_batch.json').read_text(encoding='utf-8'))
    rows: list[dict] = []
    for shard_name in batch.get('sample_shards', []):
        shard = json.loads((DATA / shard_name).read_text(encoding='utf-8'))
        rows.extend(shard.get('samples', []))
    if not rows:
        rows = batch.get('samples', [])
    return rows


records: list[dict] = []
for group in GROUP_STYLE:
    for row in read_rows(group):
        objectives = row.get('objectives') or {}
        if row.get('status') != 'evaluated':
            continue
        if not all(objectives.get(key, {}).get('eligible') for key in ('npv', 'subsidy_granted', 'climate')):
            continue
        records.append({
            'sample_id': row['sample_id'],
            'group': group,
            'npv': float(objectives['npv']['value']) / 1e6,
            'support': float(objectives['subsidy_granted']['value']) / 1e6,
            'co2': float(objectives['climate']['value']) / 1000,
        })

if not records:
    raise RuntimeError('No evaluated scenarios have eligible NPV, support PV and climate results.')

# NPV is maximized; discounted public support and annual operational CO2 are minimized.
npv = np.asarray([r['npv'] for r in records])
support = np.asarray([r['support'] for r in records])
co2 = np.asarray([r['co2'] for r in records])
front_mask = np.ones(len(records), dtype=bool)
for i in range(len(records)):
    dominates_i = (npv >= npv[i]) & (support <= support[i]) & (co2 <= co2[i])
    dominates_i[i] = False
    strict = (npv > npv[i]) | (support < support[i]) | (co2 < co2[i])
    if np.any(dominates_i & strict):
        front_mask[i] = False

fig = plt.figure(figsize=(12.4, 9.4), dpi=300, facecolor=BG)
ax = fig.add_subplot(111, projection='3d', facecolor=BG)
ax.computed_zorder = False
ax.view_init(elev=24, azim=-55)
ax.set_proj_type('persp')

# All evaluated combinations provide context; nondominated designs are overlaid by protein route.
ax.scatter(npv, support, co2, s=10, c='#aeb7b4', alpha=.18, depthshade=False, linewidths=0, zorder=1)
front_ids: dict[str, list[int]] = {name: [] for name in GROUP_STYLE}
for idx, record in enumerate(records):
    if front_mask[idx]:
        front_ids[record['group']].append(idx)
for group, style in GROUP_STYLE.items():
    ids = front_ids[group]
    if ids:
        ax.scatter(npv[ids], support[ids], co2[ids], s=48, c=style['color'], marker=style['marker'],
                   edgecolor=INK, linewidth=.45, depthshade=False, label=style['label'], zorder=3)

economic_idx = int(np.argmax(npv))
climate_idx = int(np.argmin(co2))
for idx, label in ((economic_idx, 'Economic optimum'), (climate_idx, 'Lowest CO₂')):
    ax.scatter([npv[idx]], [support[idx]], [co2[idx]], s=130, c=ENDPOINT_COLORS[label],
               marker='*', edgecolor='white', linewidth=1.0, depthshade=False, zorder=10)

ax.set_xlabel('NPV (€ million)', labelpad=10, fontsize=13, color=INK)
ax.set_ylabel('Public support PV (€ million)', labelpad=11, fontsize=13, color=INK)
ax.set_zlabel('CO₂ emissions (t CO₂-eq/year)', labelpad=10, fontsize=13, color=INK)
ax.tick_params(axis='x', labelsize=10, colors=INK, pad=2)
ax.tick_params(axis='y', labelsize=10, colors=INK, pad=2)
ax.tick_params(axis='z', labelsize=10, colors=INK, pad=3)
ax.set_box_aspect((1.15, 1.15, .88))
ax.set_title('NPV, support & CO₂ Pareto', fontsize=21, fontweight='bold', color=INK, pad=18, loc='center')
ax.grid(True, color=GRID, linewidth=.65, alpha=.75)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.set_facecolor(BG)
    axis.pane.set_edgecolor(GRID)
    axis._axinfo['grid']['color'] = (*matplotlib.colors.to_rgb(GRID), .55)

legend_items = [
    Line2D([0], [0], marker=GROUP_STYLE[group]['marker'], color='none', markerfacecolor=GROUP_STYLE[group]['color'],
           markeredgecolor=INK, markersize=9, label=GROUP_STYLE[group]['label'])
    for group in GROUP_STYLE
]
legend_items.extend(Line2D([0], [0], marker='*', color='none', markerfacecolor=color, markeredgecolor='white',
                           markersize=12, label=label) for label, color in ENDPOINT_COLORS.items())
ax.legend(handles=legend_items, loc='upper center', bbox_to_anchor=(.5, .94), ncol=4,
          frameon=False, fontsize=12, columnspacing=1.5, handletextpad=.5)
fig.subplots_adjust(left=.02, right=.92, top=.90, bottom=.04)
fig.savefig(OUT, dpi=300, facecolor=BG, bbox_inches='tight', pad_inches=.16)
print(f'{OUT}\nscenarios={len(records)}\nthree_objective_nondominated={int(front_mask.sum())}')
