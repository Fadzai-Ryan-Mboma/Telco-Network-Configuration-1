import { ChevronDown, Network, MapPin } from 'lucide-react';
import type { Site, SiteInfo } from '../../services/api';

interface HeaderProps {
  sites: Site[];
  selectedSite: string | null;
  siteInfo: SiteInfo | null;
  onSiteSelect: (siteName: string) => void;
  lastUpdated: string | null;
}

export default function Header({
  sites,
  selectedSite,
  siteInfo,
  onSiteSelect,
  lastUpdated
}: HeaderProps) {
  return (
    <header className="bg-bg-card border-b border-white/5 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-accent-teal/20 rounded-lg flex items-center justify-center">
            <Network className="w-6 h-6 text-accent-teal" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white">NetGenix</span>
            <span className="badge badge-success text-[10px] uppercase tracking-wider">
              AI Powered
            </span>
          </div>
        </div>

        {/* Site Selector & Info */}
        <div className="flex items-center gap-6">
          {/* Active Site Dropdown */}
          <div className="flex items-center gap-3">
            <span className="text-gray-400 text-sm">Active Site</span>
            <div className="relative">
              <select
                value={selectedSite || ''}
                onChange={(e) => onSiteSelect(e.target.value)}
                className="appearance-none bg-bg-input border border-white/10 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:border-accent-teal/50 cursor-pointer min-w-[200px]"
              >
                {sites.length === 0 && (
                  <option value="">Loading sites...</option>
                )}
                {sites.map((site) => (
                  <option key={site.site_name} value={site.site_name}>
                    {site.site_name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            {siteInfo && (
              <span className="badge badge-success">Live</span>
            )}
          </div>

          {/* Location & Cells */}
          {siteInfo && (
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2 text-gray-400">
                <MapPin className="w-4 h-4" />
                <span>Location</span>
                <span className="text-white font-medium">{siteInfo.location}</span>
              </div>
              <div className="text-gray-400">
                Cells <span className="text-accent-teal font-medium">{siteInfo.cell_count}</span>
              </div>
            </div>
          )}

          {/* Last Updated */}
          {lastUpdated && (
            <div className="text-sm text-gray-500">
              Updated: {new Date(lastUpdated).toLocaleDateString()}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
