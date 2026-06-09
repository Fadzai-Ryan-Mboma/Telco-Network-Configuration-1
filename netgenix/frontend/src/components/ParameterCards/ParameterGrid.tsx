import { Signal, ArrowUpRight, Clock, Wifi, FileText } from 'lucide-react';
import ParameterCard from './ParameterCard';
import type { SiteParameters } from '../../services/api';

interface ParameterGridProps {
  parameters: SiteParameters | null;
  loading?: boolean;
}

export default function ParameterGrid({ parameters, loading }: ParameterGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="w-8 h-8 bg-white/5 rounded-lg mb-3" />
            <div className="h-8 bg-white/5 rounded w-20 mb-2" />
            <div className="h-3 bg-white/5 rounded w-24" />
          </div>
        ))}
      </div>
    );
  }

  const params = parameters?.parameters;

  return (
    <div className="grid grid-cols-5 gap-4">
      <ParameterCard
        icon={Signal}
        value={params?.reference_signal_power_pdschcfg?.value ?? null}
        unit="dBm"
        label="Signal Power"
        iconColor="text-accent-teal"
      />
      <ParameterCard
        icon={ArrowUpRight}
        value={params?.a3_event_offset?.value ?? null}
        unit="dB"
        label="A3 Offset"
        iconColor="text-accent-green"
      />
      <ParameterCard
        icon={Clock}
        value={params?.t310_timer?.value ?? null}
        unit="ms"
        label="T310 Timer"
        iconColor="text-accent-purple"
      />
      <ParameterCard
        icon={Wifi}
        value={params?.p0_nominal_pusch?.value ?? null}
        unit="dBm"
        label="P0 PUSCH"
        iconColor="text-accent-teal"
      />
      <ParameterCard
        icon={FileText}
        value={params?.pdcch_aggregation_level?.value ?? null}
        unit=""
        label="PDCCH AGG"
        iconColor="text-accent-green"
      />
    </div>
  );
}
