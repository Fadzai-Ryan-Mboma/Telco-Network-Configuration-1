import { useEffect, useRef, useState } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { KPI_OPTIONS, KPI_BY_VALUE, CHART_SERIES_COLORS } from '../../constants/kpis';

const MAX_SELECTED_KPIS = CHART_SERIES_COLORS.length;

interface KPIMultiSelectProps {
  selectedKPIs: string[];
  onChange: (kpis: string[]) => void;
}

export default function KPIMultiSelect({ selectedKPIs, onChange }: KPIMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const groupedOptions = KPI_OPTIONS.reduce<Record<string, typeof KPI_OPTIONS>>((groups, option) => {
    groups[option.group] = groups[option.group] || [];
    groups[option.group].push(option);
    return groups;
  }, {});

  const atCap = selectedKPIs.length >= MAX_SELECTED_KPIS;

  function toggleKPI(value: string) {
    if (selectedKPIs.includes(value)) {
      if (selectedKPIs.length === 1) return; // always keep at least one selected
      onChange(selectedKPIs.filter((kpi) => kpi !== value));
    } else {
      if (atCap) return;
      onChange([...selectedKPIs, value]);
    }
  }

  function removeChip(value: string) {
    if (selectedKPIs.length === 1) return;
    onChange(selectedKPIs.filter((kpi) => kpi !== value));
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="flex flex-wrap items-center gap-2">
        {selectedKPIs.map((kpi, index) => (
          <span
            key={kpi}
            className="flex items-center gap-1.5 rounded-full bg-bg-card-hover px-3 py-1.5 text-sm text-white"
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length] }}
            />
            {KPI_BY_VALUE[kpi]?.label ?? kpi}
            {selectedKPIs.length > 1 && (
              <button
                type="button"
                onClick={() => removeChip(kpi)}
                aria-label={`Remove ${KPI_BY_VALUE[kpi]?.label ?? kpi}`}
                className="text-gray-400 hover:text-white"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </span>
        ))}
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="input flex items-center gap-2 text-sm py-2"
          aria-label="Add KPI to chart"
        >
          {selectedKPIs.length < MAX_SELECTED_KPIS ? 'Add KPI' : 'Max 4 selected'}
          <ChevronDown className="h-4 w-4" />
        </button>
      </div>

      {open && (
        <div className="absolute z-20 mt-2 max-h-80 w-72 overflow-y-auto rounded-lg border border-white/10 bg-bg-card-hover p-2 shadow-lg">
          {Object.entries(groupedOptions).map(([group, options]) => (
            <div key={group} className="mb-2">
              <div className="px-2 py-1 text-xs font-medium uppercase text-gray-500">{group}</div>
              {options.map((opt) => {
                const checked = selectedKPIs.includes(opt.value);
                const disabled = !checked && atCap;
                return (
                  <label
                    key={opt.value}
                    className={`flex items-center gap-2 rounded px-2 py-1.5 text-sm ${
                      disabled ? 'cursor-not-allowed text-gray-600' : 'cursor-pointer text-gray-200 hover:bg-white/5'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={disabled}
                      onChange={() => toggleKPI(opt.value)}
                      className="accent-accent-teal"
                    />
                    {opt.label}
                  </label>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
