import React, { useState } from 'react';
import { ProcessAreaInfo, UnitOperation, ProcessStream } from '../types';
import { Cpu, ArrowRight, Gauge, Thermometer, Zap, Layers } from 'lucide-react';

interface FlowsheetViewerProps {
  processAreas: Record<string, ProcessAreaInfo>;
  units: UnitOperation[];
  streams: ProcessStream[];
}

export const FlowsheetViewer: React.FC<FlowsheetViewerProps> = ({ processAreas, units, streams }) => {
  const [selectedArea, setSelectedArea] = useState<string>('nutrient_recovery');
  const [selectedUnit, setSelectedUnit] = useState<UnitOperation | null>(null);

  const activeArea = processAreas[selectedArea] || Object.values(processAreas)[0];
  const areaUnits = units.filter((u) => u.area === selectedArea);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Process Flowsheet & Unit Operations Navigator
          </h2>
        </div>
      </div>

      {/* Process Area Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 border-b border-slate-800/80">
        {Object.values(processAreas).map((area) => {
          const isSelected = selectedArea === area.id;
          return (
            <button
              key={area.id}
              onClick={() => {
                setSelectedArea(area.id);
                setSelectedUnit(null);
              }}
              className={`px-3.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition cursor-pointer ${
                isSelected
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {area.name}
            </button>
          );
        })}
      </div>

      {/* Active Area Info */}
      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 mb-4">
        <p className="text-xs text-slate-300 leading-relaxed">{activeArea?.description}</p>
      </div>

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
                  : isSelected
                  ? 'bg-emerald-500/10 border-emerald-500/60 ring-1 ring-emerald-500/30'
                  : 'bg-slate-950 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-bold text-emerald-400">{unit.id}</span>
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
              </div>
              <h3 className="text-xs font-semibold text-white mb-2">{unit.name}</h3>
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                <div className="flex items-center gap-1">
                  <Zap className="w-3 h-3 text-amber-400" />
                  <span>{unit.power_kw} kW power</span>
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

      {/* Unit Operations Details modal/panel */}
      {selectedUnit && (
        <div className="bg-slate-950 border border-emerald-500/30 rounded-xl p-4 animate-fade-in">
          <div className="flex items-center justify-between mb-2 border-b border-slate-800 pb-2">
            <h4 className="text-xs font-bold font-mono text-emerald-400">
              Unit Detail: {selectedUnit.id} - {selectedUnit.name}
            </h4>
            <button
              onClick={() => setSelectedUnit(null)}
              className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer"
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">Equipment Type:</span>
              <span className="text-slate-200 font-semibold">{selectedUnit.type}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Thermal Duty:</span>
              <span className="text-amber-400 font-semibold">{selectedUnit.duty_kw} kW</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Operating Pressure:</span>
              <span className="text-cyan-400 font-semibold">{selectedUnit.pressure_bar} bar</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Operating Status:</span>
              <span className="text-emerald-400 font-semibold">{selectedUnit.status}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
