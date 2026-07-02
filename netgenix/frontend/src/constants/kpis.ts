export interface KPIMetadata {
  value: string;
  label: string;
  unit: string;
  group: string;
  threshold: number | null;
  lowerIsBetter?: boolean;
}

export const KPI_OPTIONS: KPIMetadata[] = [
  { value: 'radio_net_availability_rate', label: 'Radio Net Availability', unit: '%', group: 'Availability', threshold: 99 },
  { value: 'rrc_setup_success_rate_all', label: 'RRC Setup Success All', unit: '%', group: 'Access', threshold: 98 },
  { value: 'rrc_setup_success_rate_service', label: 'RRC Setup Success Service', unit: '%', group: 'Access', threshold: 98 },
  { value: 'rrc_setup_success_rate_signal', label: 'RRC Setup Success Signal', unit: '%', group: 'Access', threshold: 95 },
  { value: 'erab_setup_success_rate', label: 'ERAB Setup Success', unit: '%', group: 'Access', threshold: 98 },
  { value: 'call_drop_rate', label: 'Call Drop Rate', unit: '%', group: 'Retainability', threshold: 2, lowerIsBetter: true },
  { value: 'ho_success_rate_intra_freq', label: 'HO Success Intra-Freq', unit: '%', group: 'Mobility', threshold: 95 },
  { value: 'ho_success_rate_s1', label: 'HO Success S1', unit: '%', group: 'Mobility', threshold: 95 },
  { value: 'paging_transfer_success_rate', label: 'Paging Transfer Success', unit: '%', group: 'Paging', threshold: 98 },
  { value: 'total_traffic_gbit', label: 'Total Traffic', unit: 'Gbit', group: 'Traffic', threshold: null },
  { value: 'dl_traffic_volume_gbit', label: 'DL Traffic Volume', unit: 'Gbit', group: 'Traffic', threshold: null },
  { value: 'ul_traffic_volume_gbit', label: 'UL Traffic Volume', unit: 'Gbit', group: 'Traffic', threshold: null },
  { value: 'l_traffic_user_avg', label: 'Avg Traffic Users', unit: 'users', group: 'Users', threshold: null },
  { value: 'l_traffic_user_max', label: 'Max Traffic Users', unit: 'users', group: 'Users', threshold: null },
  { value: 'user_dl_pdcp_avg_throughput', label: 'User DL Throughput', unit: 'Mbps', group: 'Throughput', threshold: 5 },
  { value: 'user_ul_pdcp_avg_throughput', label: 'User UL Throughput', unit: 'Mbps', group: 'Throughput', threshold: 3 },
  { value: 'dl_ibler', label: 'DL IBLER', unit: '%', group: 'Quality', threshold: 10, lowerIsBetter: true },
  { value: 'ul_ibler', label: 'UL IBLER', unit: '%', group: 'Quality', threshold: 10, lowerIsBetter: true },
  { value: 'dl_retrans_rate', label: 'DL Retransmission Rate', unit: '%', group: 'Quality', threshold: 5, lowerIsBetter: true },
  { value: 'dl_packet_loss_rate', label: 'DL Packet Loss', unit: '%', group: 'Quality', threshold: 1, lowerIsBetter: true },
  { value: 'ul_packet_loss_rate', label: 'UL Packet Loss', unit: '%', group: 'Quality', threshold: 1, lowerIsBetter: true },
  { value: 'dl_prb_usage_rate', label: 'DL PRB Usage', unit: '%', group: 'Resource', threshold: 80, lowerIsBetter: true },
  { value: 'ul_prb_usage_rate', label: 'UL PRB Usage', unit: '%', group: 'Resource', threshold: 80, lowerIsBetter: true },
  { value: 'pucch_usage_rate', label: 'PUCCH Usage', unit: '%', group: 'Resource', threshold: 80, lowerIsBetter: true },
  { value: 'pdcch_cce_usage_rate', label: 'PDCCH CCE Usage', unit: '%', group: 'Resource', threshold: 80, lowerIsBetter: true },
  { value: 'average_cqi', label: 'Average CQI', unit: '', group: 'Radio Quality', threshold: 9 },
  { value: 'average_pdsch_mcs', label: 'Average PDSCH MCS', unit: '', group: 'Radio Quality', threshold: 12 },
  { value: 'data_access_time_ms', label: 'Data Access Time', unit: 'ms', group: 'Latency', threshold: 10, lowerIsBetter: true },
  { value: 'total_cell_unavail_duration_s', label: 'Cell Unavailability', unit: 's', group: 'Availability', threshold: 0, lowerIsBetter: true },
  { value: 'integrity', label: 'Integrity', unit: '%', group: 'Data Quality', threshold: 100 },
];

export const KPI_BY_VALUE = Object.fromEntries(KPI_OPTIONS.map((kpi) => [kpi.value, kpi]));

// Fixed-order categorical palette for overlaid chart series, validated for
// colorblind-safety and contrast against the dark chart surface (see
// dataviz skill references/palette.md dark-mode categorical steps).
// Assign by selection order, never cycled past this length — the KPI
// multi-select cap (4) matches this palette's length exactly.
export const CHART_SERIES_COLORS = ['#3987e5', '#199e70', '#c98500', '#9085e9'];
