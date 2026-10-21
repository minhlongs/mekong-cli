/**
 * FleetOverview Component - RaaS UX Kit v2.1.79
 * Multi-robot fleet management with grid/list views, filtering, sorting, and bulk actions
 */
import React, { useCallback, useMemo } from 'react';
import { Button } from '../atoms/Button';
import { Icon } from '../atoms/Icon';
import { Robot } from '../types/robot';
import { FleetOverviewProps, FleetFilters, FleetSortConfig } from '../types/fleet';
import { FleetStatsBar, RobotGridCard, RobotListRow } from './fleet-overview-cards';
import { SelectionBar, FilterPanel } from './fleet-overview-controls';

export type { FleetOverviewProps, FleetFilters, FleetSortConfig };

export interface LocalFleetOverviewProps {
  robots: Robot[]; isLoading?: boolean; viewMode: 'grid' | 'list'; onViewModeChange: (mode: 'grid' | 'list') => void;
  filters: FleetFilters; onFilterChange: (filters: FleetFilters) => void; sortConfig?: FleetSortConfig;
  onSortChange?: (config: FleetSortConfig) => void; selectedRobotIds: string[]; onSelectionChange: (ids: string[]) => void;
  onBulkStartMission?: (robotIds: string[]) => void; onBulkCharge?: (robotIds: string[]) => void;
  onBulkLocate?: (robotIds: string[]) => void; onBulkStop?: (robotIds: string[]) => void;
  onBulkReboot?: (robotIds: string[]) => void; onRobotClick: (robotId: string) => void;
  onQuickAction?: (robotId: string, action: string) => void;
  pagination?: { page: number; pageSize: number; total: number }; onPageChange?: (page: number) => void;
  className?: string; compact?: boolean;
}

export const FleetOverview: React.FC<LocalFleetOverviewProps> = ({
  robots = [], isLoading = false, viewMode = 'grid', onViewModeChange, filters, onFilterChange, sortConfig,
  selectedRobotIds = [], onSelectionChange, onBulkStartMission, onBulkCharge, onBulkLocate, onBulkStop,
  onBulkReboot, onRobotClick, onQuickAction, className = '', compact = false,
}) => {
  const locations = useMemo(() => Array.from(new Set(robots.map((r) => r.location?.zone).filter(Boolean))) as string[], [robots]);

  const filteredRobots = useMemo(
    () =>
      robots.filter((robot) => {
        if (filters.status?.length && !filters.status.includes(robot.status)) return false;
        if (filters.mode?.length && !filters.mode.includes(robot.mode)) return false;
        if (filters.location?.length && !filters.location.includes(robot.location?.zone || '')) return false;
        if (filters.batteryRange) {
          const level = robot.battery?.level || 0;
          if (level < (filters.batteryRange.min || 0) || level > (filters.batteryRange.max || 100)) return false;
        }
        if (filters.searchQuery) {
          const q = filters.searchQuery.toLowerCase();
          return robot.name.toLowerCase().includes(q) || (robot.serialNumber?.toLowerCase() || '').includes(q) || (robot.location?.zone?.toLowerCase() || '').includes(q);
        }
        return true;
      }),
    [robots, filters]
  );

  const sortedRobots = useMemo(() => {
    if (!sortConfig) return filteredRobots;
    const dir = sortConfig.direction === 'asc' ? 1 : -1;
    return [...filteredRobots].sort((a, b) => {
      if (sortConfig.field === 'name') return dir * a.name.localeCompare(b.name);
      if (sortConfig.field === 'location') return dir * (a.location?.zone || '').localeCompare(b.location?.zone || '');
      if (sortConfig.field === 'status') return dir * a.status.localeCompare(b.status);
      if (sortConfig.field === 'battery') return dir * ((a.battery?.level || 0) - (b.battery?.level || 0));
      if (sortConfig.field === 'lastSeen') return dir * ((a.lastSeen?.getTime() || 0) - (b.lastSeen?.getTime() || 0));
      return 0;
    });
  }, [filteredRobots, sortConfig]);

  const handleSelectAll = useCallback((checked: boolean) => onSelectionChange(checked ? sortedRobots.map((r) => r.id) : []), [sortedRobots, onSelectionChange]);
  const handleSelectRobot = useCallback(
    (robotId: string) => onSelectionChange(selectedRobotIds.includes(robotId) ? selectedRobotIds.filter((id) => id !== robotId) : [...selectedRobotIds, robotId]),
    [selectedRobotIds, onSelectionChange]
  );

  if (compact) {
    return (
      <div className={`flex flex-col gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 ${className}`} role="region" aria-label="Fleet overview">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Fleet Overview</h2>
          <span className="text-sm text-[var(--color-text-secondary)] tabular-nums">{filteredRobots.length} robots</span>
        </div>
        <FleetStatsBar robots={robots} />
      </div>
    );
  }

  const CardComponent = viewMode === 'grid' ? RobotGridCard : RobotListRow;

  return (
    <div className={`flex flex-col gap-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 ${className}`} role="region" aria-label="Fleet overview">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Fleet Overview</h2>
          <p className="text-sm text-[var(--color-text-tertiary)] tabular-nums">{filteredRobots.length} of {robots.length} robots</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)] p-1">
            {(['grid', 'list'] as const).map((mode) => (
              <button
                key={mode} type="button" aria-pressed={viewMode === mode} onClick={() => onViewModeChange(mode)}
                className={`px-3 py-1.5 text-xs font-medium rounded-[var(--radius-sm)] capitalize transition-colors cursor-pointer ${
                  viewMode === mode ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
          <Button variant="primary" size="sm">Add Robot</Button>
        </div>
      </div>

      <FleetStatsBar robots={robots} />
      <FilterPanel filters={filters} onFilterChange={onFilterChange} locations={locations} />

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Icon size="xl" color="secondary" isAnimated><circle cx="12" cy="12" r="10" /></Icon>
          <span className="ml-3 text-[var(--color-text-secondary)]">Loading robots...</span>
        </div>
      ) : sortedRobots.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-[var(--color-text-secondary)]">No robots match your filters</p>
          <Button variant="ghost" size="sm" className="mt-2" onClick={() => onFilterChange({})}>Clear Filters</Button>
        </div>
      ) : (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4' : 'flex flex-col gap-2'}>
          {sortedRobots.map((robot) => (
            <CardComponent key={robot.id} robot={robot} isSelected={selectedRobotIds.includes(robot.id)} onSelect={handleSelectRobot} onClick={onRobotClick} onQuickAction={onQuickAction} />
          ))}
        </div>
      )}

      {selectedRobotIds.length > 0 && (
        <SelectionBar
          selectedCount={selectedRobotIds.length} totalCount={sortedRobots.length} onSelectAll={handleSelectAll}
          onBulkStartMission={onBulkStartMission} onBulkCharge={onBulkCharge} onBulkLocate={onBulkLocate} onBulkStop={onBulkStop} onBulkReboot={onBulkReboot}
        />
      )}
    </div>
  );
};

export default FleetOverview;
