import React, { useState } from 'react';
import { PlotCatalogItem, ScenarioComparisonItem } from '../types';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  Cell
} from 'recharts';
import { Activity, BarChart3, LineChart as LineChartIcon, PieChart, Layers, Scale, ShieldCheck, Zap } from 'lucide-react';
import { TooltipInfo } from './TooltipInfo';

interface PlotCatalogProps {
  plots: PlotCatalogItem[];
  scenarioComparisons?: ScenarioComparisonItem[];
}

export const PlotCatalog: React.FC<PlotCatalogProps> = ({ plots, scenarioComparisons = [] }) => {
  const [activePlotId, setActivePlotId] = useState<string>(plots[0]?.id || 'SANKEY-FLOWS');

  const activePlot = plots.find((p) => p.id === activePlotId) || plots[0];

  const categoryIcons: Record<string, any> = {
    'Mass & Stream Balance': Scale,
    'Nutrient Recovery': BarChart3,
    'Process Organics': PieChart,
    'Seasonal Dynamics': LineChartIcon,
    'Energy Balance': Zap,
    'Equipment Analysis': Layers,
    'Validation & Quality': ShieldCheck,
    'Data Governance': Activity
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Scientific Decision-Support Plot & Analytics Center
          </h2>
          <TooltipInfo
            title="Scientific Plot Catalog"
            content="Interactive visualizations covering mass balances, nutrient fate (N, P, K), COD carbon allocation, 12-month seasonal dynamics, process utility hotspots, boundary validation residuals, and scenario trade-off comparison matrixes."
          />
        </div>
      </div>

      {/* Plot Selector Buttons */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 border-b border-slate-800/80">
        {plots.map((plot) => {
          const isSelected = activePlotId === plot.id;
          const Icon = categoryIcons[plot.category] || Activity;
          return (
            <button
              key={plot.id}
              onClick={() => setActivePlotId(plot.id)}
              className={`px-3 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition cursor-pointer flex items-center gap-1.5 ${
                isSelected
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{plot.title.split('(')[0]}</span>
            </button>
          );
        })}
        <button
          onClick={() => setActivePlotId('SCENARIO-MATRIX')}
          className={`px-3 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition cursor-pointer flex items-center gap-1.5 ${
            activePlotId === 'SCENARIO-MATRIX'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
              : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Scenario Trade-off Matrix</span>
        </button>
      </div>

      {/* Active Plot Render */}
      {activePlotId === 'SCENARIO-MATRIX' ? (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-white">Scenario Trade-off Comparison Matrix (NR0 - NR7)</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparative analysis of Biogas output, Protein recovery, Struvite yield, Ammonium Sulfate yield, Net Power balance, and Nutrient Recovery efficiencies.
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-800 mb-4">
            <table className="w-full text-xs text-left text-slate-300 font-mono">
              <thead className="bg-slate-900 text-slate-400">
                <tr>
                  <th className="p-2.5">Scenario Pathway</th>
                  <th className="p-2.5 text-right">Biogas (m³/h)</th>
                  <th className="p-2.5 text-right">Protein (kg/h)</th>
                  <th className="p-2.5 text-right">Struvite (kg/h)</th>
                  <th className="p-2.5 text-right">Ammonium Sulfate</th>
                  <th className="p-2.5 text-right">P Rec (%)</th>
                  <th className="p-2.5 text-right">N Rec (%)</th>
                  <th className="p-2.5 text-right">Net Power (kW)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {scenarioComparisons.map((sc) => (
                  <tr key={sc.scenario_id} className="hover:bg-slate-900/60">
                    <td className="p-2.5 font-bold text-white font-sans">{sc.title}</td>
                    <td className="p-2.5 text-right text-amber-400">{sc.biogas_m3h.toFixed(1)}</td>
                    <td className="p-2.5 text-right text-emerald-400">{sc.protein_kgh.toFixed(1)}</td>
                    <td className="p-2.5 text-right text-cyan-400">{sc.struvite_kgh.toFixed(1)}</td>
                    <td className="p-2.5 text-right text-purple-400">{sc.amsult_kgh.toFixed(1)} kg/h</td>
                    <td className="p-2.5 text-right text-emerald-400 font-bold">{sc.p_recovery_pct}%</td>
                    <td className="p-2.5 text-right text-purple-400 font-bold">{sc.n_recovery_pct}%</td>
                    <td className="p-2.5 text-right text-blue-400">{sc.net_power_kw.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Comparative Bar Chart */}
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scenarioComparisons} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="scenario_id" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} label={{ value: 'Efficiency %', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="p_recovery_pct" name="Phosphorus Recovery (%)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                <Bar dataKey="n_recovery_pct" name="Nitrogen Recovery (%)" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : activePlot && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
          <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white">{activePlot.title}</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                  {activePlot.category}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">{activePlot.description}</p>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {activePlot.type === 'line' ? (
                <LineChart data={activePlot.data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Line type="monotone" dataKey="biogas_m3h" name="Biogas (m³/h)" stroke="#f59e0b" strokeWidth={2.5} dot={{ fill: '#f59e0b', r: 4 }} />
                  <Line type="monotone" dataKey="protein_kgh" name="Protein (kg/h)" stroke="#10b981" strokeWidth={2.5} dot={{ fill: '#10b981', r: 4 }} />
                  <Line type="monotone" dataKey="struvite_kgh" name="Struvite (kg/h)" stroke="#06b6d4" strokeWidth={2.5} dot={{ fill: '#06b6d4', r: 4 }} />
                </LineChart>
              ) : activePlot.id === 'NUTRIENT-FATE' ? (
                <BarChart data={activePlot.data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="element" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="recovered_pct" name="Recovered Product (%)" fill="#10b981" stackId="a" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="unrecovered_pct" name="Residual Effluent Loss (%)" fill="#64748b" stackId="a" radius={[4, 4, 0, 0]} />
                </BarChart>
              ) : activePlot.id === 'UTILITY-HOTSPOTS' || activePlot.id === 'UNIT-HOTSPOTS' ? (
                <BarChart data={activePlot.data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey={activePlot.id === 'UTILITY-HOTSPOTS' ? 'area' : 'unit'} stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} label={{ value: 'kW', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="power_kw" name="Electrical Power (kW)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="duty_kw" name="Thermal Heat Duty (kW)" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              ) : (
                <BarChart data={activePlot.data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey={Object.keys(activePlot.data[0] || {})[0]} stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey={Object.keys(activePlot.data[0] || {})[1]} fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
