/**
 * API Client for NetGenix Backend
 */

import axios from 'axios';
import { KPI_BY_VALUE } from '../constants/kpis';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Site {
  site_name: string;
}

export interface SiteInfo {
  site_name: string;
  location: string;
  cell_count: number;
  cell_id: number;
  status: string;
  last_updated: string | null;
}

export interface ParameterValue {
  value: number | string | null;
  unit: string;
  source: 'live_api' | 'database' | 'change_history' | 'unavailable';
  label?: string | null;
  category?: string | null;
  priority?: number | null;
  description?: string | null;
}

export interface SiteParameters {
  site_name: string;
  parameters: Record<string, ParameterValue>;
  status: 'success' | 'fallback' | 'error';
  site_offline: boolean;
  last_updated: string | null;
  errors: string[];
}

export interface SystemStatus {
  api_connected: boolean;
  ne_connected: boolean;
  db_connected: boolean;
  api_status: string;
  ne_status: string;
  db_status: string;
}

export interface OptimizationRequest {
  site_name: string;
  cell_id: number;
  query: string;
}

export interface ParameterRecommendation {
  parameter: string;
  current_value: string | number;
  recommended_value: string | number;
  unit: string;
  description: string;
}

export interface KPIComparison {
  kpi: string;
  current_value: number | string | null;
  baseline: number | string | null;
  status: 'above_baseline' | 'at_baseline' | 'below_baseline' | '';
}

export interface OptimizationResult {
  status: 'success' | 'rejected' | 'error';
  issue: string;
  detailed_issue?: string;
  recommendations: ParameterRecommendation[];
  detailed_recommendations?: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'NONE';
  risk_score: number;
  detailed_risk?: string;
  expected_impact: string;
  detailed_impact?: string;
  mml_commands: string[];
  kpi_issue?: string;
  kpi_comparison?: KPIComparison[];
  clarifying_question?: string | null;
  message?: string;
  error_message?: string;
}

export interface ExecutionResult {
  status: 'success' | 'partial' | 'failed';
  message: string;
  dry_run: boolean;
  details: Array<{
    command: string;
    status: string;
    message?: string;
  }>;
}

export interface KPIValues {
  site_name: string;
  [key: string]: number | string | null;
  timestamp: string | null;
}

export interface KPIHistoryPoint {
  date: string;
  value: number;
}

export interface KPIHistory {
  site_name: string;
  kpi_name: string;
  days: number;
  data: KPIHistoryPoint[];
  threshold: number | null;
}

export interface ActivityRecord {
  site_name: string;
  timestamp: string;
  action_type: string;
  description: string;
  changes: string | null;
  result: string | null;
  status: 'success' | 'rejected' | 'detected' | 'info';
}

export interface NBIEnvironmentDiagnostic {
  name: string;
  gui_url: string;
  nbi_base_url: string;
  token_url: string;
  gui_reachable: boolean;
  gui_status_code: number | null;
  nbi_reachable: boolean;
  nbi_status_code: number | null;
  classification: 'success' | 'auth_failed' | 'timeout' | 'endpoint_missing' | 'method_wrong' | 'unknown';
  ret_code: string | null;
  ret_message: string | null;
  error: string | null;
  credentials_supplied: boolean;
}

export interface NBIDiagnostics {
  environments: NBIEnvironmentDiagnostic[];
  summary: {
    success: number;
    auth_failed: number;
    timeout: number;
    unavailable: number;
  };
}

export interface ReportSiteMetric {
  site_name: string;
  weekly_traffic_gb: number;
  weekly_traffic_tb: number;
  prb_busy_hour_weekly_average: number;
  code_drop_average: number;
  active_subscribers: number;
  addressable_subscribers: number;
  penetration_rate: number;
  average_gb_per_active_user: number;
  average_throughput_per_active_user: number;
  excluded: boolean;
}

export interface ReportColumnMapping {
  concept: string;
  matched_column: string | null;
  confidence: 'high' | 'missing';
  required: boolean;
}

export interface ReportColumnPreview {
  filename: string;
  row_count: number;
  columns: string[];
  mappings: ReportColumnMapping[];
  warnings: string[];
}

export interface ReportSection {
  name: string;
  worksheet: string;
  description: string;
  status: string;
}

export interface ReportRun {
  run_id: string;
  status: string;
  input_file: string;
  output_file: string;
  download_url: string;
  pdf_file: string;
  pdf_download_url: string;
  site_count: number;
  sections: ReportSection[];
  top_traffic_sites: ReportSiteMetric[];
  bottom_traffic_sites: ReportSiteMetric[];
  audit_file: string;
}

export interface ReportRunSummary {
  run_id: string;
  created_at: string | null;
  original_filename: string | null;
  site_count: number;
  sections_count: number;
  output_file: string;
  download_url: string;
  pdf_file: string | null;
  pdf_download_url: string | null;
  audit_file: string;
}

export interface EvaluationStatus {
  connected: boolean;
  reason: string | null;
  updated_at: string | null;
  last_successful_extraction: string | null;
  last_period_start: string | null;
  last_period_end: string | null;
  last_rows_ingested: number;
}

export interface ReconnectSessionStatus {
  session_id: string;
  status: 'starting' | 'awaiting_login' | 'session_saved' | 'failed' | 'timeout' | 'cancelled';
  error_message: string | null;
  started_at: number | null;
  novnc_url: string | null;
}

export interface ReportAutomationJob {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  refresh_requested: boolean;
  period_start: string;
  period_end: string;
  exclusions: string[];
  stage: string;
  error_message: string | null;
  report_run_id: string | null;
  source_freshness: string | null;
  rows_ingested: number;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  download_url: string | null;
  pdf_download_url: string | null;
}

export interface TopologySite {
  site_name: string;
  status: 'healthy' | 'watch' | 'critical' | 'unknown';
  latitude: number;
  longitude: number;
  network_access_success: number | null;
  download_speed: number | null;
  control_channel_load: number | null;
  cell_count: number | null;
  total_traffic_gb: number | null;
  availability: number | null;
  call_drop_rate: number | null;
  source: string | null;
  last_updated: string | null;
}

export interface TopologyResponse {
  sites: TopologySite[];
  site_count: number;
  generated_at: string;
}

// API Functions

// Sites
export const getSites = async (): Promise<Site[]> => {
  const response = await api.get('/api/sites');
  return response.data;
};

export const getSiteInfo = async (siteName: string): Promise<SiteInfo> => {
  const response = await api.get(`/api/sites/${encodeURIComponent(siteName)}`);
  return response.data;
};

export const getSiteParameters = async (siteName: string, live = true): Promise<SiteParameters> => {
  const response = await api.get(`/api/sites/${encodeURIComponent(siteName)}/params`, {
    params: { live }
  });
  return response.data;
};

export const getSiteStatus = async (siteName: string): Promise<SystemStatus> => {
  const response = await api.get(`/api/sites/${encodeURIComponent(siteName)}/status`);
  return response.data;
};

// Optimization
export const runOptimization = async (request: OptimizationRequest): Promise<OptimizationResult> => {
  // The LLM-backed analysis routinely takes 15-40s, well past the default
  // client timeout used for lightweight status/data calls.
  const response = await api.post('/api/optimize', request, { timeout: 90000 });
  return response.data;
};

export const executeOptimization = async (
  siteName: string,
  recommendations: ParameterRecommendation[],
  mmlCommands: string[]
): Promise<ExecutionResult> => {
  const response = await api.post('/api/optimize/execute', {
    site_name: siteName,
    recommendations,
    mml_commands: mmlCommands,
    execute_live: true
  }, { timeout: 90000 });
  return response.data;
};

// KPI
export const getKPIValues = async (siteName: string): Promise<KPIValues> => {
  try {
    const response = await api.get(`/api/kpi/v2/${encodeURIComponent(siteName)}/summary`, {
      params: { days: 7 }
    });
    return {
      site_name: siteName,
      timestamp: null,
      ...response.data.kpis,
    };
  } catch (error) {
    if (!axios.isAxiosError(error) || error.response?.status !== 503) throw error;
    const response = await api.get(`/api/kpi/${encodeURIComponent(siteName)}`);
    return response.data;
  }
};

export const getKPIHistory = async (
  siteName: string,
  kpiName: string,
  days: number
): Promise<KPIHistory> => {
  try {
    const response = await api.get(`/api/kpi/v2/${encodeURIComponent(siteName)}/history`, {
      params: { kpi: kpiName, days }
    });
    return {
      site_name: siteName,
      kpi_name: kpiName,
      days,
      data: response.data.data,
      threshold: KPI_BY_VALUE[kpiName]?.threshold ?? null,
    };
  } catch (error) {
    if (!axios.isAxiosError(error) || error.response?.status !== 503) throw error;
    const response = await api.get(`/api/kpi/${encodeURIComponent(siteName)}/history`, {
      params: { kpi_name: kpiName, days }
    });
    return response.data;
  }
};

// Activity
export const getActivity = async (limit = 10): Promise<{ activities: ActivityRecord[]; total: number }> => {
  const response = await api.get('/api/activity', { params: { limit } });
  return response.data;
};

// Status
export const getSystemStatus = async (): Promise<SystemStatus> => {
  const response = await api.get('/api/status');
  return response.data;
};

// Diagnostics
export const getNBIDiagnostics = async (): Promise<NBIDiagnostics> => {
  const response = await api.get('/api/diagnostics/nbi', { params: { timeout: 5 } });
  return response.data;
};

// Reports
export const previewReportFile = async (file: File): Promise<ReportColumnPreview> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/reports/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};

export const importReportFile = async (
  file: File,
  exclusions: string,
  userContext = 'dashboard'
): Promise<ReportRun> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/reports/imports', formData, {
    params: { exclusions, user_context: userContext },
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};

export const cookReportFiles = async (
  files: File[],
  exclusions: string,
  userContext = 'dashboard'
): Promise<ReportRun> => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const response = await api.post('/api/reports/cook', formData, {
    params: { exclusions, user_context: userContext },
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};

export const getReportRuns = async (): Promise<ReportRunSummary[]> => {
  const response = await api.get('/api/reports/runs');
  return response.data;
};

export const getEvaluationStatus = async (): Promise<EvaluationStatus> => {
  const response = await api.get('/api/evaluation/status');
  return response.data;
};

export const startEvaluationReconnect = async (): Promise<ReconnectSessionStatus> => {
  const response = await api.post('/api/evaluation/reconnect/start');
  return response.data;
};

export const getEvaluationReconnectStatus = async (sessionId: string): Promise<ReconnectSessionStatus> => {
  const response = await api.get(`/api/evaluation/reconnect/status/${encodeURIComponent(sessionId)}`);
  return response.data;
};

export const cancelEvaluationReconnect = async (sessionId: string): Promise<ReconnectSessionStatus> => {
  const response = await api.post(`/api/evaluation/reconnect/cancel/${encodeURIComponent(sessionId)}`);
  return response.data;
};

export const startAutomatedReport = async (
  periodStart: string,
  periodEnd: string,
  refresh: boolean,
  exclusionOverrides: string[]
): Promise<ReportAutomationJob> => {
  const response = await api.post('/api/reports/automation/runs', {
    period_start: periodStart,
    period_end: periodEnd,
    refresh,
    exclusion_overrides: exclusionOverrides,
  });
  return response.data;
};

export const getAutomatedReportJob = async (jobId: string): Promise<ReportAutomationJob> => {
  const response = await api.get(`/api/reports/automation/runs/${encodeURIComponent(jobId)}`);
  return response.data;
};

export const getAutomatedReportJobs = async (limit = 10): Promise<ReportAutomationJob[]> => {
  const response = await api.get('/api/reports/automation/runs', { params: { limit } });
  return response.data;
};

export const getReportExclusions = async (): Promise<string[]> => {
  const response = await api.get('/api/reports/exclusions');
  return response.data.sites;
};

export const saveReportExclusions = async (sites: string[]): Promise<string[]> => {
  const response = await api.put('/api/reports/exclusions', { sites });
  return response.data.sites;
};

export const getReportDownloadUrl = (downloadUrl: string): string => `${API_BASE_URL}${downloadUrl}`;

// Topology
export const getTopologySites = async (): Promise<TopologyResponse> => {
  const response = await api.get('/api/topology/sites');
  return response.data;
};

export default api;
