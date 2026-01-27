import type { LucideIcon } from 'lucide-react';

interface ParameterCardProps {
  icon: LucideIcon;
  value: number | string | null;
  unit: string;
  label: string;
  iconColor?: string;
}

export default function ParameterCard({
  icon: Icon,
  value,
  unit,
  label,
  iconColor = 'text-accent-teal'
}: ParameterCardProps) {
  return (
    <div className="card flex flex-col gap-3">
      <div className={`w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center ${iconColor}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-white">
            {value !== null ? value : 'N/A'}
          </span>
          {unit && <span className="text-sm text-gray-400">{unit}</span>}
        </div>
        <div className="text-xs text-gray-500 uppercase tracking-wider mt-1">
          {label}
        </div>
      </div>
    </div>
  );
}
