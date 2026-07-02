import {
  Activity,
  ArrowUpRight,
  Clock,
  FileText,
  Gauge,
  Hash,
  Radio,
  Router,
  Signal,
  ToggleLeft,
  Wifi
} from 'lucide-react';
import ParameterCard from './ParameterCard';
import type { ParameterValue, SiteParameters } from '../../services/api';

interface ParameterGridProps {
  parameters: SiteParameters | null;
  loading?: boolean;
}

export default function ParameterGrid({ parameters, loading }: ParameterGridProps) {
  const cardCount = 5;

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[...Array(cardCount)].map((_, i) => (
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
  const fallbackOrder = [
    'reference_signal_power_pdschcfg',
    'a3_event_offset',
    't310_timer',
    'p0_nominal_pusch',
    'pdcch_aggregation_level'
  ];
  const fallbackLabels: Record<string, string> = {
    reference_signal_power_pdschcfg: 'Signal Power',
    a3_event_offset: 'A3 Offset',
    t310_timer: 'T310 Timer',
    p0_nominal_pusch: 'P0 PUSCH',
    pdcch_aggregation_level: 'PDCCH Agg'
  };

  const entries: Array<[string, ParameterValue]> = params
    ? Object.entries(params).sort(([, a], [, b]) => (a.priority ?? 999) - (b.priority ?? 999))
    : fallbackOrder.map((key) => [
        key,
        {
          value: null,
          unit: '',
          source: 'unavailable',
          label: fallbackLabels[key],
          priority: fallbackOrder.indexOf(key) + 1
        }
      ]);

  const iconFor = (key: string, category?: string | null) => {
    if (key.includes('state')) return ToggleLeft;
    if (key.includes('pci') || key.includes('cell_id')) return Hash;
    if (key.includes('earfcn') || key.includes('bandwidth')) return Radio;
    if (key.includes('power') || key === 'pb') return Signal;
    if (key.includes('p0_')) return Wifi;
    if (key.includes('a3') || key.includes('handover') || category === 'Mobility') return ArrowUpRight;
    if (key.includes('timer') || key.includes('ttt')) return Clock;
    if (key.includes('pdcch')) return FileText;
    if (category === 'Carrier') return Gauge;
    if (category === 'Transport') return Router;
    return Activity;
  };

  const colorFor = (category?: string | null) => {
    switch (category) {
      case 'Cell':
        return 'text-accent-green';
      case 'Carrier':
        return 'text-sky-300';
      case 'RF':
        return 'text-accent-teal';
      case 'Uplink':
        return 'text-cyan-300';
      case 'Mobility':
        return 'text-accent-green';
      case 'RLF':
        return 'text-accent-purple';
      case 'PDCCH':
        return 'text-amber-300';
      default:
        return 'text-accent-teal';
    }
  };

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {entries.map(([key, param]) => {
        const Icon = iconFor(key, param.category);
        return (
          <ParameterCard
            key={key}
            icon={Icon}
            value={param.value ?? null}
            unit={param.unit}
            label={param.label || fallbackLabels[key] || key}
            category={param.category}
            source={param.source}
            iconColor={colorFor(param.category)}
          />
        );
      })}
    </div>
  );
}
