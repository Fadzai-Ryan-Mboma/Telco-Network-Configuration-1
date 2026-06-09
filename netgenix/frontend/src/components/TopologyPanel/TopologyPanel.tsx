import { Activity, MapPin, RadioTower } from 'lucide-react';
import type { TopologyResponse, TopologySite } from '../../services/api';

interface TopologyPanelProps {
  topology: TopologyResponse | null;
}

const statusClass: Record<TopologySite['status'], string> = {
  healthy: 'bg-status-success',
  watch: 'bg-status-warning',
  critical: 'bg-status-error',
  unknown: 'bg-gray-500',
};

export default function TopologyPanel({ topology }: TopologyPanelProps) {
  const sites = topology?.sites ?? [];
  const visibleSites = sites.slice(0, 250);

  return (
    <div className="grid gap-6 xl:grid-cols-5">
      <div className="card xl:col-span-3">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
              <RadioTower className="h-5 w-5 text-accent-teal" />
              Network Topology
            </h3>
            <p className="text-sm text-gray-500">MAE-derived site inventory with KPI health overlays.</p>
          </div>
          <span className="badge badge-success">{topology?.site_count ?? 0} sites</span>
        </div>

        <div className="relative min-h-[420px] overflow-hidden rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_20%_20%,rgba(0,245,212,0.18),transparent_28%),radial-gradient(circle_at_80%_30%,rgba(0,241,156,0.12),transparent_24%),linear-gradient(135deg,#081220,#101b2d)]">
          <div className="absolute inset-0 opacity-20" style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px)',
            backgroundSize: '44px 44px',
          }} />

          {visibleSites.map((site, index) => (
            <SiteMarker key={site.site_name} site={site} index={index} total={visibleSites.length} />
          ))}
        </div>
      </div>

      <div className="card xl:col-span-2">
        <div className="mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-accent-green" />
          <h3 className="text-lg font-semibold text-white">Site Drilldown</h3>
        </div>

        <div className="space-y-3">
          {sites.slice(0, 40).map((site) => (
            <div key={site.site_name} className="rounded-xl border border-white/5 bg-bg-input p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-white">{site.site_name}</p>
                  <p className="text-xs text-gray-500">
                    {site.cell_count ?? '-'} cells · {site.source ?? 'NetGenix'}
                  </p>
                </div>
                <span className={`status-dot ${statusClass[site.status]}`} />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
                <Metric label="Avail." value={site.availability ?? site.network_access_success} suffix="%" />
                <Metric label="Traffic" value={site.total_traffic_gb} suffix=" GB" />
                <Metric label="PRB" value={site.control_channel_load} suffix="%" />
              </div>
            </div>
          ))}
          {sites.length > 40 && (
            <p className="text-sm text-gray-500">
              Showing first 40 sites in drilldown. Map view plots up to 250 markers.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function SiteMarker({ site, index, total }: { site: TopologySite; index: number; total: number }) {
  const columns = Math.max(1, Math.min(24, Math.ceil(Math.sqrt(total))));
  const rows = Math.max(1, Math.ceil(total / columns));
  const column = index % columns;
  const row = Math.floor(index / columns);
  const left = `${8 + (column * 84) / Math.max(1, columns - 1)}%`;
  const top = `${10 + (row * 78) / Math.max(1, rows - 1)}%`;
  const showLabel = total <= 60 || index % 5 === 0;

  return (
    <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left, top }}>
      <div className="flex flex-col items-center gap-2">
        <div
          className={`rounded-full ${statusClass[site.status]} shadow-[0_0_24px_rgba(0,245,212,.5)] ring-4 ring-white/10 ${
            total > 100 ? 'h-2.5 w-2.5' : 'h-4 w-4'
          }`}
          title={`${site.site_name} · ${site.status}`}
        />
        {showLabel && (
        <div className="rounded-xl border border-white/10 bg-bg-card/90 px-3 py-2 text-center shadow-xl backdrop-blur">
          <div className="flex items-center gap-1 text-sm font-semibold text-white">
            <MapPin className="h-3 w-3 text-accent-teal" />
            {site.site_name}
          </div>
          <p className="text-xs text-gray-500">{site.status}</p>
        </div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value, suffix }: { label: string; value: number | null; suffix: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <p className="text-gray-200">{value === null ? '-' : `${value.toFixed(2)}${suffix}`}</p>
    </div>
  );
}
