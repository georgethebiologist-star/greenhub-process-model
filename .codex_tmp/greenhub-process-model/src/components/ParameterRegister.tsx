import React, { useState } from 'react';
import { ParameterDefinition } from '../types';
import { Search, Sliders, CheckCircle2, AlertCircle, Edit3, RotateCcw } from 'lucide-react';

interface ParameterRegisterProps {
  parameters: ParameterDefinition[];
  onUpdateParameter: (parameterId: string, newValue: number | string | boolean) => void;
  onResetDefaults: () => void;
}

export const ParameterRegister: React.FC<ParameterRegisterProps> = ({
  parameters,
  onUpdateParameter,
  onResetDefaults,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterArea, setFilterArea] = useState<string>('all');

  const filteredParams = parameters.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.parameter_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesArea = filterArea === 'all' || p.process_area === filterArea;
    return matchesSearch && matchesArea;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Canonical Parameter Registry & Design Overrides
          </h2>
        </div>
        <button
          onClick={onResetDefaults}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset All Defaults
        </button>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search parameters by ID, name, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
        <select
          value={filterArea}
          onChange={(e) => setFilterArea(e.target.value)}
          className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
        >
          <option value="all">All Process Areas</option>
          <option value="front_end">Front-End</option>
          <option value="protein_recovery">Protein Recovery</option>
          <option value="anaerobic_digestion">Anaerobic Digestion</option>
          <option value="biogas_upgrading">Biogas Upgrading</option>
          <option value="nutrient_recovery">Nutrient Recovery</option>
        </select>
      </div>

      {/* Parameter Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-xs text-left text-slate-300">
          <thead className="bg-slate-950 text-slate-400 font-mono">
            <tr>
              <th className="p-3">Parameter ID & Name</th>
              <th className="p-3">Process Area</th>
              <th className="p-3">Quality Class</th>
              <th className="p-3 text-right">Value & Unit</th>
              <th className="p-3 text-right">Default</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filteredParams.map((param) => {
              const isModified = param.current_value !== param.default_value;
              return (
                <tr key={param.parameter_id} className="hover:bg-slate-950/40">
                  <td className="p-3">
                    <div className="font-bold text-white font-sans">{param.name}</div>
                    <div className="text-[10px] text-emerald-400">{param.parameter_id}</div>
                    <div className="text-[11px] text-slate-400 font-sans mt-0.5">{param.description}</div>
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-300">
                      {param.process_area}
                    </span>
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        param.quality_class === 'A'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : param.quality_class === 'B'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      Class {param.quality_class}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {param.is_editable && typeof param.current_value === 'number' ? (
                        <input
                          type="number"
                          step="0.01"
                          min={param.min_value}
                          max={param.max_value}
                          value={param.current_value}
                          onChange={(e) =>
                            onUpdateParameter(param.parameter_id, parseFloat(e.target.value) || 0)
                          }
                          className={`w-24 bg-slate-950 border px-2 py-1 rounded text-right text-xs font-mono font-bold focus:outline-none ${
                            isModified
                              ? 'border-amber-500 text-amber-400'
                              : 'border-slate-800 text-emerald-400'
                          }`}
                        />
                      ) : (
                        <span className="font-bold text-white">{String(param.current_value)}</span>
                      )}
                      <span className="text-slate-500 text-[10px]">{param.unit}</span>
                    </div>
                  </td>
                  <td className="p-3 text-right text-slate-500 text-[11px]">
                    {String(param.default_value)} {param.unit}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
