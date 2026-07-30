import React from 'react';
import { RecoveryMetrics } from '../types';
import { Flame, Zap, Droplet, Leaf, Factory, ShieldCheck, Activity } from 'lucide-react';
import { TooltipInfo } from './TooltipInfo';

interface MetricsCardsProps {
  metrics: RecoveryMetrics;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics }) => {
  const cards = [
    {
      title: 'Raw Biogas & Biomethane',
      value: `${metrics.biogas_m3h.toFixed(1)} m³/h`,
      sub: `${metrics.biomethane_flow_m3h.toFixed(1)} m³/h biomethane (${metrics.methane_purity_pct.toFixed(1)}% CH₄)`,
      icon: Flame,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
      tooltip: 'Biogas production from CSTR digestion R301 and biomethane grid output after M401 membrane separation.'
    },
    {
      title: 'Leaf Protein Concentrate',
      value: `${metrics.protein_recovered_kgh.toFixed(1)} kg/h`,
      sub: `${metrics.protein_purity_pct.toFixed(1)}% dry purity from PR1/PR2`,
      icon: Leaf,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
      tooltip: 'Isoelectric/thermal precipitation yield of RuBisCO protein from press juice S101.'
    },
    {
      title: 'Struvite Yield (P basis)',
      value: `${metrics.struvite_yield_kgh.toFixed(1)} kg/h`,
      sub: `${metrics.p_recovery_pct.toFixed(0)}% P recovery efficiency`,
      icon: Droplet,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20',
      tooltip: 'MgNH4PO4·6H2O fertilizer crystals recovered from fluidized bed crystallizer R711.'
    },
    {
      title: 'Ammonium Sulfate (N basis)',
      value: `${metrics.ammonia_sulfate_kgh.toFixed(1)} kg/h`,
      sub: `${metrics.n_recovery_pct.toFixed(0)}% N recovery efficiency`,
      icon: Factory,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
      tooltip: '28% liquid (NH4)2SO4 solution produced by air stripping A721 & acid scrubber A722.'
    },
    {
      title: 'Net Power & Energy',
      value: `${metrics.net_power_kw.toFixed(1)} kW`,
      sub: `Heat demand: ${metrics.net_heat_kw.toFixed(0)} kW`,
      icon: Zap,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
      tooltip: 'Combined CHP electrical output minus total process parasitic load (pumps, centrifuges, compressors, blowers).'
    },
    {
      title: 'Data Readiness Score',
      value: `${metrics.data_readiness_score.toFixed(1)}%`,
      sub: `Class A-E verified parameters`,
      icon: ShieldCheck,
      color: 'text-teal-400',
      bg: 'bg-teal-500/10 border-teal-500/20',
      tooltip: 'Overall system data governance readiness score based on verified experimental data (Class A) vs literature or structural assumptions.'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border ${card.bg} flex flex-col justify-between transition-all hover:scale-[1.01]`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-300 truncate">{card.title}</span>
              <div className="flex items-center gap-1">
                <Icon className={`w-3.5 h-3.5 ${card.color}`} />
                <TooltipInfo title={card.title} content={card.tooltip} />
              </div>
            </div>
            <div>
              <div className="text-lg font-bold font-mono text-white mb-0.5">{card.value}</div>
              <p className="text-[10px] text-slate-400 leading-tight">{card.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
