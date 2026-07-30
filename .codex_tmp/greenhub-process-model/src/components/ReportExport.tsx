import React from 'react';
import { ProcessStream, SimulationResult } from '../types';
import { FileSpreadsheet, Download, Table, FileText } from 'lucide-react';

interface ReportExportProps {
  simulationResult: SimulationResult;
}

export const ReportExport: React.FC<ReportExportProps> = ({ simulationResult }) => {
  const downloadJSON = () => {
    const jsonStr = JSON.stringify(simulationResult, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `greenhub_simulation_${simulationResult.run_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadCSVStreams = () => {
    const headers = ['Stream ID', 'Name', 'Origin', 'Destination', 'Mass Flow (kg/h)', 'Dry Solids (%)', 'COD (kg/h)', 'N (kg/h)', 'P (kg/h)', 'K (kg/h)'];
    const rows = simulationResult.streams.map((s) => [
      s.id,
      `"${s.name}"`,
      s.origin,
      s.destination,
      s.mass_flow_kgh,
      s.dry_solids_pct,
      s.cod_kgh,
      s.nitrogen_kgh,
      s.phosphorus_kgh,
      s.potassium_kgh
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `greenhub_streams_${simulationResult.run_id}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Stream Table & Integrated Report Export
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={downloadCSVStreams}
            className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-700 transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            Export Stream CSV
          </button>
          <button
            onClick={downloadJSON}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow transition cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            Export Run JSON
          </button>
        </div>
      </div>

      {/* Stream Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-xs text-left text-slate-300 font-mono">
          <thead className="bg-slate-950 text-slate-400">
            <tr>
              <th className="p-2.5">Stream ID</th>
              <th className="p-2.5">Name</th>
              <th className="p-2.5">Origin → Destination</th>
              <th className="p-2.5 text-right">Mass Flow (kg/h)</th>
              <th className="p-2.5 text-right">TS (%)</th>
              <th className="p-2.5 text-right">COD (kg/h)</th>
              <th className="p-2.5 text-right">N (kg/h)</th>
              <th className="p-2.5 text-right">P (kg/h)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {simulationResult.streams.map((stream) => (
              <tr key={stream.id} className="hover:bg-slate-950/40">
                <td className="p-2.5 font-bold text-emerald-400">{stream.id}</td>
                <td className="p-2.5 font-semibold text-white font-sans">{stream.name}</td>
                <td className="p-2.5 text-slate-400 text-[11px]">
                  {stream.origin} → {stream.destination}
                </td>
                <td className="p-2.5 text-right text-slate-200">{stream.mass_flow_kgh.toFixed(1)}</td>
                <td className="p-2.5 text-right text-slate-400">{stream.dry_solids_pct.toFixed(1)}%</td>
                <td className="p-2.5 text-right text-cyan-400">{stream.cod_kgh.toFixed(1)}</td>
                <td className="p-2.5 text-right text-purple-400">{stream.nitrogen_kgh.toFixed(2)}</td>
                <td className="p-2.5 text-right text-amber-400">{stream.phosphorus_kgh.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
