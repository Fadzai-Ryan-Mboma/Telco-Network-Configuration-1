import { useMemo } from 'react';
import { LayoutGrid } from 'lucide-react';
import type { TopologySite } from '../../services/api';
import { statusClass, statusLabel, statusSeverity } from './statusStyles';

interface StatusHeatmapProps {
  sites: TopologySite[];
  onSelectSite: (siteName: string) => void;
  onSelectGroup: (prefix: string) => void;
}

// The only structural signal available in a bare site_name is its leading
// alpha prefix (e.g. "MSH-0014-Chipadze" -> "MSH", "BYO-0083-..." -> "BYO").
// This is a location-code convention, not real geography or topology.
function groupPrefix(siteName: string): string {
  const match = siteName.match(/^[A-Za-z]+/);
  return match ? match[0] : 'Other';
}

export default function StatusHeatmap({ sites, onSelectSite, onSelectGroup }: StatusHeatmapProps) {
  const groups = useMemo(() => {
    const byPrefix = new Map<string, TopologySite[]>();
    for (const site of sites) {
      const prefix = groupPrefix(site.site_name);
      const bucket = byPrefix.get(prefix) ?? [];
      bucket.push(site);
      byPrefix.set(prefix, bucket);
    }
    for (const bucket of byPrefix.values()) {
      bucket.sort((a, b) => a.site_name.localeCompare(b.site_name));
    }
    return Array.from(byPrefix.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [sites]);

  const statusCounts = useMemo(() => {
    const counts: Record<TopologySite['status'], number> = { healthy: 0, watch: 0, critical: 0, unknown: 0 };
    for (const site of sites) counts[site.status] += 1;
    return counts;
  }, [sites]);

  return (
    <div className="card">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
            <LayoutGrid className="h-5 w-5 text-accent-teal" />
            Sites by Location Code
          </h3>
          <p className="text-sm text-gray-500">
            Grouped by site-name prefix. Click a tile for one site, a group heading for all sites in that group.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
          {statusSeverity.map((status) => (
            <span key={status} className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-sm ${statusClass[status]}`} />
              {statusLabel[status]} ({statusCounts[status]})
            </span>
          ))}
        </div>
      </div>

      <div className="max-h-[420px] overflow-y-auto pr-1">
        {groups.map(([prefix, groupSites]) => (
          <div key={prefix} className="mb-4">
            <button
              type="button"
              onClick={() => onSelectGroup(prefix)}
              className="mb-1.5 text-xs font-medium uppercase tracking-wide text-gray-500 hover:text-accent-teal"
            >
              {prefix} · {groupSites.length} sites
            </button>
            <div className="flex flex-wrap gap-1">
              {groupSites.map((site) => (
                <button
                  key={site.site_name}
                  type="button"
                  onClick={() => onSelectSite(site.site_name)}
                  title={`${site.site_name} · ${statusLabel[site.status]}`}
                  className={`h-3 w-3 rounded-sm ${statusClass[site.status]} transition-transform hover:scale-125`}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
