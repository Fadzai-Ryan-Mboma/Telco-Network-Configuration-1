/**
 * API Client for NetGenix Backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8503';

const api = axios.create({
  baseURL: API_BASE_URL,
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
  source: 'live_api' | 'database';
}

export interface SiteParameters {
  site_name: string;
  parameters: {
    reference_signal_power_pdschcfg: ParameterValue;
    a3_event_offset: ParameterValue;
    t310_timer: ParameterValue;
    p0_nominal_pusch: ParameterValue;
    pdcch_aggregation_level: ParameterValue;
  };
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

export interface OptimizationResult {
  status: 'success' | 'rejected' | 'error';
  issue: string;
  detailed_issue?: string;
  recommendations: ParameterRecommendation[];
  detailed_recommendations?: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_score: number;
  detailed_risk?: string;
  expected_impact: string;
  detailed_impact?: string;
  mml_commands: string[];
  kpi_issue?: string;
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
  network_access_success: number | null;
  download_speed: number | null;
  download_quality: number | null;
  upload_speed: number | null;
  upload_quality: number | null;
  control_channel_load: number | null;
  feedback_channel_load: number | null;
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
  threshold: number;
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
  const response = await api.post('/api/optimize', request);
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
    mml_commands: mmlCommands
  });
  return response.data;
};

// KPI
export const getKPIValues = async (siteName: string): Promise<KPIValues> => {
  const response = await api.get(`/api/kpi/${encodeURIComponent(siteName)}`);
  return response.data;
};

export const getKPIHistory = async (
  siteName: string,
  kpiName: string,
  days: number
): Promise<KPIHistory> => {
  const response = await api.get(`/api/kpi/${encodeURIComponent(siteName)}/history`, {
    params: { kpi_name: kpiName, days }
  });
  return response.data;
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

export default api;
