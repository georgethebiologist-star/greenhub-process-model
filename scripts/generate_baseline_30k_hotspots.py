from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

OUT = Path('results/report_figures/05_hotspots/baseline_30000_process_stage_hotspots.png')
OUT.parent.mkdir(parents=True, exist_ok=True)

# Annual BioSTEAM simulation for F1 / PR3 / AD1 / BG2 / NR7, no PEF.
stages_e = {
    'Pretreatment': 208.970973,
    'Protein recovery': 29.731624,
    'Biomethane production': 39.785,
    'Ammonia recovery': 0.273,
    'Struvite recovery': 0.674,
    'Potassium recovery': 396.166,
    'Shared utilities': 1.760,
}
stages_h = {
    'Protein recovery': 764.911010,
    'Biomethane production': 44.733324,
    'Ammonia recovery': 384.676,
    'Potassium recovery': 11900.717,
}
capex = {
    'Pretreatment': 442772.0819,
    'Protein recovery': 142232.8652,
    'Biomethane production': 1512135.4175,
    'Ammonia recovery': 326959.2178,
    'Struvite recovery': 164565.3451,
    'Potassium recovery': 78193.4983,
}
opex = {'Heat': 1038436.5177, 'Labour': 359250.0, 'Electricity': 134862.6285, 'Consumables': 53812.4819}

palette = {
    'bg': '#f4f0eb', 'ink': '#0c3338', 'muted': '#58747a', 'grid': '#d8d1c9',
    'electricity': '#729ad2', 'heating': '#d1a520', 'protein': '#d277a3',
    'biomethane': '#729ad2', 'nitrogen': '#408f4d', 'phosphorus': '#d1a520',
    'potassium': '#b77436', 'shared': '#0c3338', 'other': '#0c3338',
}
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':palette['ink'],'axes.labelcolor':palette['ink'],
                     'xtick.color':palette['ink'],'ytick.color':palette['ink']})
fig, ax = plt.subplots(2, 2, figsize=(12, 9), dpi=300, facecolor=palette['bg'])
fig.suptitle('Energy & economic hotspots', x=0.5, y=0.975, ha='center', fontsize=27, fontweight='bold', color=palette['ink'])


def barh(a, data, title, unit, color_or_map, fmt):
    labels, vals = list(data.keys()), list(data.values())
    labels, vals = labels[::-1], vals[::-1]
    colors = [color_or_map.get(k, palette['ink']) for k in labels] if isinstance(color_or_map, dict) else color_or_map
    a.set_facecolor(palette['bg'])
    a.barh(labels, vals, color=colors, height=.58)
    a.set_title(title, loc='center', fontsize=19, pad=14, color=palette['ink'])
    a.set_xlabel(unit, fontsize=15, labelpad=8)
    a.xaxis.set_major_formatter(FuncFormatter(fmt))
    a.xaxis.set_major_locator(MaxNLocator(nbins=5))
    a.grid(axis='x', color=palette['grid'], linewidth=.6)
    a.set_axisbelow(True)
    a.tick_params(axis='both', labelsize=13, length=0, pad=7)
    for spine in ('top','right'):
        a.spines[spine].set_visible(False)
    for spine in ('left','bottom'):
        a.spines[spine].set_color(palette['ink'])
        a.spines[spine].set_linewidth(.65)

barh(ax[0,0], stages_e, 'Electricity by stage', 'MWh/year', palette['electricity'], lambda x,p: f'{x:,.0f}')
barh(ax[0,1], stages_h, 'Heat by stage', 'MWh/year', palette['heating'], lambda x,p: f'{x:,.0f}')
capcolors = {'Pretreatment':palette['potassium'],'Protein recovery':palette['protein'],'Biomethane production':palette['biomethane'],'Ammonia recovery':palette['nitrogen'],'Struvite recovery':palette['phosphorus'],'Potassium recovery':palette['potassium']}
barh(ax[1,0], capex, 'CAPEX by process stage', '€', capcolors, lambda x,p: f'{x/1e6:.1f}M' if x>=1e6 else f'{x/1e3:.0f}k')
opexcolors = {'Heat':palette['heating'],'Labour':palette['nitrogen'],'Electricity':palette['electricity'],'Consumables':palette['shared']}
barh(ax[1,1], opex, 'OPEX contribution', '€/year', opexcolors, lambda x,p: f'{x/1e6:.1f}M' if x>=1e6 else f'{x/1e3:.0f}k')
fig.subplots_adjust(left=.205, right=.97, top=.88, bottom=.09, hspace=.48, wspace=.34)
fig.savefig(OUT, dpi=300, facecolor=palette['bg'])
print(OUT.resolve())
