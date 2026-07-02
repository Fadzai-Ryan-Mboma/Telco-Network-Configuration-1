import type { LucideIcon } from 'lucide-react';

interface ParameterCardProps {
  icon: LucideIcon;
  value: number | string | null;
  unit: string;
  label: string;
  category?: string | null;
  source?: string;
  iconColor?: string;
}

export default function ParameterCard({
  icon: Icon,
  value,
  unit,
  label,
  category,
  source,
  iconColor = 'text-accent-teal'
}: ParameterCardProps) {
  return (
    <div className="card flex min-h-[116px] flex-col gap-3">
      <div className={`w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center ${iconColor}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <div className="flex min-w-0 items-baseline gap-1">
          <span className="min-w-0 break-words text-xl font-bold text-white xl:text-2xl">
            {value !== null ? value : 'N/A'}
          </span>
          {unit && <span className="text-sm text-gray-400">{unit}</span>}
        </div>
        <div className="mt-1 text-xs uppercase text-gray-500">
          {label}
        </div>
        {category && <div className="mt-1 text-[11px] text-gray-600">{category}</div>}
        <div className="mt-2 text-[10px] uppercase text-gray-500">
          {source === 'live_api'
            ? 'Live NBI'
            : source === 'database'
              ? 'Saved snapshot'
              : source === 'change_history'
                ? 'Change history'
                : 'No snapshot'}
        </div>
      </div>
    </div>
  );
}
