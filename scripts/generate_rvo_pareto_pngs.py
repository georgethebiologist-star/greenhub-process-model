"""Create publication-size PNGs from the latest RVO-screened BioSTEAM run."""
from __future__ import annotations

import csv, json, math, io
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Greenhub'/'results'/'pareto_rvo_2026'/'rvo_pareto_manifest.json'
FIGROOT=ROOT/'results'/'report_figures'/'10_rvo_2026_support_adjusted'
OUT=FIGROOT/'07_optimization'
OUT.mkdir(parents=True,exist_ok=True)
BG='#efebe6'; INK='#0c3338'; GREEN='#408f4d'; BLUE='#729ad2'; YELLOW='#d1a520'; ROSE='#d277a3'; GREY='#8d9996'
CASE_COLORS={'C30':BLUE,'C45':GREEN,'C60':YELLOW,'C0':ROSE}
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'savefig.facecolor':BG,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':INK,'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':15,'axes.labelsize':12,'legend.fontsize':9,'figure.dpi':300,'savefig.dpi':300})
INDEX=[]

def save(fig,path,description,source,scenario,units):
    # Render in memory before writing; this avoids transient Windows file-handle
    # conflicts when the report-figure directory is being indexed or previewed.
    image=io.BytesIO()
    fig.savefig(image,format='png',dpi=300,bbox_inches='tight',facecolor=BG)
    path.write_bytes(image.getvalue())
    plt.close(fig)
    INDEX.append({'figure_name':path.stem,'description':description,'source_dataset':source,'scenario':scenario,'units':units,'file_location':str(path.relative_to(ROOT))})

def short_switches(row):
    s=row['configuration']['simulation']['scenarios']; nr=s['nutrient_recovery']
    vals=[s['protein_recovery']!='PR0',s['biogas_upgrading']!='BG0',nr in ('NR3','NR4','NR6','NR7'),nr in ('NR2','NR4','NR5','NR7'),nr=='NR7']
    return ''.join('✓' if x else 'X' for x in vals)

def pairplot(group,rows,front,key,xlabel,xunit,title,case=None):
    fig,ax=plt.subplots(figsize=(8,6))
    cloud=[r for r in rows if r.get('status')=='evaluated' and r.get('objectives',{}).get(key,{}).get('eligible') and r.get('objectives',{}).get('npv',{}).get('eligible')]
    if cloud:
        ax.scatter([r['objectives'][key]['value'] for r in cloud],[r['objectives']['npv']['value'] for r in cloud],s=18,c=GREY,alpha=.25,label='Evaluated designs',linewidths=0)
    for point in front['points']:
        row=next((r for r in rows if r['sample_id']==point['sample_id']),None)
        color=CASE_COLORS.get(point['support_case'],INK)
        ax.scatter(point[key],point['npv'],s=50,c=color,edgecolor=INK,linewidth=.35,alpha=.9)
    if key=='net_carbon' and case is None:
        selected_rows={r['sample_id']:r for r in rows}
        offsets={0:(9,13),10:(-20,-16)}
        for c in _select_for_plot:
            row=selected_rows.get(c['sample_id'])
            if not row: continue
            p={key:row['objectives'][key]['value'],'npv':row['objectives']['npv']['value']}
            color=ROSE if c['rank']==0 else GREEN if c['rank']==10 else YELLOW
            ax.scatter(p[key],p['npv'],s=95,c=color,edgecolor='white',linewidth=1.1,zorder=4)
            if c['rank'] in offsets:
                ax.annotate(str(c['rank']),(p[key],p['npv']),xytext=offsets[c['rank']],textcoords='offset points',fontsize=8,fontweight='bold',color=INK,arrowprops={'arrowstyle':'-','lw':.45,'color':INK,'alpha':.6})
        ax.text(.01,.015,'Ranks 1–9 are indexed in candidate KPI figures. Selected ranks are from the 3-objective front; the 2D projection may include dominated points.',transform=ax.transAxes,fontsize=7,color=INK,ha='left',va='bottom')
    ax.set_xlabel(f'{xlabel} ({xunit}) · minimize');ax.set_ylabel('NPV (€) · maximize')
    ax.set_title(title,loc='left',fontweight='bold');ax.grid(axis='both',color='#aebbb6',alpha=.22,linewidth=.55)
    ax.spines[['top','right']].set_visible(False)
    if case is None: ax.legend(frameon=False,loc='best')
    else: ax.text(.99,.02,case,transform=ax.transAxes,ha='right',va='bottom',fontsize=9,color=INK)
    name=f'pareto_{key}_vs_npv_{group}'+(f'_case_{case}' if case else '')+'.png'
    save(fig,OUT/name,title,Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',group+(f' / case {case}' if case else ' / all support cases'),f'{xlabel}: {xunit}; NPV: €')

doc=json.loads(SOURCE.read_text(encoding='utf-8'))
_select_for_plot=[]
for group in ('protein_enabled','protein_bypass'):
    pack=doc['groups_payload'][group]; rows=pack['samples']; fronts=pack['fronts']; selected=pack['selected_candidates']['net_carbon_vs_npv']; _select_for_plot=selected
    title_group='Protein enabled' if group=='protein_enabled' else 'Protein bypassed'
    pairplot(group,rows,fronts['net_carbon_vs_npv'],'net_carbon','Net carbon','t C/year',f'Net carbon and NPV · {title_group}')
    pairplot(group,rows,fronts['subsidy_vs_npv'],'subsidy_granted','Public support','€ PV',f'Public support and NPV · {title_group}')
    for case,front in fronts.get('by_support_case',{}).items():
        pairplot(group,rows,front,'net_carbon','Net carbon','t C/year',f'Carbon and NPV · {title_group}',case)

    # Three-objective non-dominance; 2D projections are provided above as well.
    front3=fronts['net_carbon_npv_subsidy']
    if front3['points']:
        fig=plt.figure(figsize=(10.5,8));ax=fig.add_subplot(111,projection='3d')
        for cid,color in CASE_COLORS.items():
            pts=[p for p in front3['points'] if p['support_case']==cid]
            if pts: ax.scatter([p['net_carbon'] for p in pts],[p['npv'] for p in pts],[p['subsidy_granted'] for p in pts],s=28,c=color,edgecolor=INK,linewidth=.3,label=f'Case {cid}')
        selected_rank={c['sample_id']:c['rank'] for c in selected}
        for p in front3['points']:
            rank=selected_rank.get(p['sample_id'])
            if rank is not None:
                color=ROSE if rank==0 else GREEN if rank==10 else YELLOW
                ax.scatter([p['net_carbon']],[p['npv']],[p['subsidy_granted']],s=92,c=color,edgecolor='white',linewidth=1.0,zorder=8)
        ax.scatter([],[],[],s=72,c=ROSE,edgecolor='white',label='Rank 0 · economic')
        ax.scatter([],[],[],s=72,c=GREEN,edgecolor='white',label='Rank 10 · environmental')
        ax.set_xlabel('Net carbon (t C/year) · min',labelpad=10);ax.set_ylabel('NPV (€) · max',labelpad=10);ax.set_zlabel('Support PV (€) · min',labelpad=8)
        ax.set_title(f'Carbon, NPV and support · {title_group}',loc='left',fontweight='bold',pad=16);ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(0,1))
        save(fig,OUT/f'pareto_3d_carbon_npv_support_{group}.png','Three-objective Pareto front',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',title_group,'t C/year; €; € present value')

    # Candidate KPI heatmap and economic/environmental comparisons.
    if selected:
        fields=[('npv','NPV (€)'),('subsidy_granted','Support PV (€)'),('net_carbon','Net carbon (t C/y)')]
        matrix=np.array([[float(c['values'][f]) for f,_ in fields] for c in selected])
        norm=np.empty_like(matrix)
        for j,(field,_) in enumerate(fields):
            lo,hi=matrix[:,j].min(),matrix[:,j].max();norm[:,j]=(matrix[:,j]-lo)/(hi-lo) if hi>lo else .5
            if field in ('subsidy_granted','net_carbon'): norm[:,j]=1-norm[:,j]  # lower support and carbon are favorable
        fig,ax=plt.subplots(figsize=(8,6));im=ax.imshow(norm,aspect='auto',cmap='RdYlGn',vmin=0,vmax=1)
        ax.set_yticks(range(len(selected)),[f"{c['rank']}  {short_switches(c)}" for c in selected]);ax.set_xticks(range(len(fields)),[label for _,label in fields])
        for i,c in enumerate(selected):
            for j,(field,_) in enumerate(fields):
                v=float(c['values'][field]); label=f'{v:,.0f}'
                ax.text(j,i,label,ha='center',va='center',fontsize=8,color=INK)
        ax.set_title(f'Candidate KPI matrix · {title_group}',loc='left',fontweight='bold');fig.colorbar(im,ax=ax,fraction=.035,pad=.03,label='Relative score within selected set')
        save(fig,OUT/f'candidate_kpi_heatmap_{group}.png','Selected candidate KPI comparison; color normalized by objective direction',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',title_group,'€, € present value, t C/year')

        x=np.arange(len(selected));labs=[str(c['rank']) for c in selected]
        fig,ax=plt.subplots(figsize=(9,5.5));w=.37
        ax.bar(x-w/2,[c['values']['npv']/1e6 for c in selected],w,color=BLUE,label='NPV (€ million)')
        ax.bar(x+w/2,[c['values']['subsidy_granted']/1e6 for c in selected],w,color=YELLOW,label='Support PV (€ million)')
        ax.axhline(0,color=INK,linewidth=.8);ax.set_xticks(x,labs);ax.set_xlabel('Selected candidate rank · 0 economic → 10 environmental');ax.set_ylabel('€ million');ax.set_title(f'Economic comparison · {title_group}',loc='left',fontweight='bold');ax.legend(frameon=False,ncols=2);ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
        save(fig,OUT/f'candidate_economics_{group}.png','NPV and assumed public support PV for selected Pareto candidates',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',title_group,'€ million')

        fig,axs=plt.subplots(1,2,figsize=(10,5.5));axs[0].bar(x,[c['values']['net_carbon'] for c in selected],color=[ROSE if c['rank']==0 else GREEN if c['rank']==10 else BLUE for c in selected]);axs[0].set_ylabel('t C/year');axs[0].set_title('Net carbon · lower preferred')
        axs[1].bar(x,[float(next(r for r in rows if r['sample_id']==c['sample_id'])['objectives']['climate']['value'])/1000 for c in selected],color=GREEN);axs[1].set_ylabel('t CO₂-eq/year');axs[1].set_title('Operational climate load')
        for ax in axs: ax.set_xticks(x,labs);ax.set_xlabel('Candidate rank');ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
        fig.suptitle(f'Environmental comparison · {title_group}',x=.08,ha='left',fontweight='bold',fontsize=15)
        save(fig,OUT/f'candidate_environment_{group}.png','Net stored carbon objective and attributional operational climate load',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',title_group,'t C/year; t CO₂-eq/year')

        lcadir=FIGROOT/'04_lca';lcadir.mkdir(parents=True,exist_ok=True)
        selected_rows=[next(r for r in rows if r['sample_id']==c['sample_id']) for c in selected]
        op=[r['carbon_assessment']['operational_climate_load_t_co2e_per_year']*12/44 for r in selected_rows]
        fiber=[-r['carbon_assessment']['fiber_carbon_t_c_per_year'] for r in selected_rows]
        soil=[-r['carbon_assessment']['nutrient_rich_solids_carbon_t_c_per_year']*r['carbon_assessment']['soil_carbon_retention_fraction'] for r in selected_rows]
        net=[r['carbon_assessment']['net_carbon_t_c_per_year'] for r in selected_rows]
        fig,ax=plt.subplots(figsize=(9,5.8));w=.24
        ax.bar(x-w,op,w,label='Operational load (C eq.)',color=ROSE)
        ax.bar(x,fiber,w,label='Fiber carbon stored',color=BLUE)
        ax.bar(x+w,soil,w,label='Soil carbon retained',color=GREEN)
        ax.plot(x,net,color=INK,marker='o',linewidth=1.4,label='Net carbon')
        ax.axhline(0,color=INK,lw=.8);ax.set_xticks(x,labs);ax.set_xlabel('Candidate rank · 0 economic → 10 lower-carbon');ax.set_ylabel('t C/year');ax.set_title(f'Operational carbon and stored carbon · {title_group}',loc='left',fontweight='bold');ax.legend(frameon=False,ncols=2,loc='upper center',bbox_to_anchor=(.5,-.17));ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
        save(fig,lcadir/f'carbon_load_vs_stored_carbon_{group}.png','Attributional operational carbon-equivalent load minus fiber and soil retained product carbon',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',title_group,'t C/year')

        # Each candidate receives a compact, comparable mini-library in its own subfolder.
        for c in selected:
            row=next(r for r in rows if r['sample_id']==c['sample_id']); rank=int(c['rank']); dest=FIGROOT/'08_candidate_comparison'/group/f'candidate_{rank:02d}'
            dest.mkdir(parents=True,exist_ok=True); ann=row['annual']; products=ann.get('products',{}); util=ann.get('utilities',{}); econ=row.get('candidate_economics',{})
            config=row['configuration'];sw=short_switches(row); sc=config['simulation']['scenarios'];feed=float(ann['feed_processed']['value'])/1000
            # Separate gas volume from solid products. CH4 density: 0.716 kg/Nm3 at 0 °C, 1.01325 bar; ideal pure methane basis.
            methane_nm3=float(products.get('biomethane',{}).get('value',0))/0.716
            fig,ax=plt.subplots(figsize=(8,5.4));solid_labels=['Protein','P product','N product','K concentrate','Nutrient solids'];solid_keys=['dry_protein_product','phosphorus_product','ammonium_product','potassium_concentrate','nutrient_rich_solids'];vals=[float(products.get(k,{}).get('value',0))/1000 for k in solid_keys]
            ax.barh(solid_labels,vals,color=[BLUE,YELLOW,GREEN,ROSE,GREY]);ax.set_xlabel('t/year');ax.set_title(f'Products · candidate {rank} · {sw}',loc='left',fontweight='bold');ax.text(.99,.02,f"CH₄ product: {methane_nm3:,.0f} Nm³/y",transform=ax.transAxes,ha='right',va='bottom',fontsize=9);ax.grid(axis='x',alpha=.2);ax.spines[['top','right']].set_visible(False)
            save(fig,dest/'candidate_products.png','Annual solid products; methane separately shown as Nm3 using 0.716 kg/Nm3 at normal conditions',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',f"{group}; rank {rank}; {sc}",'t/year; Nm³/year')
            fig,ax=plt.subplots(figsize=(8,5.4));labels=['Electricity','Heat','Cooling'];values=[float(util.get(k,{}).get('value',0))/1000 for k in ('electricity','heating','cooling')];ax.bar(labels,values,color=[BLUE,ROSE,GREEN]);ax.set_ylabel('MWh/year');ax.set_title(f'Utilities · candidate {rank} · {sw}',loc='left',fontweight='bold');ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
            save(fig,dest/'candidate_utilities.png','Annual electricity, heating and cooling duty',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',f"{group}; rank {rank}; {sc}",'MWh/year')
            finance=config['candidate_economics'];life=int(finance.get('project_lifetime_years',20));discount=float(finance.get('discount_rate',.08));
            factor=float(life) if discount==0 else (1-(1+discount)**(-life))/discount
            high_capex=float(row['tea_totals']['high_direct_capex_eur']);grant=float(row['tea_totals']['subsidy_eur']);
            annual_cash=float(row['tea_totals']['optimized_annual_revenue_eur'])-float(row['tea_totals']['optimized_annual_opex_eur'])
            op_pv=annual_cash*factor;support_pv=float(c['values']['subsidy_granted'])-grant
            contributions=[-(high_capex-grant),op_pv,support_pv];total=sum(contributions)
            starts=[0,contributions[0],contributions[0]+contributions[1]]
            fig,ax=plt.subplots(figsize=(8,5.4));labels=['Net CAPEX','Operating margin\nPV','OPEX support\nPV','NPV']
            for i,(base_value,value) in enumerate(zip(starts,contributions)):
                ax.bar(i,abs(value),bottom=min(base_value,base_value+value),color=GREEN if value>=0 else ROSE,width=.62)
                ax.text(i,base_value+value/2,f'{value/1e6:+.2f}',ha='center',va='center',fontsize=8,color='white',fontweight='bold')
            ax.bar(3,abs(total),bottom=min(0,total),color=BLUE if total>=0 else ROSE,width=.62);ax.text(3,total/2,f'{total/1e6:+.2f}',ha='center',va='center',fontsize=8,color='white',fontweight='bold')
            levels=[0,contributions[0],contributions[0]+contributions[1],total]
            for i,y in enumerate(levels[:3]):ax.plot([i+.31,i+1-.31],[y,y],color=GREY,lw=.8,ls='--')
            ax.axhline(0,color=INK,lw=.8);ax.set_xticks(range(4),labels);ax.set_ylabel('€ million present value');ax.set_title(f'Cash-flow value bridge · candidate {rank} · {sw}',loc='left',fontweight='bold');ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
            save(fig,dest/'candidate_kpis.png','Present-value bridge: net direct CAPEX, discounted annual operating margin and operating-support PV to screening NPV',Path('Greenhub/results/pareto_rvo_2026')/f'{group}_batch.json',f"{group}; rank {rank}; support {c['support_case']}",'€ million present value')

# Explicit no-PEF baseline references, split by protein recovery status.
baseline_rows=[]
for group in ('protein_enabled','protein_bypass'):
    p=json.loads((ROOT/'Greenhub'/'results'/'pareto_rvo_2026'/f'{group}_batch.json').read_text(encoding='utf-8'))
    baseline_rows.extend([r for r in p['samples'] if r.get('baseline_reference') and r.get('status')=='evaluated'])
if baseline_rows:
    dest=FIGROOT/'01_baseline';dest.mkdir(parents=True,exist_ok=True)
    case_ids=['C30','C45','C60','C0'];x=np.arange(4);w=.36
    fig,axs=plt.subplots(1,2,figsize=(10,5.5))
    for i,(group,label,color) in enumerate([('protein_enabled','Protein enabled',BLUE),('protein_bypass','Protein bypassed',GREEN)]):
        rows=[next((r for r in baseline_rows if r['group']==group and r['support_case']==c),None) for c in case_ids]
        vals=[r['objectives']['npv']['value']/1e6 if r else np.nan for r in rows]
        axs[0].bar(x+(i-.5)*w,vals,w,color=color,label=label)
        cvals=[r['objectives']['net_carbon']['value'] if r else np.nan for r in rows]
        axs[1].bar(x+(i-.5)*w,cvals,w,color=color,label=label)
    axs[0].axhline(0,color=INK,lw=.8);axs[0].set_ylabel('€ million');axs[0].set_title('NPV by support case')
    axs[1].set_ylabel('t C/year');axs[1].set_title('Net carbon by support case')
    for ax in axs: ax.set_xticks(x,case_ids);ax.set_xlabel('RVO what-if case');ax.legend(frameon=False);ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Baseline support comparison · F1, no PEF',x=.08,ha='left',fontweight='bold',fontsize=15)
    save(fig,dest/'baseline_rvo_support_kpis.png','Baseline NPV and net carbon across paired RVO screening cases',Path('Greenhub/results/pareto_rvo_2026'),'No-PEF baseline; protein enabled and bypassed','€ million; t C/year')
    fig,ax=plt.subplots(figsize=(8,5.5))
    for i,(group,label,color) in enumerate([('protein_enabled','Protein enabled',BLUE),('protein_bypass','Protein bypassed',GREEN)]):
        row=next((r for r in baseline_rows if r['group']==group and r['support_case']=='C0'),None)
        if not row: continue
        vals=row['annual']['utilities'];v=[vals[k]['value']/1000 for k in ('electricity','heating','cooling')]
        ax.bar(np.arange(3)+(i-.5)*w,v,w,label=label,color=color)
    ax.set_xticks(np.arange(3),['Electricity','Heat','Cooling']);ax.set_ylabel('MWh/year');ax.set_title('Baseline utility demand · C0',loc='left',fontweight='bold');ax.legend(frameon=False);ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
    save(fig,dest/'baseline_utilities_protein_comparison.png','Baseline utility comparison for protein route and bypass',Path('Greenhub/results/pareto_rvo_2026'),'No-PEF baseline; C0 (utilities unaffected by support case)','MWh/year')

# Cross-configuration subsidy sensitivity for scenario comparison folder.
compare_dir=FIGROOT/'06_scenario_comparison';compare_dir.mkdir(parents=True,exist_ok=True)
case_ids=['C30','C45','C60','C0'];fig,axs=plt.subplots(1,2,figsize=(10,5.5));x=np.arange(4);w=.36
for i,(group,label,color) in enumerate([('protein_enabled','Protein enabled',BLUE),('protein_bypass','Protein bypassed',GREEN)]):
    p=json.loads((ROOT/'Greenhub'/'results'/'pareto_rvo_2026'/f'{group}_batch.json').read_text(encoding='utf-8'));rows=p['samples']
    for j,cid in enumerate(case_ids):
        vals=[r['objectives']['npv']['value']/1e6 for r in rows if r.get('status')=='evaluated' and r.get('support_case')==cid]
        axs[0].scatter(np.repeat(j+(i-.5)*w,len(vals)),vals,s=12,alpha=.3,color=color)
    med=[];support=[]
    for cid in case_ids:
        vals=[r for r in rows if r.get('status')=='evaluated' and r.get('support_case')==cid]
        med.append(float(np.median([r['objectives']['npv']['value'] for r in vals]))/1e6 if vals else np.nan)
        support.append(float(np.median([r['objectives']['subsidy_granted']['value'] for r in vals]))/1e6 if vals else np.nan)
    axs[0].plot(x,med,color=color,marker='o',linewidth=1.5,label=f'{label} median NPV')
    axs[1].plot(x,support,color=color,marker='o',linewidth=1.8,label=f'{label} median support PV')
axs[0].axhline(0,color=INK,lw=.8);axs[0].set_ylabel('NPV (€ million)');axs[0].set_title('NPV by RVO support case')
axs[1].set_ylabel('Support present value (€ million)');axs[1].set_title('Assumed public support')
for ax in axs: ax.set_xticks(x,case_ids);ax.set_xlabel('User-defined what-if case');ax.legend(frameon=False,fontsize=8);ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Support scenario comparison · sampled designs',x=.08,ha='left',fontweight='bold',fontsize=15)
save(fig,compare_dir/'rvo_support_case_npv_comparison.png','NPV samples and median support present value by support case',Path('Greenhub/results/pareto_rvo_2026'),'Protein enabled and bypassed; paired support cases','€ million')

# Dense technical, TEA and hotspot figures from actual saved model results.
technical_dir=FIGROOT/'02_technical';tea_dir=FIGROOT/'03_tea';hotspot_dir=FIGROOT/'05_hotspots'
for folder in (technical_dir,tea_dir,hotspot_dir):folder.mkdir(parents=True,exist_ok=True)
latest=json.loads((ROOT/'Greenhub'/'results'/'pareto_rvo_2026'/'latest.json').read_text(encoding='utf-8'))
endpoint_rows=[]
for group,label in [('protein_enabled','Protein enabled'),('protein_bypass','Protein bypassed')]:
    block=latest['groups_payload'][group]
    by_id={r['sample_id']:r for r in block['samples']}
    for rank in (0,10):
        chosen=next((r for r in block['selected_candidates']['net_carbon_vs_npv'] if r['rank']==rank),None)
        if chosen and chosen['sample_id'] in by_id:
            endpoint_rows.append((group,label,rank,chosen,by_id[chosen['sample_id']]))

# Solid yields use kg product stream / t wet grass; gas remains a separate Nm3 functional unit.
fig,axs=plt.subplots(1,2,figsize=(10,5.8));solid_keys=['dry_protein_product','phosphorus_product','ammonium_product','potassium_concentrate','nutrient_rich_solids'];solid_labels=['Protein','P product','N product','K concentrate','Nutrient solids'];x=np.arange(len(solid_keys));w=.19
for i,(group,label,rank,chosen,row) in enumerate(endpoint_rows):
    feed_t=float(row['annual']['feed_processed']['value'])/1000
    products=row['annual']['products'];vals=[float(products.get(k,{}).get('value',0))/feed_t for k in solid_keys]
    color=ROSE if rank==0 else GREEN
    offset=(i-(len(endpoint_rows)-1)/2)*w
    axs[0].bar(x+offset,vals,w,label=f'{"Protein" if group=="protein_enabled" else "Bypass"} r{rank}',color=color,alpha=.94 if group=='protein_enabled' else .6,edgecolor=INK,linewidth=.35,hatch=None if group=='protein_enabled' else '//')
    methane=float(products.get('biomethane',{}).get('value',0))/0.716/feed_t
    axs[1].bar(i,methane,color=color,alpha=.94 if group=='protein_enabled' else .6,edgecolor=INK,linewidth=.35,hatch=None if group=='protein_enabled' else '//')
axs[0].set_xticks(x,solid_labels,rotation=18,ha='right');axs[0].set_ylabel('kg product/t wet grass');axs[0].set_title('Solid product yields',loc='left',fontweight='bold');axs[0].legend(frameon=False,ncol=2,fontsize=8)
axs[1].set_xticks(np.arange(len(endpoint_rows)),[f'{"Protein" if g=="protein_enabled" else "Bypass"}\nr{r}' for g,_,r,_,_ in endpoint_rows]);axs[1].set_ylabel('CH₄ Nm³/t wet grass');axs[1].set_title('Methane yield',loc='left',fontweight='bold')
for ax in axs:ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Endpoint product yields',x=.08,ha='left',fontweight='bold',fontsize=15)
save(fig,technical_dir/'endpoint_product_yields.png','Solid product and methane yields at selected economic and carbon endpoints',Path('Greenhub/results/pareto_rvo_2026'),'Rank 0 and 10 from the three-objective front; no PEF','kg product/t wet grass; CH4 Nm3/t wet grass')

fig,ax=plt.subplots(figsize=(9,5.5));labels=[f'{"Protein" if g=="protein_enabled" else "Bypass"} · r{rank}' for g,_,rank,_,_ in endpoint_rows];x=np.arange(len(labels));bottom=np.zeros(len(labels))
for key,name,color in [('electricity','Electricity',BLUE),('heating','Heat',ROSE),('cooling','Cooling',GREEN)]:
    vals=[]
    for _,_,_,_,row in endpoint_rows:
        feed_t=float(row['annual']['feed_processed']['value'])/1000;vals.append(float(row['annual']['utilities'].get(key,{}).get('value',0))/1e6/feed_t)
    ax.bar(x,vals,bottom=bottom,label=name,color=color);bottom+=np.asarray(vals)
ax.set_xticks(x,labels);ax.set_ylabel('MWh/t wet grass');ax.set_title('Energy intensity',loc='left',fontweight='bold');ax.legend(frameon=False,ncol=3);ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
save(fig,technical_dir/'energy_intensity_by_candidate.png','Electricity, heat and cooling intensity at selected endpoint candidates',Path('Greenhub/results/pareto_rvo_2026'),'Rank 0 and 10 from the three-objective front; no PEF','MWh/t wet grass')

# Scale-dependent screening finance: plot all evaluated cases; this is a design sweep, not a probability distribution.
case_colors={'A':BLUE,'B':GREEN,'C':YELLOW,'D':ROSE};fig,axs=plt.subplots(2,2,figsize=(10,7.2),sharex='col')
for col,(group,label) in enumerate([('protein_enabled','Protein enabled'),('protein_bypass','Protein bypassed')]):
    rows=latest['groups_payload'][group]['samples']
    for cid,color in case_colors.items():
        selected=[r for r in rows if r.get('status')=='evaluated' and r.get('support_case')==cid]
        feed=np.asarray([float(r['annual']['feed_processed']['value'])/1000 for r in selected])
        npv=np.asarray([float(r['objectives']['npv']['value'])/1e6 for r in selected])
        profit=np.asarray([float(r['objectives']['operating_profit']['value'])/feed[i] for i,r in enumerate(selected)])
        axs[0,col].scatter(feed,npv,s=13,alpha=.45,color=color,label=f'Case {cid}')
        axs[1,col].scatter(feed,profit,s=13,alpha=.45,color=color)
    axs[0,col].set_title(label,loc='left',fontweight='bold');axs[0,col].axhline(0,color=INK,lw=.8);axs[1,col].axhline(0,color=INK,lw=.8);axs[1,col].set_xlabel('Wet grass (t/year)')
    for row in (0,1):axs[row,col].grid(alpha=.16);axs[row,col].spines[['top','right']].set_visible(False)
axs[0,0].set_ylabel('NPV (€ million)');axs[1,0].set_ylabel('Adjusted profit (€/t feed)');axs[0,1].legend(frameon=False,ncol=2,fontsize=8)
fig.suptitle('Financial scale effects',x=.08,ha='left',fontweight='bold',fontsize=15)
save(fig,tea_dir/'npv_profit_by_feed_scale.png','Screening NPV and adjusted annual profit across evaluated feed scales',Path('Greenhub/results/pareto_rvo_2026'),'All evaluated designs; cases A–D; design-space scatter, not probabilistic uncertainty','NPV: € million; profit intensity: €/t wet grass')

fig,axs=plt.subplots(1,2,figsize=(9,5.5),sharey=True);case_order=['A','B','C','D'];x=np.arange(4);w=.62
for ax,(group,label) in zip(axs,[('protein_enabled','Protein enabled'),('protein_bypass','Protein bypassed')]):
    rows=latest['groups_payload'][group]['samples'];grant=[];operating=[]
    for cid in case_order:
        values=[r['candidate_economics'] for r in rows if r.get('status')=='evaluated' and r.get('support_case')==cid]
        grant.append(float(np.median([v.get('subsidy_eur',0) for v in values]))/1e6 if values else 0)
        operating.append(float(np.median([max(0,v.get('total_public_support_pv_eur',0)-v.get('subsidy_eur',0)) for v in values]))/1e6 if values else 0)
    ax.bar(x,grant,w,color=BLUE,label='Upfront CAPEX grant');ax.bar(x,operating,w,bottom=grant,color=GREEN,label='OPEX support PV')
    ax.set_xticks(x,case_order);ax.set_title(label,loc='left',fontweight='bold');ax.set_xlabel('RVO what-if case');ax.grid(axis='y',alpha=.16);ax.spines[['top','right']].set_visible(False)
axs[0].set_ylabel('Median public support (€ million PV)');axs[1].legend(frameon=False,fontsize=8)
fig.suptitle('Support composition',x=.08,ha='left',fontweight='bold',fontsize=15)
save(fig,tea_dir/'rvo_support_composition.png','Median upfront grant and discounted operating-support components across paired support cases',Path('Greenhub/results/pareto_rvo_2026'),'Median across evaluated designs by protein group','€ million present value')

# Hotspots use stored reports for representative endpoints; shared costs stay at process/system level.
def stored_report(candidate):
    path=ROOT/'Greenhub'/'results'/'runs'/candidate['run_id']/'decision_support.json'
    return json.loads(path.read_text(encoding='utf-8'))

climate_parts=[];opex_parts=[]
for group,label,rank,chosen,row in endpoint_rows:
    report=stored_report(chosen);inventory=report.get('lca',{}).get('inventory',[]);sums={'Electricity':0.0,'Heat':0.0,'Process methane':0.0}
    for item in inventory:
        val=item.get('climate_kg_co2e')
        if val is None or not isinstance(val,(int,float)):continue
        if item.get('flow_id')=='electricity':sums['Electricity']+=max(0,float(val))
        elif item.get('flow_id')=='heat':sums['Heat']+=max(0,float(val))
        elif 'Methane' in str(item.get('flow_id')):sums['Process methane']+=max(0,float(val))
    climate_parts.append((f'{"Protein" if group=="protein_enabled" else "Bypass"} · r{rank}',sums))
    costs={}
    for item in report.get('tea',{}).get('opex_lines',[]):
        value=item.get('annual_cost_eur')
        if not isinstance(value,(int,float)) or value<=0:continue
        kind=str(item.get('cost_type') or 'other').lower();key={'labor':'Labour','logistics':'Feed logistics','utility':'Utilities','maintenance':'Maintenance'}.get(kind,'Other')
        costs[key]=costs.get(key,0.0)+float(value)
    opex_parts.append((f'{"Protein" if group=="protein_enabled" else "Bypass"} · r{rank}',costs))

fig,ax=plt.subplots(figsize=(9,5.6));x=np.arange(len(climate_parts));bottom=np.zeros(len(climate_parts))
for key,color in [('Electricity',BLUE),('Heat',ROSE),('Process methane',YELLOW)]:
    vals=np.asarray([p.get(key,0.0)/1000 for _,p in climate_parts]);ax.bar(x,vals,bottom=bottom,label=key,color=color);bottom+=vals
ax.set_xticks(x,[name for name,_ in climate_parts]);ax.set_ylabel('t CO₂-eq/year');ax.set_title('Operational climate hotspots',loc='left',fontweight='bold');ax.legend(frameon=False,ncol=3);ax.grid(axis='y',alpha=.16);ax.spines[['top','right']].set_visible(False)
save(fig,hotspot_dir/'operational_climate_by_stage.png','Electricity, heat and characterized process-methane burdens for representative Pareto endpoints',Path('Greenhub/results/pareto_rvo_2026')/'stored decision_support.json','Rank 0 and 10; protein enabled and bypassed; attributional gate-to-gate loads only','t CO2-eq/year')

cost_keys=['Labour','Feed logistics','Utilities','Maintenance','Other'];fig,ax=plt.subplots(figsize=(9,5.6));x=np.arange(len(opex_parts));bottom=np.zeros(len(opex_parts));cost_colors=[BLUE,GREEN,YELLOW,ROSE,GREY]
for key,color in zip(cost_keys,cost_colors):
    vals=np.asarray([p.get(key,0.0)/1000 for _,p in opex_parts]);
    if not np.any(vals):continue
    ax.bar(x,vals,bottom=bottom,label=key,color=color);bottom+=vals
ax.set_xticks(x,[name for name,_ in opex_parts]);ax.set_ylabel('€ thousand/year');ax.set_title('Recorded operating costs',loc='left',fontweight='bold');ax.legend(frameon=False,ncol=3);ax.grid(axis='y',alpha=.16);ax.spines[['top','right']].set_visible(False)
save(fig,hotspot_dir/'opex_categories_by_endpoint.png','Recorded system-level OPEX categories at representative Pareto endpoints; shared costs are not product-allocated',Path('Greenhub/results/pareto_rvo_2026')/'stored decision_support.json','Rank 0 and 10; protein enabled and bypassed; recorded cost lines only','€ thousand/year')

equipment_panels=[]
for kind,title,color in [('electricity','Electricity by equipment',BLUE),('heat','Heat by equipment',ROSE)]:
    unions={}
    for group,label,rank,chosen,row in endpoint_rows:
        if rank!=0:continue
        run_dir=ROOT/'Greenhub'/'results'/'runs'/chosen['run_id'];unit_map={u['unit_id']:u.get('display_name',u['unit_id']) for u in json.loads((run_dir/'units.json').read_text(encoding='utf-8'))}
        hours=float(row['annual']['period']['operating_hours'])
        for utility in json.loads((run_dir/'utilities.json').read_text(encoding='utf-8')):
            if str(utility.get('kind','')).lower()!=kind:continue
            demand=utility.get('demand',{});value=demand.get('value') if isinstance(demand,dict) else demand;unit=demand.get('unit','kW') if isinstance(demand,dict) else 'kW'
            if not isinstance(value,(int,float)) or not str(unit).lower()=='kw' or value<=0:continue
            name=unit_map.get(utility.get('unit_id'),utility.get('unit_id'));unions[(group,name)]=float(value)*hours/1000
    if unions:
        equipment_panels.append((kind,title,color,unions))
fig,axs=plt.subplots(1,len(equipment_panels),figsize=(6*len(equipment_panels),6),squeeze=False)
for ax,(kind,title,color,unions) in zip(axs.ravel(),equipment_panels):
    top=sorted(unions,key=lambda k:unions[k],reverse=True)[:12];labels=[f'{"Protein" if g=="protein_enabled" else "Bypass"} · {n}' for g,n in top];vals=[unions[k] for k in top]
    ax.barh(labels[::-1],vals[::-1],color=color);ax.set_xlabel('MWh/year');ax.set_title(title,loc='left',fontweight='bold');ax.grid(axis='x',alpha=.16);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Equipment energy hotspots',x=.08,ha='left',fontweight='bold',fontsize=15)
shown=', '.join(title.replace(' by equipment','').lower() for _,title,_,_ in equipment_panels)
save(fig,hotspot_dir/'equipment_energy_by_endpoint.png',f'Largest saved equipment {shown} duties for economic-endpoint process runs',Path('Greenhub/results/pareto_rvo_2026')/'stored utilities.json','Rank 0; protein-enabled and protein-bypassed cases; annualized at each run schedule', 'MWh/year')

for index_path in (FIGROOT/'rvo_pareto_figure_index.csv', FIGROOT/'figure_index.csv'):
    with index_path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['figure_name','description','source_dataset','scenario','units','file_location']);w.writeheader();w.writerows(INDEX)
print(f'Generated {len(INDEX)} PNGs; index: {FIGROOT/"rvo_pareto_figure_index.csv"}')
