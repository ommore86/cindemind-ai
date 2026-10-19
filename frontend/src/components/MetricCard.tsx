import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'amber' | 'cyan' | 'purple' | 'emerald' | 'rose';
  badge?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'amber',
  badge
}) => {
  const colorMap = {
    amber: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      text: 'text-amber-400',
      glow: 'hover:border-amber-500/40'
    },
    cyan: {
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/20',
      text: 'text-cyan-400',
      glow: 'hover:border-cyan-500/40'
    },
    purple: {
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/20',
      text: 'text-purple-400',
      glow: 'hover:border-purple-500/40'
    },
    emerald: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      text: 'text-emerald-400',
      glow: 'hover:border-emerald-500/40'
    },
    rose: {
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
      text: 'text-rose-400',
      glow: 'hover:border-rose-500/40'
    }
  };

  const scheme = colorMap[color] || colorMap.amber;

  return (
    <div className={`p-5 rounded-xl bg-slate-900/60 border ${scheme.border} ${scheme.glow} transition-all duration-300 shadow-lg shadow-slate-950/40 flex flex-col justify-between`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`w-9 h-9 rounded-lg ${scheme.bg} flex items-center justify-center ${scheme.text}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-4">
        <div className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-['Outfit']">
          {value}
        </div>
        {subtitle && (
          <p className="text-xs text-slate-400 mt-1 flex items-center justify-between">
            <span>{subtitle}</span>
            {badge && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${scheme.bg} ${scheme.text}`}>
                {badge}
              </span>
            )}
          </p>
        )}
      </div>
    </div>
  );
};
