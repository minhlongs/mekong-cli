/**
 * FleetOverview SelectionBar & FilterPanel - RaaS UX Kit v2.1.79
 */
import React, { useState } from 'react';
import { Button } from '../atoms/Button';
import { RobotStatus, RobotMode } from '../types/robot';
import { FleetFilters } from '../types/fleet';

export interface SelectionBarProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: (checked: boolean) => void;
  onBulkStartMission?: (robotIds: string[]) => void;
  onBulkCharge?: (robotIds: string[]) => void;
  onBulkLocate?: (robotIds: string[]) => void;
  onBulkStop?: (robotIds: string[]) => void;
  onBulkReboot?: (robotIds: string[]) => void;
}

export const SelectionBar: React.FC<SelectionBarProps> = ({
  selectedCount,
  totalCount,
  onSelectAll,
  onBulkStartMission,
  onBulkCharge,
  onBulkLocate,
  onBulkStop,
}) => {
  const [showStopDialog, setShowStopDialog] = useState(false);

  return (
    <>
      <div className="sticky bottom-0 z-10 flex items-center justify-between p-3 bg-[var(--color-surface)] border-t border-[var(--color-border)] shadow-lg">
        <button
          type="button"
          className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)] cursor-pointer"
          onClick={() => onSelectAll(selectedCount < totalCount)}
        >
          <span
            className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
              selectedCount === totalCount ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white' : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'
            }`}
          >
            {selectedCount === totalCount && (
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <polyline points="20,6 9,17 4,12" strokeWidth="3" />
              </svg>
            )}
          </span>
          Select All{selectedCount > 0 && ` (${selectedCount})`}
        </button>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => onBulkStartMission?.([])} disabled={selectedCount === 0}>Start Mission</Button>
          <Button variant="outline" size="sm" onClick={() => onBulkCharge?.([])} disabled={selectedCount === 0}>Charge</Button>
          <Button variant="outline" size="sm" onClick={() => onBulkLocate?.([])} disabled={selectedCount === 0}>Locate</Button>
          <Button variant="danger" size="sm" onClick={() => selectedCount > 0 && setShowStopDialog(true)} disabled={selectedCount === 0}>Stop</Button>
        </div>
      </div>

      {showStopDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" onClick={() => setShowStopDialog(false)}>
          <div className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-6 max-w-md w-full mx-4 shadow-xl border-2 border-[var(--color-error)]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-center text-[var(--color-text-primary)] mb-2">Emergency Stop {selectedCount} Robots?</h3>
            <p className="text-center text-[var(--color-text-secondary)] mb-4">This will immediately halt all selected robots.</p>
            <div className="flex gap-3">
              <Button variant="ghost" size="lg" onClick={() => setShowStopDialog(false)} className="flex-1">Cancel</Button>
              <Button variant="danger" size="lg" onClick={() => { onBulkStop?.([]); setShowStopDialog(false); }} className="flex-1">
                STOP {selectedCount} ROBOTS
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

const statusOptions: { value: RobotStatus; label: string }[] = [
  { value: 'online', label: 'Online' }, { value: 'offline', label: 'Offline' }, { value: 'charging', label: 'Charging' },
  { value: 'error', label: 'Error' }, { value: 'warning', label: 'Warning' }, { value: 'busy', label: 'Busy' },
  { value: 'idle', label: 'Idle' }, { value: 'paused', label: 'Paused' }, { value: 'maintenance', label: 'Maintenance' },
];

const modeOptions: { value: RobotMode; label: string }[] = [
  { value: 'auto', label: 'Auto' }, { value: 'manual', label: 'Manual' }, { value: 'charging', label: 'Charging' },
  { value: 'sleep', label: 'Sleep' }, { value: 'error', label: 'Error' },
];

export const FilterPanel: React.FC<{
  filters: FleetFilters;
  onFilterChange: (filters: FleetFilters) => void;
  locations?: string[];
}> = ({ filters, onFilterChange }) => {
  const toggleFilter = <T extends string>(current: T[] | undefined, value: T, onChange: (values: T[] | undefined) => void) => {
    if (!current) onChange([value]);
    else if (current.includes(value)) {
      const next = current.filter((v) => v !== value);
      onChange(next.length === 0 ? undefined : next);
    } else onChange([...current, value]);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-lg)] border border-[var(--color-border)]">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-[var(--color-text-secondary)]">Status:</span>
        <div className="flex items-center gap-1 flex-wrap">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`px-2 py-1 text-xs rounded-[var(--radius-sm)] capitalize transition-colors cursor-pointer ${
                filters.status?.includes(opt.value)
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'
              }`}
              onClick={() => toggleFilter(filters.status || [], opt.value, (v) => onFilterChange({ ...filters, status: v }))}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-[var(--color-text-secondary)]">Mode:</span>
        <div className="flex items-center gap-1 flex-wrap">
          {modeOptions.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`px-2 py-1 text-xs rounded-[var(--radius-sm)] capitalize transition-colors cursor-pointer ${
                filters.mode?.includes(opt.value)
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'
              }`}
              onClick={() => toggleFilter(filters.mode || [], opt.value, (v) => onFilterChange({ ...filters, mode: v }))}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-w-[200px]">
        <input
          type="text"
          placeholder="Search robots..."
          value={filters.searchQuery || ''}
          onChange={(e) => onFilterChange({ ...filters, searchQuery: e.target.value })}
          className="w-full px-3 py-1.5 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-md)] text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-primary)]"
        />
      </div>
    </div>
  );
};
