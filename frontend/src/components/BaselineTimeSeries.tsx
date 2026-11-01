import React, {useMemo, useState} from 'react';
import {CartesianGrid, Legend, LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import type {AnnualSummary} from '../types';

type ViewId='supply'|'bulk'|'protein'|'biomethane'|'nitrogen'|'phosphorus'|'potassium'|'electricity';
type ChartRows='schedule'|'bulk_streams'|'small_products'|'biomethane'|'energy';
const views:Record<ViewId,{title:string;unit:string;rows:ChartRows;series:Array<[string,string]>;color:string}>= {
  supply:{title:'Biomass available and processed',unit:'tonnes / month',rows:'schedule',series:[['available_biomass_tonnes','Available'],['processed_biomass_tonnes','Processed']],color:'#408f4d'},
  bulk:{title:'Feed and residual streams',unit:'tonnes / month',rows:'bulk_streams',series:[['feed_processed_tonnes','Feed'],['press_cake_tonnes','Press cake'],['digestate_tonnes','Digestate']],color:'#729ad2'},
  protein:{title:'Protein product',unit:'tonnes / month',rows:'small_products',series:[['protein_tonnes','Dry protein product']],color:'#408f4d'},
  biomethane:{title:'Biomethane production',unit:'m³ / month',rows:'biomethane',series:[['biomethane_m3','Biomethane']],color:'#729ad2'},
  nitrogen:{title:'Ammonium product',unit:'tonnes / month',rows:'small_products',series:[['ammonium_product_tonnes','Ammonium product']],color:'#d1a520'},
  phosphorus:{title:'Phosphorus product',unit:'tonnes / month',rows:'small_products',series:[['phosphorus_product_tonnes','Phosphorus product']],color:'#d277a3'},
  potassium:{title:'Potassium concentrate',unit:'tonnes / month',rows:'small_products',series:[['potassium_concentrate_tonnes','Potassium concentrate']],color:'#307e86'},
  electricity:{title:'Electricity demand',unit:'MWh / month',rows:'energy',series:[['electricity_MWh','Electricity']],color:'#b77436'},
};

export default function BaselineTimeSeries({annual}:{annual:AnnualSummary|null|undefined}) {
  const [view,setView]=useState<ViewId>('supply');
  const selected=views[view];
  const rows=useMemo(()=>annual?.chart_data?.[selected.rows]||[],[annual,selected.rows]);
  const supported=annual?.method==='quasi_dynamic_integration'&&rows.length>1;
  const lines=selected.series.filter(([key])=>rows.some(row=>typeof row[key]==='number'));
  const exportCsv=()=>{
    if(!supported)return;
    const keys=['period',...lines.map(([key])=>key)];
    const csv=[keys.join(','),...rows.map(row=>keys.map(key=>JSON.stringify(row[key]??'')).join(','))].join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');link.href=url;link.download=`greenhub-${view}-monthly.csv`;link.click();URL.revokeObjectURL(url);
  };
  return <section className="panel baseline-series" aria-label="Baseline monthly time series">
    <div className="baseline-series-head"><div><span className="eyebrow">Baseline · backend report</span><h2>{selected.title}</h2><p>{supported?`${selected.unit} · ${annual?.method_label}`:'Monthly process series are not available for this calculation.'}</p></div>
      <label>View<select value={view} onChange={event=>setView(event.target.value as ViewId)}>{Object.entries(views).map(([key,item])=><option key={key} value={key}>{item.title}</option>)}</select></label>
    </div>
    {supported&&lines.length?<><div className="baseline-series-chart" role="img" aria-label={`${selected.title}, ${selected.unit}`}><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{top:12,right:22,bottom:8,left:8}}><CartesianGrid stroke="#ded8d0" vertical={false}/><XAxis dataKey="period" tick={{fontSize:11}}/><YAxis unit={selected.unit.startsWith('m³')?' m³':''} tick={{fontSize:10}}/><Tooltip formatter={(value:number)=>[value.toLocaleString(undefined,{maximumFractionDigits:2}),selected.unit.split(' / ')[0]]}/><Legend/>{lines.map(([key,label],index)=><Line key={key} dataKey={key} name={label} type="monotone" stroke={index===0?selected.color:'#729ad2'} strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer></div><div className="baseline-series-footer"><span>Monthly values integrated from the selected model timesteps. No monthly TEA/LCA series are inferred.</span><button className="secondary" onClick={exportCsv}>Export CSV</button></div></>:<div className="empty-state"><strong>{annual?.method==='steady_state_annualization'?'Monthly profile not calculated':'Series unavailable for this route'}</strong><span>{annual?.basis||'Run the backend simulation to load real time-series values.'}</span></div>}
  </section>;
}
