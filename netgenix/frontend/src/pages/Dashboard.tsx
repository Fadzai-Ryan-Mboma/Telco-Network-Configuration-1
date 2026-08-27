import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query';
import { Header, LiveBanner } from '../components/Header';
import { ParameterGrid, StatusIndicators } from '../components/ParameterCards';
import { AIAssistant } from '../components/AIAssistant';
import { ResultsPanel } from '../components/ResultsPanel';
import { PerformanceChart } from '../components/PerformanceChart';
import { ActivityLog } from '../components/ActivityLog';
import { ReportingPanel } from '../components/ReportingPanel';
import { TopologyPanel } from '../components/TopologyPanel';
import {
  getSites,
  getSiteInfo,
  getSiteParameters,
  getSystemStatus,
  runOptimization,
  executeOptimization,
  getKPIValues,
  getKPIHistory,
  getActivity,
  getNBIDiagnostics,
  getEvaluationStatus,
  getTopologySites,
} from '../services/api';
import type { KPIHistory, OptimizationResult } from '../services/api';
import type { ThemeMode } from '../App';

const ACTIVE_BINDURA_SITES = new Set([
  'MSH-0014-Chipadze',
  'MSH-0112-Bindura Hospital',
  'MSH-0331-Chiwaridzo 2',
  'MSH-0013-Bindura Zaoga',
]);

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

interface DashboardProps {
  theme: ThemeMode;
  onThemeChange: (theme: ThemeMode) => void;
}

export default function Dashboard({ theme, onThemeChange }: DashboardProps) {
  const queryClient = useQueryClient();

  // State
  const [selectedSite, setSelectedSite] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hi! I'm your AI Network Optimizer. Describe any network issue or optimization goal, and I'll analyze and provide recommendations.",
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [selectedKPIs, setSelectedKPIs] = useState<string[]>(['radio_net_availability_rate']);
  const [selectedDays, setSelectedDays] = useState(7);
  const [selectedHistorySite, setSelectedHistorySite] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'performance' | 'activity' | 'reports' | 'topology'>('performance');

  // Queries
  const { data: sites = [], isLoading: sitesLoading, isError: sitesError } = useQuery({
    queryKey: ['sites'],
    queryFn: getSites,
    retry: 3,
    refetchInterval: 15000,
  });

  const activeSites = sites.filter((site) => ACTIVE_BINDURA_SITES.has(site.site_name));

  useEffect(() => {
    if (activeSites.length === 0) {
      return;
    }

    const siteStillExists = selectedSite
      ? activeSites.some((site) => site.site_name === selectedSite)
      : false;

    if (!siteStillExists) {
      setSelectedSite(activeSites[0].site_name);
    }
  }, [activeSites, selectedSite]);

  useEffect(() => {
    if (!selectedSite) {
      return;
    }
    setSelectedHistorySite(selectedSite);
  }, [selectedSite]);

  useEffect(() => {
    if (sites.length === 0) {
      return;
    }

    const historySiteStillExists = selectedHistorySite
      ? sites.some((site) => site.site_name === selectedHistorySite)
      : false;

    if (!historySiteStillExists) {
      setSelectedHistorySite(selectedSite ?? sites[0].site_name);
    }
  }, [sites, selectedSite, selectedHistorySite]);

  const { data: siteInfo } = useQuery({
    queryKey: ['siteInfo', selectedSite],
    queryFn: () => getSiteInfo(selectedSite!),
    enabled: !!selectedSite,
  });

  const useLiveParameters = import.meta.env.VITE_USE_LIVE_PARAMETERS === 'true';

  const { data: parameters, isLoading: paramsLoading } = useQuery({
    queryKey: ['parameters', selectedSite],
    queryFn: () => getSiteParameters(selectedSite!, useLiveParameters),
    enabled: !!selectedSite,
    refetchInterval: false,
  });

  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['status'],
    queryFn: getSystemStatus,
    refetchInterval: 15000,
  });

  const { data: nbiDiagnostics } = useQuery({
    queryKey: ['nbiDiagnostics'],
    queryFn: getNBIDiagnostics,
    refetchInterval: 60000,
  });

  const { data: evaluationStatus } = useQuery({
    queryKey: ['evaluationStatus'],
    queryFn: getEvaluationStatus,
    refetchInterval: 60000,
  });

  const { data: kpiValues } = useQuery({
    queryKey: ['kpiValues', selectedHistorySite],
    queryFn: () => getKPIValues(selectedHistorySite!),
    enabled: !!selectedHistorySite,
  });

  const kpiHistoryQueries = useQueries({
    queries: selectedKPIs.map((kpi) => ({
      queryKey: ['kpiHistory', selectedHistorySite, kpi, selectedDays],
      queryFn: () => getKPIHistory(selectedHistorySite!, kpi, selectedDays),
      enabled: !!selectedHistorySite,
    })),
  });

  const kpiHistories = useMemo(
    () => kpiHistoryQueries.map((query) => query.data).filter((data): data is KPIHistory => !!data),
    [kpiHistoryQueries]
  );
  const historyLoading = kpiHistoryQueries.some((query) => query.isLoading);

  // Outer-join each selected KPI's history by date so Recharts can render
  // every series from one merged dataset.
  const mergedChartData = useMemo(() => {
    const byDate = new Map<string, Record<string, string | number>>();
    for (const history of kpiHistories) {
      for (const point of history.data) {
        const row = byDate.get(point.date) ?? { date: point.date };
        row[history.kpi_name] = point.value;
        byDate.set(point.date, row);
      }
    }
    return Array.from(byDate.values()).sort((a, b) => String(a.date).localeCompare(String(b.date)));
  }, [kpiHistories]);

  // Primary KPI (first selected) keeps driving the summary cards, unchanged
  // from single-KPI behavior.
  const kpiHistory = kpiHistories.find((history) => history.kpi_name === selectedKPIs[0]) ?? null;

  const { data: activityData } = useQuery({
    queryKey: ['activity'],
    queryFn: () => getActivity(10),
  });

  const { data: topologyData } = useQuery({
    queryKey: ['topology'],
    queryFn: getTopologySites,
    refetchInterval: 60000,
  });

  // Mutations
  const optimizeMutation = useMutation({
    mutationFn: (query: string) =>
      runOptimization({
        site_name: selectedSite!,
        cell_id: siteInfo?.cell_id ?? 1,
        query,
      }),
    onSuccess: (result) => {
      setOptimizationResult(result);
      const baseMessage = result.status === 'success'
        ? `Analysis complete. I've identified ${result.issue}. Review the recommendations on the right panel.`
        : result.error_message || 'Analysis completed with issues.';
      const content = result.clarifying_question
        ? `${baseMessage}\n\nTo give you a more targeted answer next time: ${result.clarifying_question}`
        : baseMessage;
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content,
          isBot: true,
          timestamp: new Date(),
        },
      ]);
    },
    onError: (error: Error) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: `Sorry, I encountered an error: ${error.message}`,
          isBot: true,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const executeMutation = useMutation({
    mutationFn: () =>
      executeOptimization(
        selectedSite!,
        optimizationResult?.recommendations ?? [],
        optimizationResult?.mml_commands ?? []
      ),
    onSuccess: (result) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: result.dry_run
            ? `[DRY RUN] ${result.message}`
            : result.message,
          isBot: true,
          timestamp: new Date(),
        },
      ]);
      setOptimizationResult(null);
      queryClient.invalidateQueries({ queryKey: ['parameters'] });
      queryClient.invalidateQueries({ queryKey: ['activity'] });
    },
    onError: (error: Error) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: `Execution failed: ${error.message}`,
          isBot: true,
          timestamp: new Date(),
        },
      ]);
    },
  });

  // Handlers
  const handleQuerySubmit = useCallback((query: string) => {
    if (!selectedSite) return;

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        content: query,
        isBot: false,
        timestamp: new Date(),
      },
    ]);

    optimizeMutation.mutate(query);
  }, [selectedSite, optimizeMutation]);

  const handleApprove = useCallback(() => {
    // Validate before executing
    if (!selectedSite) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: 'No site selected. Please select a site first.',
          isBot: true,
          timestamp: new Date(),
        },
      ]);
      return;
    }

    if (!optimizationResult) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: 'No optimization results to execute. Please run analysis first.',
          isBot: true,
          timestamp: new Date(),
        },
      ]);
      return;
    }

    if (!optimizationResult.mml_commands || optimizationResult.mml_commands.length === 0) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: 'No MML commands available to execute. The analysis may not have generated executable commands.',
          isBot: true,
          timestamp: new Date(),
        },
      ]);
      return;
    }

    executeMutation.mutate();
  }, [executeMutation, selectedSite, optimizationResult, setMessages]);

  const handleReject = useCallback(() => {
    setOptimizationResult(null);
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        content: 'Recommendations rejected. Let me know if you need a different analysis.',
        isBot: true,
        timestamp: new Date(),
      },
    ]);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <Header
        sites={activeSites}
        sitesLoading={sitesLoading}
        sitesError={sitesError}
        selectedSite={selectedSite}
        siteInfo={siteInfo ?? null}
        onSiteSelect={setSelectedSite}
        lastUpdated={parameters?.last_updated ?? null}
        theme={theme}
        onThemeChange={onThemeChange}
      />

      {/* Main Content */}
      <main className="flex-1 p-6 space-y-6">
        {/* Live Banner */}
        <LiveBanner
          connected={systemStatus?.api_connected ?? false}
          loading={statusLoading}
          timestamp={parameters?.last_updated}
        />

        {/* Parameter Cards */}
        <ParameterGrid parameters={parameters ?? null} loading={paramsLoading} />

        {/* Status Indicators */}
        <StatusIndicators
          status={systemStatus ?? null}
          nbiDiagnostics={nbiDiagnostics ?? null}
          evaluationStatus={evaluationStatus ?? null}
        />

        {/* Two Column Layout */}
        <div className="grid grid-cols-5 gap-6">
          {/* AI Assistant - 2 columns */}
          <div className="col-span-2">
            <AIAssistant
              onSubmit={handleQuerySubmit}
              isLoading={optimizeMutation.isPending}
              messages={messages}
            />
          </div>

          {/* Results Panel - 3 columns */}
          <div className="col-span-3">
            <ResultsPanel
              result={optimizationResult}
              onApprove={handleApprove}
              onReject={handleReject}
              isExecuting={executeMutation.isPending}
            />
          </div>
        </div>

        {/* Performance / Activity Tabs */}
        <div className="card">
          {/* Tabs */}
          <div className="mb-6 flex flex-wrap gap-2">
            <button
              onClick={() => setActiveTab('performance')}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeTab === 'performance'
                  ? 'bg-accent-green text-bg-primary'
                  : 'bg-transparent text-gray-400 hover:text-white'
              }`}
            >
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
              Activity
            </button>
            <button
              onClick={() => setActiveTab('reports')}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeTab === 'reports'
                  ? 'bg-accent-green text-bg-primary'
                  : 'bg-transparent text-gray-400 hover:text-white'
              }`}
            >
              Reports
            </button>
            <button
              onClick={() => setActiveTab('topology')}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                activeTab === 'topology'
                  ? 'bg-accent-green text-bg-primary'
                  : 'bg-transparent text-gray-400 hover:text-white'
              }`}
            >
              Topology
            </button>
          </div>

          {activeTab === 'performance' ? (
            <PerformanceChart
              kpiHistory={kpiHistory}
              chartData={mergedChartData}
              currentKPIs={kpiValues ?? null}
              sites={sites}
              selectedSite={selectedHistorySite}
              onSiteChange={setSelectedHistorySite}
              selectedKPIs={selectedKPIs}
              onKPIsChange={setSelectedKPIs}
              selectedDays={selectedDays}
              onDaysChange={setSelectedDays}
              loading={historyLoading}
            />
          ) : activeTab === 'activity' ? (
            <ActivityLog
              activities={activityData?.activities ?? []}
            />
          ) : activeTab === 'reports' ? (
            <ReportingPanel />
          ) : (
            <TopologyPanel topology={topologyData ?? null} />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-4 text-sm text-gray-600 border-t border-white/5">
        <p>NetGenix Network Optimizer | Powered by AI</p>
        <p>Cassava Technologies 2026</p>
      </footer>
    </div>
  );
}
