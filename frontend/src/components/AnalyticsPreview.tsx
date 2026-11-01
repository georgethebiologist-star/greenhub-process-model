import React,{useMemo} from 'react';
import {Bar,BarChart,CartesianGrid,Legend,ReferenceLine,ResponsiveContainer,Scatter,ScatterChart,Tooltip,XAxis,YAxis} from 'recharts';
import paretoSnapshot from '../data/actualParetoPreview.json';

type View='hotspots'|'optimization';
type ObjectivePoint={sample_id:string;x:number;y:number;pareto?:boolean};
const euro=(v:number)=>new Intl.NumberFormat(undefined,{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(v);
const compact=(v:number)=>Math.abs(v)>=1e6?`${(v/1e6).toFixed(1)}m`:Math.abs(v)>=1000?`${(v/1000).toFixed(0)}k`:String(Math.round(v));

// Means are computed from the persisted 2,000-candidate backend batch.
const overlayMeans=[
  {name:'Subsidy rate',value:20},
  {name:'Eligible CAPEX',value:35},
  {name:'Labour saving',value:15.12},
  {name:'Logistics saving',value:12.45},
  {name:'Energy saving',value:12.37},
  {name:'Protein yield uplift',value:9.93},
  {name:'Nutrient recovery',value:7.54},
];

export default function AnalyticsPreview({view}:{view:View}) {
  const points=useMemo(()=>{
    const cloud=(paretoSnapshot.cloud as ObjectivePoint[]).map(p=>({...p,pareto:false}));
    const front=cloud.filter(p=>!cloud.some(q=>q.sample_id!==p.sample_id&&q.x>=p.x&&q.y<=p.y&&(q.x>p.x||q.y<p.y)));
    const ids=new Set(front.map(p=>p.sample_id));
    return cloud.map(p=>({...p,pareto:ids.has(p.sample_id)}));
  },[]);
  const front=points.filter(p=>p.pareto);
  const ordinary=points.filter(p=>!p.pareto);

  return <section className="panel analytics-preview" aria-label={view==='optimization'?'BioSTEAM Pareto optimization':'BioSTEAM optimization hotspots'}>
    <div className="analytics-preview-top"><span className="ds-badge">BIOSTEAM · 2,000 SCENARIOS · PARTIAL LCA</span><span className="analytics-preview-meta">20% subsidy · 35% eligible CAPEX · 25.8% tax</span></div>
    {view==='optimization'?<div className="analytics-preview-chart" role="img" aria-label="BioSTEAM Pareto scatter chart of annual profit versus climate impact">
      <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:20,right:28,bottom:34,left:28}}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--line)"/>
        <XAxis type="number" dataKey="x" name="After-tax profit" tickFormatter={compact} unit=" EUR/year" tick={{fontSize:11}} label={{value:'After-tax profit (EUR/year) · maximize',position:'insideBottom',offset:-22,fontSize:12}}/>
        <YAxis type="number" dataKey="y" name="Climate impact" tickFormatter={compact} unit=" kg CO₂e/year" tick={{fontSize:11}} label={{value:'Climate impact (kg CO₂e/year) · minimize',angle:-90,position:'insideLeft',fontSize:12}}/>
        <Tooltip formatter={(value:any,name:any)=>[name==='After-tax profit'?euro(Number(value)):`${compact(Number(value))} kg CO₂e/year`,name]} labelFormatter={(_,payload:any[])=>payload?.[0]?.payload?.sample_id||''}/>
        <Legend verticalAlign="top" height={32}/><ReferenceLine x={0} stroke="#819188"/>
        <Scatter name="Backend scenarios" data={ordinary} fill="#5f8bb5" fillOpacity={0.45} isAnimationActive={false}/>
        <Scatter name="Sampled Pareto front" data={front} fill="#bd7837" isAnimationActive={false}/>
      </ScatterChart></ResponsiveContainer>
    </div>:<>
      <h2 className="analytics-preview-title">Optimization assumptions · mean across scenarios</h2>
      <div className="analytics-preview-hotspots"><ResponsiveContainer width="100%" height="100%"><BarChart data={overlayMeans} layout="vertical" margin={{top:8,right:34,bottom:8,left:18}}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--line)"/>
        <XAxis type="number" domain={[0,40]} tickFormatter={value=>`${value}%`} tick={{fontSize:11}}/>
        <YAxis type="category" dataKey="name" width={120} tick={{fontSize:12}}/>
        <Tooltip formatter={(value:any)=>[`${Number(value).toFixed(1)}%`,'Mean per scenario']}/>
        <Bar dataKey="value" name="Assumption (%)" fill="#527d5e" radius={[0,5,5,0]}/>
      </BarChart></ResponsiveContainer></div>
    </>}
    <div className="analytics-preview-footer">{view==='optimization'?`${paretoSnapshot.cloud.length} plotted · ${front.length} nondominated in plotted sample`:'2,000 backend candidates · assumptions, not verified performance.'}</div>
  </section>;
}
