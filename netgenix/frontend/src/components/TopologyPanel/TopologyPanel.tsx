import { useState } from 'react';
import type { TopologyResponse } from '../../services/api';
import StatusHeatmap from './StatusHeatmap';
import SiteTable from './SiteTable';

interface TopologyPanelProps {
  topology: TopologyResponse | null;
}

export default function TopologyPanel({ topology }: TopologyPanelProps) {
  const sites = topology?.sites ?? [];
  const [search, setSearch] = useState('');

  return (
    <div className="space-y-6">
      <StatusHeatmap sites={sites} onSelectSite={setSearch} onSelectGroup={setSearch} />
      <SiteTable sites={sites} search={search} onSearchChange={setSearch} />
    </div>
  );
}
