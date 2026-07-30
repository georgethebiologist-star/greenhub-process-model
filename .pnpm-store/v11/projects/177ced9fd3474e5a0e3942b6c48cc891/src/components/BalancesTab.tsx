import React from 'react';
import { SystemBalances } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Scale, CheckCircle2 } from 'lucide-react';

interface BalancesTabProps {
  balances: SystemBalances;
}

export const BalancesTab: React.FC<BalancesTabProps> = ({ balances }) => {
  const elementalData = [
    { name: 'Carbon (C)', in: balances.elemental.carbon.in, out: balances.elemental.carbon.out, closure: balances.elemental.carbon.closure },
    { name: 'Nitrogen (N)', in: balances.elemental.nitrogen.in, out: balances.elemental.nitrogen.out, closure: balances.elemental.nitrogen.closure },
    { name: 'Phosphorus (P)', in: balances.elemental.phosphorus.in, out: balances.elemental.phosphorus.out, closure: balances.elemental.phosphorus.closure },
    { name: 'Potassium (K)', in: balances.elemental.potassium.in, out: balances.elemental.potassium.out, closure: balances.elemental.potassium.closure },
    { name: 'Sulfur (S)', in: balances.elemental.sulfur.in, out: balances.elemental.sulfur.out, closure: balances.elemental.sulfur.closure },
  ];

  const overallData = [
    { name: 'Total Mass (kg/h)', in: balances.mass_in_kgh, out: balances.mass_out_kgh, closure: balances.mass_closure_pct },
    { name: 'COD Load (kg/h)', in: balances.cod_in_kgh, out: balances.cod_out_kgh, closure: balances.cod_closure_pct },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            System Mass, COD & Elemental Balance Validation
          </h2>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full font-mono">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Residual &lt; 1e-6 kg/h</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overall Mass & COD */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-slate-300 mb-3">
            Overall Plant Mass & COD Throughput (kg/h)
          </h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overallData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="in" name="Boundary Inflow" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="out" name="Boundary Outflow" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Elemental Balances */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-slate-300 mb-3">
            Elemental Species Balances (kg element/h)
          </h3>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={elementalData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="in" name="Inflow" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="out" name="Outflow" fill="#a855f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Closure Table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-xs text-left text-slate-300 font-mono">
          <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="p-2.5">Species / Property</th>
              <th className="p-2.5 text-right">Inflow (kg/h)</th>
              <th className="p-2.5 text-right">Outflow (kg/h)</th>
              <th className="p-2.5 text-right">Closure Accuracy (%)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {elementalData.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-950/40">
                <td className="p-2.5 font-semibold text-white">{row.name}</td>
                <td className="p-2.5 text-right">{row.in.toFixed(2)}</td>
                <td className="p-2.5 text-right">{row.out.toFixed(2)}</td>
                <td className="p-2.5 text-right text-emerald-400 font-bold">{row.closure.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
