import { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { BarChart3, Activity, TrendingUp, TrendingDown } from 'lucide-react';
import type { KPIHistory, KPIValues } from '../../services/api';

interface PerformanceChartProps {
  kpiHistory: KPIHistory | null;
  currentKPIs: KPIValues | null;
  selectedKPI: string;
  onKPIChange: (kpi: string) => void;
  selectedDays: number;
  onDaysChange: (days: number) => void;
  loading?: boolean;
}

const KPI_OPTIONS = [
  { value: 'network_access_success', label: 'Network Access Success' },
  { value: 'download_speed', label: 'Download Speed' },
  { value: 'download_quality', label: 'Download Quality' },
  { value: 'upload_speed', label: 'Upload Speed' },
  { value: 'upload_quality', label: 'Upload Quality' },
  { value: 'control_channel_load', label: 'Control Channel Load' },
  { value: 'feedback_channel_load', label: 'Feedback Channel Load' },
];

const DAYS_OPTIONS = [7, 14, 30, 60, 90];

export default function PerformanceChart({
  kpiHistory,
  currentKPIs,
  selectedKPI,
  onKPIChange,
  selectedDays,
  onDaysChange,
  loading
}: PerformanceChartProps) {
  const [activeTab, setActiveTab] = useState<'performance' | 'activity'>('performance');

  const currentValue = currentKPIs?.[selectedKPI as keyof KPIValues] as number | null;
  const threshold = kpiHistory?.threshold ?? 0;
  const isAbove = currentValue !== null && currentValue >= threshold;

  // Calculate trend
  const trend = kpiHistory?.data && kpiHistory.data.length > 1
    ? ((kpiHistory.data[kpiHistory.data.length - 1].value - kpiHistory.data[0].value) / kpiHistory.data[0].value * 100).toFixed(1)
    : '0.0';

  return (
    <div className="card">
      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('performance')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            activeTab === 'performance'
              ? 'bg-accent-green text-bg-primary'
              : 'bg-transparent text-gray-400 hover:text-white'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Performance
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            activeTab === 'activity'
              ? 'bg-accent-green text-bg-primary'
              : 'bg-transparent text-gray-400 hover:text-white'
          }`}
        >
          <Activity className="w-4 h-4" />
          Activity
        </button>
      </div>

      {activeTab === 'performance' && (
        <>
          {/* Controls */}
          <div className="flex items-center justify-between mb-6">
            <select
              value={selectedKPI}
              onChange={(e) => onKPIChange(e.target.value)}
              className="input text-sm py-2"
            >
              {KPI_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>

            <div className="flex gap-1">
              {DAYS_OPTIONS.map((days) => (
                <button
                  key={days}
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
                  {currentValue?.toFixed(2) ?? 'N/A'}
                </span>
                <span className="text-sm text-gray-500">%</span>
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
                  {threshold.toFixed(2)}
                </span>
                <span className="text-sm text-gray-500">%</span>
              </div>
              <div className="text-sm text-gray-500">Target baseline</div>
            </div>

            <div className="bg-bg-card-hover rounded-lg p-4">
              <div className="text-xs text-gray-500 mb-1">Status</div>
              <div className={`text-2xl font-bold ${isAbove ? 'text-status-success' : 'text-status-error'}`}>
                {isAbove ? 'ABOVE' : 'BELOW'}
              </div>
              <div className="text-sm text-gray-500">vs. average</div>
            </div>
          </div>

          {/* Chart */}
          <div className="h-64">
            {loading ? (
              <div className="h-full flex items-center justify-center">
                <div className="animate-spin w-8 h-8 border-2 border-accent-teal border-t-transparent rounded-full" />
              </div>
            ) : kpiHistory?.data && kpiHistory.data.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={kpiHistory.data}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00F5D4" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#00F5D4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis
                    dataKey="date"
                    stroke="#64748B"
                    tick={{ fill: '#64748B', fontSize: 12 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis
                    stroke="#64748B"
                    tick={{ fill: '#64748B', fontSize: 12 }}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111B2E',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#94A3B8' }}
                    itemStyle={{ color: '#00F5D4' }}
                  />
                  <ReferenceLine
                    y={threshold}
                    stroke="#00F19C"
                    strokeDasharray="5 5"
                    label={{ value: 'Threshold', fill: '#00F19C', fontSize: 12 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#00F5D4"
                    strokeWidth={2}
                    fill="url(#colorValue)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                No data available for selected period
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'activity' && (
        <div className="text-center text-gray-500 py-8">
          Activity log will be shown here
        </div>
      )}
    </div>
  );
}
