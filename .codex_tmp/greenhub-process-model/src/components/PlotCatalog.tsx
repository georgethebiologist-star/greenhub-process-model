import React, { useState } from 'react';
import { PlotCatalogItem } from '../types';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { LineChart as LineChartIcon, PieChart, Activity } from 'lucide-react';

interface PlotCatalogProps {
  plots: PlotCatalogItem[];
}

export const PlotCatalog: React.FC<PlotCatalogProps> = ({ plots }) => {
  const [activePlotId, setActivePlotId] = useState<string>(plots[0]?.id || 'DATA-READINESS');

  const activePlot = plots.find((p) => p.id === activePlotId) || plots[0];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Scientific Plot Catalog & Analytics Center
          </h2>
        </div>
      </div>

      {/* Plot Buttons */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4">
        {plots.map((plot) => {
          const isSelected = activePlotId === plot.id;
          return (
            <button
              key={plot.id}
              onClick={() => setActivePlotId(plot.id)}
              className={`px-3.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition cursor-pointer ${
                isSelected
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {plot.title}
            </button>
          );
        })}
      </div>

      {/* Active Plot Content */}
      {activePlot && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
          <div className="mb-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white">{activePlot.title}</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {activePlot.category}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{activePlot.description}</p>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {activePlot.id === 'PR-PRECIP-RECOVERY' ? (
                <LineChart data={activePlot.data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="pH" stroke="#64748b" fontSize={11} label={{ value: 'pH', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 11 }} />
                  <YAxis stroke="#64748b" fontSize={11} label={{ value: 'Yield %', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Line type="monotone" dataKey="yield_pct" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', r: 5 }} />
                </LineChart>
              ) : activePlot.id === 'DATA-READINESS' ? (
                <BarChart data={activePlot.data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="class" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="count" name="Dataset Count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
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
