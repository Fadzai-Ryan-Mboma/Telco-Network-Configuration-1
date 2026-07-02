import type { TopologySite } from '../../services/api';

export const statusClass: Record<TopologySite['status'], string> = {
  healthy: 'bg-status-success',
  watch: 'bg-status-warning',
  critical: 'bg-status-error',
  unknown: 'bg-gray-500',
};

export const statusLabel: Record<TopologySite['status'], string> = {
  healthy: 'Healthy',
  watch: 'Watch',
  critical: 'Critical',
  unknown: 'Unknown',
};

// Ascending severity — used for the table's status sort and to order the
// heatmap legend consistently.
export const statusSeverity: TopologySite['status'][] = ['healthy', 'watch', 'critical', 'unknown'];
