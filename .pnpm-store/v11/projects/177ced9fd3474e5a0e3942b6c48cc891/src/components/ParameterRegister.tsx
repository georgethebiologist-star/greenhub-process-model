import React, { useState } from 'react';
import { ParameterDefinition } from '../types';
import { Sliders, Search, RotateCcw, Code, CheckCircle2, AlertCircle, Info, ShieldAlert } from 'lucide-react';
import { TooltipInfo } from './TooltipInfo';

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
  const [activeCategory, setActiveCategory] = useState<'all' | 'basic' | 'advanced'>('all');
  const [showTechnicalIds, setShowTechnicalIds] = useState<boolean>(false);

  const filteredParams = parameters.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.parameter_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesArea = filterArea === 'all' || p.process_area === filterArea;
    const matchesCategory = activeCategory === 'all' || p.category === activeCategory;
    return matchesSearch && matchesArea && matchesCategory;
  });

  const qualityClassExplanations = (
    <div className="space-y-1.5 text-[11px]">
      <p><strong className="text-emerald-400">Class A (Experimental / Verified):</strong> Measured lab data or active PID loops with direct verification (&lt;5% uncertainty).</p>
      <p><strong className="text-cyan-400">Class B (Literature Benchmark):</strong> Peer-reviewed published bioprocess literature constants (e.g. BioSTEAM/REC-001).</p>
      <p><strong className="text-amber-400">Class C (Pilot Estimated):</strong> Estimated from pilot-scale equipment or engineering scaling curves.</p>
      <p><strong className="text-purple-400">Class D (Quarantined):</strong> High uncertainty or unverified data requiring user review.</p>
      <p><strong className="text-rose-400">Class E (Structural Assumption):</strong> Baseline physical assumption when experimental data is absent.</p>
    </div>
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold text-white">
            Canonical Parameter Registry & Design Overrides
          </h2>
          <TooltipInfo
            title="Data Quality Classes & Governance"
            content={qualityClassExplanations}
          />
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Toggle Technical Parameter IDs */}
          <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 cursor-pointer hover:border-slate-700">
            <input
              type="checkbox"
              checked={showTechnicalIds}
              onChange={(e) => setShowTechnicalIds(e.target.checked)}
              className="accent-emerald-500 cursor-pointer"
            />
            <Code className="w-3.5 h-3.5 text-emerald-400" />
            <span>Show Technical Parameter IDs</span>
          </label>

          {/* Reset All Defaults */}
          <button
            onClick={onResetDefaults}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset All Defaults
          </button>
        </div>
      </div>

      {/* Category Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 mb-4">
        {/* Basic / Advanced Category Buttons */}
        <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl p-1">
          {[
            { id: 'all', label: 'All Parameters' },
            { id: 'basic', label: 'Basic Controls' },
            { id: 'advanced', label: 'Advanced Kinetics & Thermodynamics' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id as any)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                activeCategory === cat.id
                  ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 flex-1 md:max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search parameters by name or description..."
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
            <option value="front_end">1. Front-End</option>
            <option value="protein_recovery">2. Protein Recovery</option>
            <option value="anaerobic_digestion">3. AD Digestion</option>
            <option value="biogas_upgrading">4. Biogas Upgrading</option>
            <option value="nutrient_recovery">5. Nutrient Recovery</option>
          </select>
        </div>
      </div>

      {/* Parameter Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-xs text-left text-slate-300">
          <thead className="bg-slate-950 text-slate-400">
            <tr>
              <th className="p-3">Parameter Name & Description</th>
              <th className="p-3">Category</th>
              <th className="p-3">Quality Class</th>
              <th className="p-3 text-right">Current Value & Unit</th>
              <th className="p-3 text-right">Default Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredParams.map((param) => {
              const isModified = param.current_value !== param.default_value;
              return (
                <tr key={param.parameter_id} className="hover:bg-slate-950/40">
                  <td className="p-3 max-w-md">
                    <div className="font-bold text-white font-sans text-xs">{param.name}</div>
                    {showTechnicalIds && (
                      <div className="font-mono text-[10px] text-emerald-400 mt-0.5">
                        ID: {param.parameter_id}
                      </div>
                    )}
                    <div className="text-[11px] text-slate-400 leading-snug mt-1 font-sans">
                      {param.description}
                    </div>
                    {param.notes && (
                      <div className="text-[10px] text-slate-500 italic mt-0.5">
                        {param.notes}
                      </div>
                    )}
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        param.category === 'basic'
                          ? 'bg-slate-800 text-slate-300'
                          : 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                      }`}
                    >
                      {param.category === 'basic' ? 'Basic' : 'Advanced'}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-1">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                          param.quality_class === 'A'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : param.quality_class === 'B'
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                            : param.quality_class === 'C'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : param.quality_class === 'D'
                            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        Class {param.quality_class}
                      </span>
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-1.5 font-mono">
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
                          className={`w-28 bg-slate-950 border px-2 py-1 rounded text-right text-xs font-mono font-bold focus:outline-none ${
                            isModified
                              ? 'border-amber-500 text-amber-400 ring-1 ring-amber-500/30'
                              : 'border-slate-800 text-emerald-400'
                          }`}
                        />
                      ) : (
                        <span className="font-bold text-white font-mono">{String(param.current_value)}</span>
                      )}
                      <span className="text-slate-500 text-[10px] font-mono">{param.unit}</span>
                    </div>
                  </td>
                  <td className="p-3 text-right text-slate-500 text-[11px] font-mono">
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
