import { useEffect, useMemo, useState } from 'react';
import { Activity, ChevronUp, ChevronDown, Search } from 'lucide-react';
import type { TopologySite } from '../../services/api';
import { statusClass, statusLabel, statusSeverity } from './statusStyles';

interface SiteTableProps {
  sites: TopologySite[];
  search: string;
  onSearchChange: (value: string) => void;
}

type SortKey =
  | 'site_name'
  | 'status'
  | 'availability'
  | 'call_drop_rate'
  | 'control_channel_load'
  | 'total_traffic_gb'
  | 'cell_count'
  | 'last_updated';

type StatusFilter = 'all' | TopologySite['status'];

const PAGE_SIZE = 25;

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'site_name', label: 'Site Name' },
  { key: 'status', label: 'Status' },
  { key: 'availability', label: 'Avail. %' },
  { key: 'call_drop_rate', label: 'Call Drop %' },
  { key: 'control_channel_load', label: 'PRB %' },
  { key: 'total_traffic_gb', label: 'Traffic GB' },
  { key: 'cell_count', label: 'Cells' },
  { key: 'last_updated', label: 'Last Updated' },
];

function sortValue(site: TopologySite, key: SortKey): string | number {
  switch (key) {
    case 'site_name':
      return site.site_name;
    case 'status':
      return statusSeverity.indexOf(site.status);
    case 'availability':
      return site.availability ?? site.network_access_success ?? -Infinity;
    case 'call_drop_rate':
      return site.call_drop_rate ?? -Infinity;
    case 'control_channel_load':
      return site.control_channel_load ?? -Infinity;
    case 'total_traffic_gb':
      return site.total_traffic_gb ?? -Infinity;
    case 'cell_count':
      return site.cell_count ?? -Infinity;
    case 'last_updated':
      return site.last_updated ?? '';
  }
}

function formatValue(site: TopologySite, key: SortKey): string {
  switch (key) {
    case 'site_name':
      return site.site_name;
    case 'status':
      return statusLabel[site.status];
    case 'availability': {
      const value = site.availability ?? site.network_access_success;
      return value === null ? '-' : `${value.toFixed(2)}%`;
    }
    case 'call_drop_rate':
      return site.call_drop_rate === null ? '-' : `${site.call_drop_rate.toFixed(2)}%`;
    case 'control_channel_load':
      return site.control_channel_load === null ? '-' : `${site.control_channel_load.toFixed(2)}%`;
    case 'total_traffic_gb':
      return site.total_traffic_gb === null ? '-' : `${site.total_traffic_gb.toFixed(2)} GB`;
    case 'cell_count':
      return site.cell_count === null ? '-' : String(site.cell_count);
    case 'last_updated':
      return site.last_updated ? new Date(site.last_updated).toLocaleString() : '-';
  }
}

export default function SiteTable({ sites, search, onSearchChange }: SiteTableProps) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [sortKey, setSortKey] = useState<SortKey>('status');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter]);

  const filtered = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return sites.filter((site) => {
      if (statusFilter !== 'all' && site.status !== statusFilter) return false;
      if (normalizedSearch && !site.site_name.toLowerCase().includes(normalizedSearch)) return false;
      return true;
    });
  }, [sites, search, statusFilter]);

  const sorted = useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => {
      const aVal = sortValue(a, sortKey);
      const bVal = sortValue(b, sortKey);
      const cmp = typeof aVal === 'number' && typeof bVal === 'number' ? aVal - bVal : String(aVal).localeCompare(String(bVal));
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return copy;
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const pageSites = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  return (
    <div className="card">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-accent-green" />
          <h3 className="text-lg font-semibold text-white">Site Drilldown</h3>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <input
              type="search"
              value={search}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="Search site name"
              aria-label="Search sites"
              className="bg-bg-input border border-white/10 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:border-accent-teal/50 min-w-[220px]"
            />
            <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          </div>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
            className="input text-sm py-2"
            aria-label="Filter by status"
          >
            <option value="all">All statuses</option>
            {statusSeverity.map((status) => (
              <option key={status} value={status}>
                {statusLabel[status]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[820px] w-full text-left text-sm">
          <thead className="bg-bg-card-hover text-xs uppercase tracking-wide text-gray-500">
            <tr>
              {COLUMNS.map((column) => (
                <th key={column.key} className="px-3 py-2">
                  <button
                    type="button"
                    onClick={() => toggleSort(column.key)}
                    className="flex items-center gap-1 hover:text-white"
                  >
                    {column.label}
                    {sortKey === column.key &&
                      (sortDir === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />)}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageSites.map((site) => (
              <tr key={site.site_name} className="border-t border-white/5 text-gray-300">
                <td className="px-3 py-2 font-medium text-white">{site.site_name}</td>
                <td className="px-3 py-2">
                  <span className="flex items-center gap-1.5">
                    <span className={`status-dot ${statusClass[site.status]}`} />
                    {statusLabel[site.status]}
                  </span>
                </td>
                <td className="px-3 py-2">{formatValue(site, 'availability')}</td>
                <td className="px-3 py-2">{formatValue(site, 'call_drop_rate')}</td>
                <td className="px-3 py-2">{formatValue(site, 'control_channel_load')}</td>
                <td className="px-3 py-2">{formatValue(site, 'total_traffic_gb')}</td>
                <td className="px-3 py-2">{formatValue(site, 'cell_count')}</td>
                <td className="px-3 py-2">{formatValue(site, 'last_updated')}</td>
              </tr>
            ))}
            {pageSites.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length} className="px-3 py-6 text-center text-gray-500">
                  No sites match the current search/filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-gray-500">
        <span>
          Showing {pageSites.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}-{(page - 1) * PAGE_SIZE + pageSites.length} of{' '}
          {sorted.length} sites
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setPage((value) => Math.max(1, value - 1))}
            disabled={page <= 1}
            className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40"
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
            disabled={page >= totalPages}
            className="btn-secondary px-3 py-1.5 text-xs disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
