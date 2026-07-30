import React from 'react';
import { RefreshCw, Layers, ShieldCheck, Activity, HelpCircle } from 'lucide-react';
import { CalculationMode } from '../types';
import { TooltipInfo } from './TooltipInfo';

interface HeaderProps {
  calculationMode: CalculationMode;
  setCalculationMode: (mode: CalculationMode) => void;
  selectedMonth: string;
  setSelectedMonth: (month: string) => void;
  onRunSimulation: () => void;
  isSimulating: boolean;
  dataReadinessScore: number;
}

export const Header: React.FC<HeaderProps> = ({
  calculationMode,
  setCalculationMode,
  selectedMonth,
  setSelectedMonth,
  onRunSimulation,
  isSimulating,
  dataReadinessScore,
}) => {
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 px-4 py-3 shadow-md">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Brand & Title */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-sans">
                GreenHub <span className="text-emerald-400 font-medium">BioSTEAM</span> Model
              </h1>
              <span className="px-2 py-0.5 text-xs font-mono font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full">
                v1.0.0 Integrated API
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Integrated Multi-Phase Process Configurator & Decision-Support System
            </p>
          </div>
        </div>

        {/* Global Controls & Actions */}
        <div className="flex items-center flex-wrap gap-3">
          {/* Month Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
            <span className="text-slate-500 font-medium">Seasonal Month:</span>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="bg-transparent text-emerald-400 font-medium focus:outline-none cursor-pointer"
            >
              {months.map((m) => (
                <option key={m} value={m} className="bg-slate-900 text-slate-200">
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Mode Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300">
            <span className="text-slate-500 font-medium">Mode:</span>
            <select
              value={calculationMode}
              onChange={(e) => setCalculationMode(e.target.value as CalculationMode)}
              className="bg-transparent text-emerald-400 font-medium focus:outline-none cursor-pointer"
            >
              <option value="literature_default" className="bg-slate-900 text-slate-200">
                Literature Default (REC-001)
              </option>
              <option value="structural" className="bg-slate-900 text-slate-200">
                Structural Baseline
              </option>
              <option value="calibrated" className="bg-slate-900 text-slate-200">
                Calibrated High-Quality
              </option>
            </select>
          </div>

          {/* Readiness Score */}
          <div className="flex items-center gap-1.5 bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            <span className="text-slate-400">Data Readiness:</span>
            <span className="font-mono font-bold text-teal-400">{dataReadinessScore.toFixed(1)}%</span>
            <TooltipInfo
              title="Data Governance & Readiness"
              content="The Data Readiness Score is calculated as a weighted percentage of parameters categorized in Quality Classes A (Experimental) and B (Literature) versus estimated or structural assumptions."
            />
          </div>

          {/* Run Button */}
          <button
            onClick={onRunSimulation}
            disabled={isSimulating}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1.5 rounded-lg font-medium text-xs shadow-md transition cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
            {isSimulating ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
      </div>
    </header>
  );
};
