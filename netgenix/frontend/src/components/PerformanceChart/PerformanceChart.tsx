import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Search } from 'lucide-react';
import type { KPIHistory, KPIValues, Site } from '../../services/api';
import { KPI_BY_VALUE, CHART_SERIES_COLORS } from '../../constants/kpis';
import { useEffect, useMemo, useState } from 'react';
import KPIMultiSelect from './KPIMultiSelect';

interface PerformanceChartProps {
  kpiHistory: KPIHistory | null;
  chartData: Record<string, string | number>[];
  currentKPIs: KPIValues | null;
  sites: Site[];
  selectedSite: string | null;
  onSiteChange: (siteName: string) => void;
  selectedKPIs: string[];
  onKPIsChange: (kpis: string[]) => void;
  selectedDays: number;
  onDaysChange: (days: number) => void;
  loading?: boolean;
}

const DAYS_OPTIONS = [7, 14, 30, 60, 90];

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { dataKey: string; value: number; color: string }[]; label?: string }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      style={{
        backgroundColor: '#111B2E',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '8px',
        padding: '8px 12px',
      }}
    >
      <div style={{ color: '#94A3B8', fontSize: 12, marginBottom: 4 }}>
        {new Date(label ?? '').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
      </div>
      {payload.map((entry) => {
        const meta = KPI_BY_VALUE[entry.dataKey];
        return (
          <div key={entry.dataKey} style={{ color: entry.color, fontSize: 13 }}>
            {meta?.label ?? entry.dataKey}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value} {meta?.unit ?? ''}
          </div>
        );
      })}
    </div>
  );
}

export default function PerformanceChart({
  kpiHistory,
  chartData,
  currentKPIs,
  sites,
  selectedSite,
  onSiteChange,
  selectedKPIs,
  onKPIsChange,
  selectedDays,
  onDaysChange,
  loading
}: PerformanceChartProps) {
  const [siteQuery, setSiteQuery] = useState(selectedSite ?? '');

  useEffect(() => {
    setSiteQuery(selectedSite ?? '');
  }, [selectedSite]);

  const primaryKPI = selectedKPIs[0];
  const selectedMeta = KPI_BY_VALUE[primaryKPI];
  const rawCurrentValue = currentKPIs?.[primaryKPI];
  const currentValue = typeof rawCurrentValue === 'number' ? rawCurrentValue : rawCurrentValue ? Number(rawCurrentValue) : null;
  const threshold = kpiHistory?.threshold ?? selectedMeta?.threshold ?? null;
  const hasThreshold = typeof threshold === 'number';
  const isHealthy = currentValue !== null && hasThreshold
    ? selectedMeta?.lowerIsBetter
      ? currentValue <= threshold
      : currentValue >= threshold
    : null;

  // Calculate trend for the primary (first-selected) KPI
  const firstValue = kpiHistory?.data?.[0]?.value ?? 0;
  const lastValue = kpiHistory?.data?.[kpiHistory.data.length - 1]?.value ?? 0;
  const trend = kpiHistory?.data && kpiHistory.data.length > 1 && firstValue !== 0
    ? ((lastValue - firstValue) / firstValue * 100).toFixed(1)
    : '0.0';

  // Group selected KPIs by unit so overlapping units share one Y-axis;
  // only the first 2 distinct units get a visible axis (left/right) — any
  // further units still plot (auto-scaled) on a hidden axis, readable via
  // the legend and tooltip.
  const unitOrder = useMemo(() => {
    const seen: string[] = [];
    for (const kpi of selectedKPIs) {
      const unit = KPI_BY_VALUE[kpi]?.unit ?? '';
      if (!seen.includes(unit)) seen.push(unit);
    }
    return seen;
  }, [selectedKPIs]);

  const unitToAxisId = (unit: string) => `axis-${unitOrder.indexOf(unit)}`;

  const selectMatchingSite = (query: string) => {
    const normalized = query.trim().toLowerCase();
    const exactMatch = sites.find((site) => site.site_name.toLowerCase() === normalized);
    if (exactMatch) {
      onSiteChange(exactMatch.site_name);
      setSiteQuery(exactMatch.site_name);
      return true;
    }
    return false;
  };

  return (
    <>
      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <KPIMultiSelect selectedKPIs={selectedKPIs} onChange={onKPIsChange} />

          <div className="relative">
            <input
              type="search"
              list="performance-site-options"
              value={siteQuery}
              onChange={(event) => {
                setSiteQuery(event.target.value);
                selectMatchingSite(event.target.value);
              }}
              onKeyDown={(event) => {
                if (event.key !== 'Enter' || selectMatchingSite(siteQuery)) return;
                const normalized = siteQuery.trim().toLowerCase();
                const firstMatch = sites.find((site) => site.site_name.toLowerCase().includes(normalized));
                if (firstMatch) onSiteChange(firstMatch.site_name);
              }}
              onBlur={() => {
                if (!selectMatchingSite(siteQuery)) setSiteQuery(selectedSite ?? '');
              }}
              disabled={sites.length === 0}
              placeholder="History site"
              aria-label="Search historical site"
              className="bg-bg-input border border-white/10 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:border-accent-teal/50 min-w-[240px]"
            />
            <datalist id="performance-site-options">
              {sites.map((site) => (
                <option key={site.site_name} value={site.site_name}>
                  {site.site_name}
                </option>
              ))}
            </datalist>
            <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          </div>
        </div>

        <div className="flex gap-1">
          {DAYS_OPTIONS.map((days) => (
            <button
              key={days}
              type="button"
              onClick={() => onDaysChange(days)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedDays === days
                  ? 'bg-accent-teal text-bg-primary'
                  : 'bg-bg-input text-gray-400 hover:text-white'
              }`}
            >
              {days}D
            </button>
          ))}
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-bg-card-hover rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Current Value</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              {currentValue !== null && Number.isFinite(currentValue) ? currentValue.toFixed(2) : 'N/A'}
            </span>
            <span className="text-sm text-gray-500">{selectedMeta?.unit ?? ''}</span>
          </div>
          <div className={`flex items-center gap-1 text-sm ${Number(trend) >= 0 ? 'text-status-success' : 'text-status-error'}`}>
            {Number(trend) >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            <span>{trend}%</span>
          </div>
        </div>

        <div className="bg-bg-card-hover rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Operating Average</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">
              {hasThreshold ? threshold.toFixed(2) : 'N/A'}
            </span>
            <span className="text-sm text-gray-500">{selectedMeta?.unit ?? ''}</span>
          </div>
          <div className="text-sm text-gray-500">{hasThreshold ? 'Target baseline' : 'No fixed target'}</div>
        </div>

        <div className="bg-bg-card-hover rounded-lg p-4">
          <div className="text-xs text-gray-500 mb-1">Status</div>
          <div className={`text-2xl font-bold ${isHealthy === null ? 'text-gray-400' : isHealthy ? 'text-status-success' : 'text-status-error'}`}>
            {isHealthy === null ? 'TRACK' : isHealthy ? 'HEALTHY' : 'WATCH'}
          </div>
          <div className="text-sm text-gray-500">{selectedMeta?.lowerIsBetter ? 'lower is better' : 'higher is better'}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="animate-spin w-8 h-8 border-2 border-accent-teal border-t-transparent rounded-full" />
          </div>
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                {selectedKPIs.map((kpi, index) => (
                  <linearGradient key={kpi} id={`color-${kpi}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length]} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length]} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
              <XAxis
                dataKey="date"
                stroke="#64748B"
                tick={{ fill: '#64748B', fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              {unitOrder.map((unit, unitIndex) => (
                <YAxis
                  key={unit}
                  yAxisId={unitToAxisId(unit)}
                  orientation={unitIndex === 0 ? 'left' : 'right'}
                  hide={unitIndex >= 2}
                  stroke="#64748B"
                  tick={{ fill: '#64748B', fontSize: 12 }}
                  domain={['auto', 'auto']}
                  label={unitIndex < 2 && unit ? { value: unit, angle: -90, position: unitIndex === 0 ? 'insideLeft' : 'insideRight', fill: '#64748B', fontSize: 11 } : undefined}
                />
              ))}
              <Tooltip content={<CustomTooltip />} />
              {selectedKPIs.length > 1 && <Legend formatter={(value) => KPI_BY_VALUE[value]?.label ?? value} />}
              {selectedKPIs.length === 1 && hasThreshold && (
                <ReferenceLine
                  yAxisId={unitToAxisId(unitOrder[0])}
                  y={threshold}
                  stroke="#00F19C"
                  strokeDasharray="5 5"
                  label={{ value: 'Threshold', fill: '#00F19C', fontSize: 12 }}
                />
              )}
              {selectedKPIs.map((kpi, index) => {
                const unit = KPI_BY_VALUE[kpi]?.unit ?? '';
                const color = CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length];
                return (
                  <Area
                    key={kpi}
                    yAxisId={unitToAxisId(unit)}
                    type="monotone"
                    dataKey={kpi}
                    name={kpi}
                    stroke={color}
                    strokeWidth={2}
                    fill={`url(#color-${kpi})`}
                    connectNulls
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">
            No data available for selected period
          </div>
        )}
      </div>
    </>
  );
}
