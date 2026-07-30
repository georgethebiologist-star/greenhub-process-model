import React, { useState } from 'react';
import { ProcessAreaInfo, UnitOperation, ProcessStream } from '../types';
import { Layers, Thermometer, Zap, Activity, Info, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { TooltipInfo } from './TooltipInfo';

interface FlowsheetViewerProps {
  processAreas: Record<string, ProcessAreaInfo>;
  units: UnitOperation[];
  streams: ProcessStream[];
}

export const FlowsheetViewer: React.FC<FlowsheetViewerProps> = ({ processAreas, units, streams }) => {
  const [selectedArea, setSelectedArea] = useState<string>('front_end');
  const [selectedUnit, setSelectedUnit] = useState<UnitOperation | null>(null);

  const activeArea = processAreas[selectedArea] || Object.values(processAreas)[0];
  const areaUnits = units.filter((u) => u.area === selectedArea);
  const areaStreams = streams.filter(
    (s) =>
      areaUnits.some((u) => s.origin.includes(u.id) || s.destination.includes(u.id)) ||
      (selectedArea === 'front_end' && s.id.includes('FEED') || s.id.includes('FRONT')) ||
      (selectedArea === 'protein_recovery' && s.id.includes('PROTEIN') || s.id.includes('PR')) ||
      (selectedArea === 'anaerobic_digestion' && s.id.includes('AD') || s.id.includes('RAW-BIOGAS')) ||
      (selectedArea === 'biogas_upgrading' && s.id.includes('BIOMETHANE')) ||
      (selectedArea === 'nutrient_recovery' && s.id.includes('STRUVITE') || s.id.includes('AMMONIUM') || s.id.includes('EFFLUENT'))
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Integrated Flowsheet & Unit Operations Navigator
          </h2>
          <TooltipInfo
            title="Flowsheet & Unit Operations Navigator"
            content="Displays the active BioSTEAM unit operation equipment tree, operational status (active, bypass, disabled), thermal duty, power consumption, and stream connections across all 5 process phases."
          />
        </div>
        <div className="text-xs text-slate-400 font-mono">
          Total Units: <strong className="text-emerald-400">{units.length}</strong> | Active:{' '}
          <strong className="text-emerald-400">
            {units.filter((u) => u.status === 'active').length}
          </strong>
        </div>
      </div>

      {/* Process Area Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 border-b border-slate-800/80">
        {Object.values(processAreas).map((area) => {
          const isSelected = selectedArea === area.id;
          const count = units.filter((u) => u.area === area.id && u.status === 'active').length;
          return (
            <button
              key={area.id}
              onClick={() => {
                setSelectedArea(area.id);
                setSelectedUnit(null);
              }}
              className={`px-3.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition cursor-pointer flex items-center gap-2 ${
                isSelected
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <span>{area.name}</span>
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 font-mono">
                {count} active
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Area Details & Assumptions */}
      {activeArea && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 mb-4">
          <h3 className="text-xs font-bold text-emerald-400 mb-1">{activeArea.name}</h3>
          <p className="text-xs text-slate-300 leading-relaxed mb-3">{activeArea.description}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] pt-2 border-t border-slate-800/80">
            <div>
              <span className="font-semibold text-slate-300 block mb-1">Key Modeling Assumptions:</span>
              <ul className="list-disc list-inside text-slate-400 space-y-0.5">
                {activeArea.key_assumptions.map((ass, i) => (
                  <li key={i}>{ass}</li>
                ))}
              </ul>
            </div>
            <div>
              <span className="font-semibold text-slate-300 block mb-1">Process Limitations & Constraints:</span>
              <ul className="list-disc list-inside text-slate-400 space-y-0.5">
                {activeArea.limitations.map((lim, i) => (
                  <li key={i}>{lim}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Unit Operations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
        {areaUnits.map((unit) => {
          const isSelected = selectedUnit?.id === unit.id;
          return (
            <div
              key={unit.id}
              onClick={() => setSelectedUnit(unit)}
              className={`p-4 rounded-xl border transition cursor-pointer ${
                unit.status === 'disabled'
                  ? 'bg-slate-950/40 border-slate-900 opacity-60'
                  : unit.status === 'bypass'
                  ? 'bg-amber-950/20 border-amber-800/40'
                  : isSelected
                  ? 'bg-emerald-500/10 border-emerald-500/60 ring-1 ring-emerald-500/30'
                  : 'bg-slate-950 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-emerald-400">{unit.id}</span>
                <div className="flex items-center gap-1">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                      unit.status === 'active'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                        : unit.status === 'bypass'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                        : 'bg-slate-800 text-slate-500 border-slate-700'
                    }`}
                  >
                    {unit.status}
                  </span>
                  {unit.status_reason && (
                    <TooltipInfo title={`Unit ${unit.id} Status`} content={unit.status_reason} />
                  )}
                </div>
              </div>
              <h3 className="text-xs font-semibold text-white mb-2">{unit.name}</h3>
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                <div className="flex items-center gap-1">
                  <Zap className="w-3 h-3 text-amber-400" />
                  <span>{unit.power_kw.toFixed(1)} kW power</span>
                </div>
                <div className="flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-red-400" />
                  <span>{unit.temperature_c}°C</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Unit Details Modal / Box */}
      {selectedUnit && (
        <div className="bg-slate-950 border border-emerald-500/40 rounded-xl p-4 mb-4 animate-fade-in">
          <div className="flex items-center justify-between mb-2 border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold font-mono text-emerald-400">
                Equipment Specs: {selectedUnit.id} - {selectedUnit.name}
              </span>
            </div>
            <button
              onClick={() => setSelectedUnit(null)}
              className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer"
            >
              Close Detail
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">Equipment Type:</span>
              <span className="text-slate-200 font-semibold">{selectedUnit.type}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Electrical Load:</span>
              <span className="text-amber-400 font-semibold">{selectedUnit.power_kw.toFixed(1)} kW</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Thermal Duty:</span>
              <span className="text-red-400 font-semibold">{selectedUnit.duty_kw.toFixed(1)} kW</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Operating Pressure:</span>
              <span className="text-cyan-400 font-semibold">{selectedUnit.pressure_bar} bar</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Status:</span>
              <span className="text-emerald-400 font-semibold">{selectedUnit.status}</span>
            </div>
          </div>
          {selectedUnit.status_reason && (
            <p className="text-[11px] text-amber-300 mt-2 pt-2 border-t border-slate-800/80">
              Note: {selectedUnit.status_reason}
            </p>
          )}
        </div>
      )}

      {/* Area Streams Table */}
      <div className="mt-4">
        <h3 className="text-xs font-bold text-slate-300 mb-2">Area Inter-Unit Stream Connections</h3>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-xs text-left text-slate-300 font-mono">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="p-2.5">Stream ID</th>
                <th className="p-2.5">Name</th>
                <th className="p-2.5">Origin → Destination</th>
                <th className="p-2.5 text-right">Mass Flow (kg/h)</th>
                <th className="p-2.5 text-right">Dry Solids (%)</th>
                <th className="p-2.5 text-right">COD (kg/h)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {areaStreams.map((s) => (
                <tr key={s.id} className="hover:bg-slate-950/40">
                  <td className="p-2.5 font-bold text-emerald-400">{s.id}</td>
                  <td className="p-2.5 font-semibold text-white font-sans">{s.name}</td>
                  <td className="p-2.5 text-slate-400 text-[11px]">
                    {s.origin} → {s.destination}
                  </td>
                  <td className="p-2.5 text-right text-slate-200">{s.mass_flow_kgh.toFixed(1)}</td>
                  <td className="p-2.5 text-right text-slate-400">{s.dry_solids_pct.toFixed(1)}%</td>
                  <td className="p-2.5 text-right text-cyan-400">{s.cod_kgh.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
