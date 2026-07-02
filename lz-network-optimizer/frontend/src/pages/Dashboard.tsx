import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Header, LiveBanner } from '../components/Header';
import { ParameterGrid, StatusIndicators } from '../components/ParameterCards';
import { AIAssistant } from '../components/AIAssistant';
import { ResultsPanel } from '../components/ResultsPanel';
import { PerformanceChart } from '../components/PerformanceChart';
import { ActivityLog } from '../components/ActivityLog';
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
} from '../services/api';
import type { OptimizationResult } from '../services/api';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

export default function Dashboard() {
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
  const [selectedKPI, setSelectedKPI] = useState('network_access_success');
  const [selectedDays, setSelectedDays] = useState(7);
  const [activeTab, setActiveTab] = useState<'performance' | 'activity'>('performance');

  // Queries
  const { data: sites = [] } = useQuery({
    queryKey: ['sites'],
    queryFn: getSites,
    retry: 3,
    refetchInterval: 15000,
  });

  useEffect(() => {
    if (sites.length === 0) {
      return;
    }

    const siteStillExists = selectedSite
      ? sites.some((site) => site.site_name === selectedSite)
      : false;

    if (!siteStillExists) {
      setSelectedSite(sites[0].site_name);
    }
  }, [sites, selectedSite]);

  const { data: siteInfo } = useQuery({
    queryKey: ['siteInfo', selectedSite],
    queryFn: () => getSiteInfo(selectedSite!),
    enabled: !!selectedSite,
  });

  const { data: parameters, isLoading: paramsLoading } = useQuery({
    queryKey: ['parameters', selectedSite],
    queryFn: () => getSiteParameters(selectedSite!, true), // Use live API for production demo
    enabled: !!selectedSite,
    refetchInterval: 60000, // Refresh every 1 minute for live data
  });

  const { data: systemStatus } = useQuery({
    queryKey: ['status'],
    queryFn: getSystemStatus,
    refetchInterval: 15000,
  });

  const { data: kpiValues } = useQuery({
    queryKey: ['kpiValues', selectedSite],
    queryFn: () => getKPIValues(selectedSite!),
    enabled: !!selectedSite,
  });

  const { data: kpiHistory, isLoading: historyLoading } = useQuery({
    queryKey: ['kpiHistory', selectedSite, selectedKPI, selectedDays],
    queryFn: () => getKPIHistory(selectedSite!, selectedKPI, selectedDays),
    enabled: !!selectedSite,
  });

  const { data: activityData } = useQuery({
    queryKey: ['activity'],
    queryFn: () => getActivity(10),
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
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content: result.status === 'success'
            ? `Analysis complete. I've identified ${result.issue}. Review the recommendations on the right panel.`
            : result.error_message || 'Analysis completed with issues.',
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
        sites={sites}
        selectedSite={selectedSite}
        siteInfo={siteInfo ?? null}
        onSiteSelect={setSelectedSite}
        lastUpdated={parameters?.last_updated ?? null}
      />

      {/* Main Content */}
      <main className="flex-1 p-6 space-y-6">
        {/* Live Banner */}
        <LiveBanner
          connected={systemStatus?.api_connected ?? false}
          timestamp={parameters?.last_updated}
        />

        {/* Parameter Cards */}
        <ParameterGrid parameters={parameters ?? null} loading={paramsLoading} />

        {/* Status Indicators */}
        <StatusIndicators status={systemStatus ?? null} />

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
          <div className="flex gap-2 mb-6">
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
          </div>

          {activeTab === 'performance' ? (
            <PerformanceChart
              kpiHistory={kpiHistory ?? null}
              currentKPIs={kpiValues ?? null}
              selectedKPI={selectedKPI}
              onKPIChange={setSelectedKPI}
              selectedDays={selectedDays}
              onDaysChange={setSelectedDays}
              loading={historyLoading}
            />
          ) : (
            <ActivityLog
              activities={activityData?.activities ?? []}
            />
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
