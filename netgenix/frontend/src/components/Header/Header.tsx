import { useEffect, useState } from 'react';
import { Network, MapPin, Moon, Search, Sun } from 'lucide-react';
import type { Site, SiteInfo } from '../../services/api';
import type { ThemeMode } from '../../App';

interface HeaderProps {
  sites: Site[];
  sitesLoading: boolean;
  sitesError: boolean;
  selectedSite: string | null;
  siteInfo: SiteInfo | null;
  onSiteSelect: (siteName: string) => void;
  lastUpdated: string | null;
  theme: ThemeMode;
  onThemeChange: (theme: ThemeMode) => void;
}

export default function Header({
  sites,
  sitesLoading,
  sitesError,
  selectedSite,
  siteInfo,
  onSiteSelect,
  lastUpdated,
  theme,
  onThemeChange
}: HeaderProps) {
  const nextTheme = theme === 'dark' ? 'light' : 'dark';
  const [siteQuery, setSiteQuery] = useState(selectedSite ?? '');

  useEffect(() => {
    setSiteQuery(selectedSite ?? '');
  }, [selectedSite]);

  const selectMatchingSite = (query: string) => {
    const normalized = query.trim().toLowerCase();
    const exactMatch = sites.find((site) => site.site_name.toLowerCase() === normalized);
    if (exactMatch) {
      onSiteSelect(exactMatch.site_name);
      setSiteQuery(exactMatch.site_name);
      return true;
    }
    return false;
  };

  return (
    <header className="bg-bg-card border-b border-white/5 px-6 py-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
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
        <div className="flex flex-wrap items-center gap-6">
          {/* Active Site Search */}
          <div className="flex items-center gap-3">
            <span className="text-gray-400 text-sm">Active Site</span>
            <div className="relative">
              <input
                type="search"
                list="netgenix-site-options"
                value={siteQuery}
                onChange={(event) => {
                  setSiteQuery(event.target.value);
                  selectMatchingSite(event.target.value);
                }}
                onKeyDown={(event) => {
                  if (event.key !== 'Enter' || selectMatchingSite(siteQuery)) return;
                  const normalized = siteQuery.trim().toLowerCase();
                  const firstMatch = sites.find((site) => site.site_name.toLowerCase().includes(normalized));
                  if (firstMatch) onSiteSelect(firstMatch.site_name);
                }}
                onBlur={() => {
                  if (!selectMatchingSite(siteQuery)) setSiteQuery(selectedSite ?? '');
                }}
                disabled={sites.length === 0}
                placeholder={sitesLoading ? 'Loading sites...' : sitesError ? 'Sites unavailable' : 'Search site name or code'}
                aria-label="Search active site"
                className="bg-bg-input border border-white/10 rounded-lg px-4 py-2 pr-10 text-white text-sm focus:outline-none focus:border-accent-teal/50 min-w-[240px]"
              />
              <datalist id="netgenix-site-options">
                {sites.map((site) => (
                  <option key={site.site_name} value={site.site_name}>
                    {site.site_name}
                  </option>
                ))}
              </datalist>
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            {siteInfo && (
              <span className={siteInfo.status === 'Inventory' ? 'badge badge-warning' : 'badge badge-success'}>
                {siteInfo.status === 'Inventory' ? 'Inventory' : 'Live'}
              </span>
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

          <button
            type="button"
            onClick={() => onThemeChange(nextTheme)}
            className="theme-toggle inline-flex items-center gap-2 rounded-full border border-white/10 bg-bg-input px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:border-accent-teal/40 hover:text-white"
            aria-label={`Switch to ${nextTheme} mode`}
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4 text-accent-orange" />
            ) : (
              <Moon className="h-4 w-4 text-accent-teal" />
            )}
            <span>{theme === 'dark' ? 'Light' : 'Dark'} mode</span>
          </button>
        </div>
      </div>
    </header>
  );
}
