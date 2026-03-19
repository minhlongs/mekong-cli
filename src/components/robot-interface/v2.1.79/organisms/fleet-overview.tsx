/**
 * FleetOverview Component - RaaS UX Kit v2.1.79
 * Multi-robot fleet management with grid/list views, filtering, sorting, and bulk actions
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Button } from '../../atoms/Button';
import { Icon } from '../../atoms/Icon';
import { StatusBadge } from '../../atoms/StatusBadge';
import { SearchBar } from '../../molecules/SearchBar';
import {
  FleetOverviewProps,
  FleetFilters,
  FleetSortConfig,
  Robot,
  RobotStatus,
  RobotMode,
} from '../../types/fleet';

// Re-export types for consumers
export type { FleetOverviewProps, FleetFilters, FleetSortConfig };

// ============================================
// Fleet Stats Bar Component
// ============================================

interface FleetStatsBarProps {
  robots: Robot[];
}

const FleetStatsBar: React.FC<FleetStatsBarProps> = ({ robots }) => {
  const stats = useMemo(() => {
    const online = robots.filter((r) => r.status === 'online' || r.status === 'busy').length;
    const offline = robots.filter((r) => r.status === 'offline').length;
    const charging = robots.filter((r) => r.status === 'charging').length;
    const error = robots.filter((r) => r.status === 'error' || r.status === 'warning').length;
    const maintenance = robots.filter((r) => r.status === 'maintenance').length;

    return { online, offline, charging, error, maintenance, total: robots.length };
  }, [robots]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
      <div className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <span className="text-xs text-[var(--color-text-secondary)] mb-1">Total Robots</span>
        <span className="text-lg font-semibold text-[var(--color-text-primary)]">
          {stats.total}
        </span>
      </div>
      <div className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <span className="text-xs text-[var(--color-text-secondary)] mb-1">Online</span>
        <span className="text-lg font-semibold text-[var(--color-success)]">
          {stats.online}
        </span>
      </div>
      <div className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <span className="text-xs text-[var(--color-text-secondary)] mb-1">Offline</span>
        <span className="text-lg font-semibold text-[var(--color-text-secondary)]">
          {stats.offline}
        </span>
      </div>
      <div className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <span className="text-xs text-[var(--color-text-secondary)] mb-1">Charging</span>
        <span className="text-lg font-semibold text-[var(--color-warning)]">
          {stats.charging}
        </span>
      </div>
      <div className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <span className="text-xs text-[var(--color-text-secondary)] mb-1">Error</span>
        <span className="text-lg font-semibold text-[var(--color-error)]">
          {stats.error}
        </span>
      </div>
      <div className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <span className="text-xs text-[var(--color-text-secondary)] mb-1">Maintenance</span>
        <span className="text-lg font-semibold text-[var(--color-text-tertiary)]">
          {stats.maintenance}
        </span>
      </div>
    </div>
  );
};

// ============================================
// Robot Grid Card Component
// ============================================

interface RobotGridCardProps {
  robot: Robot;
  isSelected?: boolean;
  onSelect?: (robotId: string) => void;
  onClick?: (robotId: string) => void;
  onQuickAction?: (robotId: string, action: string) => void;
}

const RobotGridCard: React.FC<RobotGridCardProps> = ({
  robot,
  isSelected,
  onSelect,
  onClick,
  onQuickAction,
}) => {
  const statusConfig = {
    online: { color: 'success', label: 'Online' },
    busy: { color: 'success', label: 'Busy' },
    offline: { color: 'secondary', label: 'Offline' },
    charging: { color: 'warning', label: 'Charging' },
    error: { color: 'danger', label: 'Error' },
    warning: { color: 'warning', label: 'Warning' },
    idle: { color: 'secondary', label: 'Idle' },
    paused: { color: 'warning', label: 'Paused' },
    maintenance: { color: 'secondary', label: 'Maintenance' },
  };

  const config = statusConfig[robot.status] || statusConfig.offline;

  const getBatteryIcon = (level: number) => {
    if (robot.battery?.charging) {
      return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="3" y="6" width="14" height="12" rx="2" strokeWidth="2" />
          <line x1="19" y1="10" x2="19" y2="14" strokeWidth="2" />
          <line x1="17" y1="8" x2="21" y2="12" strokeWidth="2" />
          <line x1="17" y1="16" x2="21" y2="12" strokeWidth="2" />
          <rect x="5" y="8" width={Math.max(0, (level / 100) * 10)} height="8" fill="currentColor" />
        </svg>
      );
    }
    return (
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <rect x="2" y="6" width="16" height="12" rx="2" strokeWidth="2" />
        <line x1="20" y1="10" x2="20" y2="14" strokeWidth="2" />
        <rect x="4" y="8" width={Math.max(0, (level / 100) * 12)} height="8" fill="currentColor" />
      </svg>
    );
  };

  return (
    <div
      className={`
        flex flex-col p-4 rounded-[var(--radius-lg)] border
        transition-all duration-150 cursor-pointer
        ${isSelected
          ? 'bg-[var(--color-surface-tertiary)] border-[var(--color-primary)]'
          : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:border-[var(--color-primary)]'
        }
      `}
      onClick={() => onClick?.(robot.id)}
      role="article"
      aria-label={`Robot ${robot.name}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {/* Selection Checkbox */}
          <button
            className={`
              w-5 h-5 rounded border flex items-center justify-center
              transition-colors
              ${isSelected
                ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white'
                : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'
              }
            `}
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.(robot.id);
            }}
            aria-label={`Select ${robot.name}`}
          >
            {isSelected && (
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <polyline points="20,6 9,17 4,12" strokeWidth="3" />
              </svg>
            )}
          </button>
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
              {robot.name}
            </h3>
            <p className="text-xs text-[var(--color-text-tertiary)]">
              {robot.location?.zone || 'Unknown'}
            </p>
          </div>
        </div>
        <StatusBadge status={robot.status} variant={config.color as any} size="sm">
          {config.label}
        </StatusBadge>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1.5 bg-[var(--color-surface-tertiary)] rounded-full overflow-hidden mb-3">
        <div
          className={`h-full transition-all duration-300 ${
            robot.battery?.level < 20
              ? 'bg-[var(--color-error)]'
              : robot.battery?.level < 50
              ? 'bg-[var(--color-warning)]'
              : 'bg-[var(--color-success)]'
          }`}
          style={{ width: `${robot.battery?.level || 0}%` }}
        />
      </div>

      {/* Stats Row */}
      <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] mb-3">
        <span className="flex items-center gap-1">
          <Icon size="xs" color={robot.battery?.charging ? 'warning' : 'secondary'}>
            {getBatteryIcon(robot.battery?.level || 0)}
          </Icon>
          {robot.battery?.level || 0}%
        </span>
        <span className="flex items-center gap-1">
          <Icon size="xs" color="secondary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeWidth="2" />
            </svg>
          </Icon>
          {robot.mode.toUpperCase()}
        </span>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-1 pt-3 border-t border-[var(--color-border)]">
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onQuickAction?.(robot.id, 'locate');
          }}
          title="Locate robot"
        >
          <Icon size="sm">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <circle cx="12" cy="12" r="3" strokeWidth="2" />
              <line x1="12" y1="2" x2="12" y2="4" strokeWidth="2" />
              <line x1="12" y1="20" x2="12" y2="22" strokeWidth="2" />
              <line x1="2" y1="12" x2="4" y2="12" strokeWidth="2" />
              <line x1="20" y1="12" x2="22" y2="12" strokeWidth="2" />
            </svg>
          </Icon>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onQuickAction?.(robot.id, 'details');
          }}
          title="View details"
        >
          <Icon size="sm">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <line x1="12" y1="16" x2="12" y2="12" strokeWidth="2" />
              <line x1="12" y1="8" x2="12.01" y2="8" strokeWidth="2" />
            </svg>
          </Icon>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onQuickAction?.(robot.id, 'more');
          }}
          title="More actions"
        >
          <Icon size="sm">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="1" strokeWidth="2" />
              <circle cx="19" cy="12" r="1" strokeWidth="2" />
              <circle cx="5" cy="12" r="1" strokeWidth="2" />
            </svg>
          </Icon>
        </Button>
      </div>
    </div>
  );
};

// ============================================
// Robot List Row Component
// ============================================

interface RobotListRowProps {
  robot: Robot;
  isSelected?: boolean;
  onSelect?: (robotId: string) => void;
  onClick?: (robotId: string) => void;
  onQuickAction?: (robotId: string, action: string) => void;
}

const RobotListRow: React.FC<RobotListRowProps> = ({
  robot,
  isSelected,
  onSelect,
  onClick,
  onQuickAction,
}) => {
  const statusConfig = {
    online: { color: 'success' as const, label: 'Online' },
    busy: { color: 'success' as const, label: 'Busy' },
    offline: { color: 'secondary' as const, label: 'Offline' },
    charging: { color: 'warning' as const, label: 'Charging' },
    error: { color: 'danger' as const, label: 'Error' },
    warning: { color: 'warning' as const, label: 'Warning' },
    idle: { color: 'secondary' as const, label: 'Idle' },
    paused: { color: 'warning' as const, label: 'Paused' },
    maintenance: { color: 'secondary' as const, label: 'Maintenance' },
  };

  const config = statusConfig[robot.status] || statusConfig.offline;

  return (
    <div
      className={`
        grid grid-cols-12 gap-4 items-center p-3 rounded-[var(--radius-md)] border
        transition-colors cursor-pointer
        ${isSelected
          ? 'bg-[var(--color-surface-tertiary)] border-[var(--color-primary)]'
          : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:border-[var(--color-primary)]'
        }
      `}
      onClick={() => onClick?.(robot.id)}
      role="row"
    >
      {/* Selection */}
      <div className="col-span-1">
        <button
          className={`
            w-5 h-5 rounded border flex items-center justify-center
            transition-colors
            ${isSelected
              ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white'
              : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'
            }
          `}
          onClick={(e) => {
            e.stopPropagation();
            onSelect?.(robot.id);
          }}
          aria-label={`Select ${robot.name}`}
        >
          {isSelected && (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <polyline points="20,6 9,17 4,12" strokeWidth="3" />
            </svg>
          )}
        </button>
      </div>

      {/* Name */}
      <div className="col-span-2">
        <p className="text-sm font-medium text-[var(--color-text-primary)]">{robot.name}</p>
        <p className="text-xs text-[var(--color-text-tertiary)]">{robot.serialNumber}</p>
      </div>

      {/* Location */}
      <div className="col-span-2">
        <p className="text-sm text-[var(--color-text-secondary)]">
          {robot.location?.zone || 'Unknown'}
        </p>
      </div>

      {/* Status */}
      <div className="col-span-1">
        <StatusBadge status={robot.status} variant={config.color} size="sm">
          {config.label}
        </StatusBadge>
      </div>

      {/* Battery */}
      <div className="col-span-2">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-[var(--color-surface-tertiary)] rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                robot.battery?.level < 20
                  ? 'bg-[var(--color-error)]'
                  : robot.battery?.level < 50
                  ? 'bg-[var(--color-warning)]'
                  : 'bg-[var(--color-success)]'
              }`}
              style={{ width: `${robot.battery?.level || 0}%` }}
            />
          </div>
          <span className="text-xs text-[var(--color-text-secondary)] w-8">
            {robot.battery?.level || 0}%
          </span>
        </div>
      </div>

      {/* Mode */}
      <div className="col-span-1">
        <span className="text-xs text-[var(--color-text-secondary)] uppercase">
          {robot.mode}
        </span>
      </div>

      {/* Actions */}
      <div className="col-span-1 flex items-center justify-end gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onQuickAction?.(robot.id, 'locate');
          }}
        >
          <Icon size="sm">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <circle cx="12" cy="12" r="3" strokeWidth="2" />
            </svg>
          </Icon>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onQuickAction?.(robot.id, 'more');
          }}
        >
          <Icon size="sm">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="1" strokeWidth="2" />
              <circle cx="19" cy="12" r="1" strokeWidth="2" />
              <circle cx="5" cy="12" r="1" strokeWidth="2" />
            </svg>
          </Icon>
        </Button>
      </div>
    </div>
  );
};

// ============================================
// Selection Bar Component
// ============================================

interface SelectionBarProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: (checked: boolean) => void;
  onBulkStartMission?: (robotIds: string[]) => void;
  onBulkCharge?: (robotIds: string[]) => void;
  onBulkLocate?: (robotIds: string[]) => void;
  onBulkStop?: (robotIds: string[]) => void;
  onBulkReboot?: (robotIds: string[]) => void;
}

const SelectionBar: React.FC<SelectionBarProps> = ({
  selectedCount,
  totalCount,
  onSelectAll,
  onBulkStartMission,
  onBulkCharge,
  onBulkLocate,
  onBulkStop,
  onBulkReboot,
}) => {
  const [showStopDialog, setShowStopDialog] = useState(false);

  const handleStop = () => {
    if (selectedCount > 0) {
      setShowStopDialog(true);
    }
  };

  const confirmStop = () => {
    onBulkStop?.([]);
    setShowStopDialog(false);
  };

  return (
    <>
      <div className="sticky bottom-0 z-10 flex items-center justify-between p-3 bg-[var(--color-surface)] border-t border-[var(--color-border)] shadow-lg">
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]"
            onClick={() => onSelectAll(selectedCount < totalCount)}
          >
            <span
              className={`
                w-5 h-5 rounded border flex items-center justify-center
                transition-colors
                ${selectedCount === totalCount
                  ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white'
                  : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'
                }
              `}
            >
              {selectedCount === totalCount && (
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <polyline points="20,6 9,17 4,12" strokeWidth="3" />
                </svg>
              )}
            </span>
            Select All{selectedCount > 0 && ` (${selectedCount})`}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onBulkStartMission?.([])}
            disabled={selectedCount === 0}
            icon={
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            }
          >
            Start Mission
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onBulkCharge?.([])}
            disabled={selectedCount === 0}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="3" y="6" width="14" height="12" rx="2" strokeWidth="2" />
                <line x1="19" y1="10" x2="19" y2="14" strokeWidth="2" />
              </svg>
            }
          >
            Charge
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onBulkLocate?.([])}
            disabled={selectedCount === 0}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" strokeWidth="2" />
                <circle cx="12" cy="12" r="3" strokeWidth="2" />
              </svg>
            }
          >
            Locate
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleStop}
            disabled={selectedCount === 0}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="4" y="4" width="16" height="16" strokeWidth="2" />
              </svg>
            }
          >
            Stop
          </Button>
        </div>
      </div>

      {/* Emergency Stop Confirmation Dialog */}
      {showStopDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          role="dialog"
          aria-modal="true"
          onClick={() => setShowStopDialog(false)}
        >
          <div
            className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-6 max-w-md w-full mx-4 shadow-xl border-2 border-[var(--color-red-600)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-center mb-4">
              <div className="w-16 h-16 rounded-full bg-[var(--color-red-100)] flex items-center justify-center">
                <svg
                  className="w-10 h-10 text-[var(--color-red-600)]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    strokeWidth="2"
                  />
                </svg>
              </div>
            </div>
            <h3 className="text-lg font-bold text-center text-[var(--color-text-primary)] mb-2">
              Emergency Stop {selectedCount} Robots?
            </h3>
            <p className="text-center text-[var(--color-text-secondary)] mb-4">
              This will immediately halt all selected robots.
            </p>
            <ul className="text-sm text-[var(--color-text-secondary)] space-y-1 mb-6 list-disc list-inside">
              <li>All active missions will be aborted</li>
              <li>Robots will engage emergency brakes</li>
              <li>Systems will enter safe mode</li>
              <li>Manual restart required for each robot</li>
            </ul>
            <div className="flex gap-3">
              <Button
                variant="ghost"
                size="lg"
                onClick={() => setShowStopDialog(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="lg"
                onClick={confirmStop}
                className="flex-1"
              >
                STOP {selectedCount} ROBOTS
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

// ============================================
// Filter Panel Component
// ============================================

interface FilterPanelProps {
  filters: FleetFilters;
  onFilterChange: (filters: FleetFilters) => void;
  locations?: string[];
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFilterChange,
  locations = [],
}) => {
  const statusOptions: { value: RobotStatus; label: string; count?: number }[] = [
    { value: 'online', label: 'Online' },
    { value: 'offline', label: 'Offline' },
    { value: 'charging', label: 'Charging' },
    { value: 'error', label: 'Error' },
    { value: 'warning', label: 'Warning' },
    { value: 'busy', label: 'Busy' },
    { value: 'idle', label: 'Idle' },
    { value: 'paused', label: 'Paused' },
    { value: 'maintenance', label: 'Maintenance' },
  ];

  const modeOptions: { value: RobotMode; label: string }[] = [
    { value: 'auto', label: 'Auto' },
    { value: 'manual', label: 'Manual' },
    { value: 'charging', label: 'Charging' },
    { value: 'sleep', label: 'Sleep' },
    { value: 'error', label: 'Error' },
  ];

  const toggleFilter = <T extends string>(
    current: T[] | undefined,
    value: T,
    onChange: (values: T[] | undefined) => void
  ) => {
    if (!current) {
      onChange([value]);
    } else if (current.includes(value)) {
      const filtered = current.filter((v) => v !== value);
      onChange(filtered.length === 0 ? undefined : filtered);
    } else {
      onChange([...current, value]);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-lg)] border border-[var(--color-border)]">
      {/* Status Filter */}
      <div className="flex items-center gap-2">
        <Icon size="sm" color="secondary">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" strokeWidth="2" />
            <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2" />
            <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2" />
          </svg>
        </Icon>
        <span className="text-xs font-medium text-[var(--color-text-secondary)]">Status:</span>
        <div className="flex items-center gap-1 flex-wrap">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              className={`
                px-2 py-1 text-xs rounded-[var(--radius-sm)] capitalize transition-colors
                ${filters.status?.includes(opt.value)
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'
                }
              `}
              onClick={() => toggleFilter(filters.status || [], opt.value, (v) =>
                onFilterChange({ ...filters, status: v })
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Mode Filter */}
      <div className="flex items-center gap-2">
        <Icon size="sm" color="secondary">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeWidth="2" />
          </svg>
        </Icon>
        <span className="text-xs font-medium text-[var(--color-text-secondary)]">Mode:</span>
        <div className="flex items-center gap-1 flex-wrap">
          {modeOptions.map((opt) => (
            <button
              key={opt.value}
              className={`
                px-2 py-1 text-xs rounded-[var(--radius-sm)] capitalize transition-colors
                ${filters.mode?.includes(opt.value)
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'
                }
              `}
              onClick={() => toggleFilter(filters.mode || [], opt.value, (v) =>
                onFilterChange({ ...filters, mode: v })
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search */}
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

// ============================================
// Main FleetOverview Component
// ============================================

// Define FleetOverviewProps locally since it may not be exported from fleet.ts
interface LocalFleetOverviewProps {
  // Data
  robots: Robot[];
  isLoading?: boolean;

  // View
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;

  // Filtering
  filters: FleetFilters;
  onFilterChange: (filters: FleetFilters) => void;

  // Sorting
  sortConfig?: FleetSortConfig;
  onSortChange?: (config: FleetSortConfig) => void;

  // Selection
  selectedRobotIds: string[];
  onSelectionChange: (ids: string[]) => void;

  // Bulk Actions
  onBulkStartMission?: (robotIds: string[]) => void;
  onBulkCharge?: (robotIds: string[]) => void;
  onBulkLocate?: (robotIds: string[]) => void;
  onBulkStop?: (robotIds: string[]) => void;
  onBulkReboot?: (robotIds: string[]) => void;

  // Row/Card Actions
  onRobotClick: (robotId: string) => void;
  onQuickAction?: (robotId: string, action: string) => void;

  // Pagination
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
  };
  onPageChange?: (page: number) => void;

  // Styling
  className?: string;
  compact?: boolean;
}

export const FleetOverview: React.FC<LocalFleetOverviewProps> = ({
  robots = [],
  isLoading = false,
  viewMode = 'grid',
  onViewModeChange,
  filters,
  onFilterChange,
  sortConfig,
  onSortChange,
  selectedRobotIds = [],
  onSelectionChange,
  onBulkStartMission,
  onBulkCharge,
  onBulkLocate,
  onBulkStop,
  onBulkReboot,
  onRobotClick,
  onQuickAction,
  pagination,
  onPageChange,
  className = '',
  compact = false,
}) => {
  // Get unique locations from robots
  const locations = useMemo(() => {
    const locs = new Set(robots.map((r) => r.location?.zone).filter(Boolean));
    return Array.from(locs) as string[];
  }, [robots]);

  // Filter robots
  const filteredRobots = useMemo(() => {
    return robots.filter((robot) => {
      // Status filter
      if (filters.status && filters.status.length > 0) {
        if (!filters.status.includes(robot.status)) return false;
      }

      // Mode filter
      if (filters.mode && filters.mode.length > 0) {
        if (!filters.mode.includes(robot.mode)) return false;
      }

      // Location filter
      if (filters.location && filters.location.length > 0) {
        if (!filters.location.includes(robot.location?.zone || '')) return false;
      }

      // Battery range filter
      if (filters.batteryRange) {
        const level = robot.battery?.level || 0;
        if (level < (filters.batteryRange.min || 0)) return false;
        if (level > (filters.batteryRange.max || 100)) return false;
      }

      // Search filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const name = robot.name.toLowerCase();
        const serial = robot.serialNumber?.toLowerCase() || '';
        const zone = robot.location?.zone?.toLowerCase() || '';
        if (!name.includes(query) && !serial.includes(query) && !zone.includes(query)) {
          return false;
        }
      }

      return true;
    });
  }, [robots, filters]);

  // Sort robots
  const sortedRobots = useMemo(() => {
    if (!sortConfig) return filteredRobots;

    return [...filteredRobots].sort((a, b) => {
      let aVal: any;
      let bVal: any;

      switch (sortConfig.field) {
        case 'name':
          aVal = a.name;
          bVal = b.name;
          break;
        case 'location':
          aVal = a.location?.zone || '';
          bVal = b.location?.zone || '';
          break;
        case 'status':
          aVal = a.status;
          bVal = b.status;
          break;
        case 'battery':
          aVal = a.battery?.level || 0;
          bVal = b.battery?.level || 0;
          break;
        case 'lastSeen':
          aVal = a.lastSeen?.getTime() || 0;
          bVal = b.lastSeen?.getTime() || 0;
          break;
        default:
          return 0;
      }

      const direction = sortConfig.direction === 'asc' ? 1 : -1;
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return direction * aVal.localeCompare(bVal);
      }
      return direction * ((aVal as number) - (bVal as number));
    });
  }, [filteredRobots, sortConfig]);

  // Handle select all
  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        onSelectionChange(sortedRobots.map((r) => r.id));
      } else {
        onSelectionChange([]);
      }
    },
    [sortedRobots, onSelectionChange]
  );

  // Handle individual selection
  const handleSelectRobot = useCallback(
    (robotId: string) => {
      if (selectedRobotIds.includes(robotId)) {
        onSelectionChange(selectedRobotIds.filter((id) => id !== robotId));
      } else {
        onSelectionChange([...selectedRobotIds, robotId]);
      }
    },
    [selectedRobotIds, onSelectionChange]
  );

  if (compact) {
    return (
      <div
        className={`
          flex flex-col gap-3
          bg-[var(--color-surface)]
          border border-[var(--color-border)]
          rounded-[var(--radius-lg)]
          p-4
          ${className}
        `}
        role="region"
        aria-label="Fleet overview"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Fleet Overview
          </h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-[var(--color-text-secondary)]">
              {filteredRobots.length} robots
            </span>
          </div>
        </div>

        {/* Mini Stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center p-2 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-sm)]">
            <p className="text-lg font-semibold text-[var(--color-success)]">
              {robots.filter((r) => r.status === 'online').length}
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)]">Online</p>
          </div>
          <div className="text-center p-2 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-sm)]">
            <p className="text-lg font-semibold text-[var(--color-warning)]">
              {robots.filter((r) => r.status === 'charging').length}
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)]">Charging</p>
          </div>
          <div className="text-center p-2 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-sm)]">
            <p className="text-lg font-semibold text-[var(--color-text-secondary)]">
              {robots.filter((r) => r.status === 'offline').length}
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)]">Offline</p>
          </div>
        </div>

        {/* Robot List Preview */}
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {sortedRobots.slice(0, 5).map((robot) => (
            <div
              key={robot.id}
              className="flex items-center justify-between p-2 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-sm)]"
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    robot.status === 'online'
                      ? 'bg-[var(--color-success)]'
                      : robot.status === 'charging'
                      ? 'bg-[var(--color-warning)]'
                      : 'bg-[var(--color-text-tertiary)]'
                  }`}
                />
                <span className="text-sm text-[var(--color-text-primary)]">{robot.name}</span>
              </div>
              <span className="text-xs text-[var(--color-text-secondary)]">
                {robot.battery?.level || 0}%
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        flex flex-col gap-4
        bg-[var(--color-surface)]
        border border-[var(--color-border)]
        rounded-[var(--radius-lg)]
        p-4
        ${className}
      `}
      role="region"
      aria-label="Fleet overview"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Fleet Overview
          </h2>
          <p className="text-sm text-[var(--color-text-tertiary)]">
            {filteredRobots.length} of {robots.length} robots
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)] p-1">
            <button
              className={`
                px-3 py-1.5 text-xs font-medium rounded-[var(--radius-sm)] flex items-center gap-1
                transition-colors
                ${viewMode === 'grid'
                  ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                }
              `}
              onClick={() => onViewModeChange('grid')}
              aria-pressed={viewMode === 'grid'}
            >
              <Icon size="sm">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <rect x="3" y="3" width="7" height="7" strokeWidth="2" />
                  <rect x="14" y="3" width="7" height="7" strokeWidth="2" />
                  <rect x="3" y="14" width="7" height="7" strokeWidth="2" />
                  <rect x="14" y="14" width="7" height="7" strokeWidth="2" />
                </svg>
              </Icon>
              Grid
            </button>
            <button
              className={`
                px-3 py-1.5 text-xs font-medium rounded-[var(--radius-sm)] flex items-center gap-1
                transition-colors
                ${viewMode === 'list'
                  ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                }
              `}
              onClick={() => onViewModeChange('list')}
              aria-pressed={viewMode === 'list'}
            >
              <Icon size="sm">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <line x1="4" y1="6" x2="20" y2="6" strokeWidth="2" />
                  <line x1="4" y1="12" x2="20" y2="12" strokeWidth="2" />
                  <line x1="4" y1="18" x2="20" y2="18" strokeWidth="2" />
                </svg>
              </Icon>
              List
            </button>
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <line x1="12" y1="5" x2="12" y2="19" strokeWidth="2" />
                <line x1="5" y1="12" x2="19" y2="12" strokeWidth="2" />
              </svg>
            }
          >
            Add Robot
          </Button>
        </div>
      </div>

      {/* Stats Bar */}
      <FleetStatsBar robots={robots} />

      {/* Filters */}
      <FilterPanel
        filters={filters}
        onFilterChange={onFilterChange}
        locations={locations}
      />

      {/* Loading State */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Icon size="xl" color="secondary" isAnimated>
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" strokeOpacity="0.25" />
              <path d="M12 2a10 10 0 0110 10" strokeWidth="2" className="animate-spin origin-center" />
            </svg>
          </Icon>
          <span className="ml-3 text-[var(--color-text-secondary)]">Loading robots...</span>
        </div>
      ) : sortedRobots.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-12">
          <Icon size="xl" color="tertiary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <line x1="12" y1="8" x2="12" y2="12" strokeWidth="2" />
              <line x1="12" y1="16" x2="12.01" y2="16" strokeWidth="2" />
            </svg>
          </Icon>
          <p className="mt-3 text-[var(--color-text-secondary)]">
            No robots match your filters
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() =>
              onFilterChange({
                status: undefined,
                mode: undefined,
                location: undefined,
                searchQuery: undefined,
                batteryRange: undefined,
              })
            }
          >
            Clear Filters
          </Button>
        </div>
      ) : viewMode === 'grid' ? (
        /* Grid View */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {sortedRobots.map((robot) => (
            <RobotGridCard
              key={robot.id}
              robot={robot}
              isSelected={selectedRobotIds.includes(robot.id)}
              onSelect={handleSelectRobot}
              onClick={onRobotClick}
              onQuickAction={onQuickAction}
            />
          ))}
        </div>
      ) : (
        /* List View */
        <div className="flex flex-col gap-2">
          {/* List Header */}
          <div className="grid grid-cols-12 gap-4 px-3 py-2 text-xs font-medium text-[var(--color-text-secondary)] border-b border-[var(--color-border)]">
            <div className="col-span-1">Select</div>
            <div className="col-span-2">Name</div>
            <div className="col-span-2">Location</div>
            <div className="col-span-1">Status</div>
            <div className="col-span-2">Battery</div>
            <div className="col-span-1">Mode</div>
            <div className="col-span-1">Actions</div>
          </div>
          {sortedRobots.map((robot) => (
            <RobotListRow
              key={robot.id}
              robot={robot}
              isSelected={selectedRobotIds.includes(robot.id)}
              onSelect={handleSelectRobot}
              onClick={onRobotClick}
              onQuickAction={onQuickAction}
            />
          ))}
        </div>
      )}

      {/* Selection Bar (when robots selected) */}
      {selectedRobotIds.length > 0 && (
        <SelectionBar
          selectedCount={selectedRobotIds.length}
          totalCount={sortedRobots.length}
          onSelectAll={handleSelectAll}
          onBulkStartMission={onBulkStartMission}
          onBulkCharge={onBulkCharge}
          onBulkLocate={onBulkLocate}
          onBulkStop={onBulkStop}
          onBulkReboot={onBulkReboot}
        />
      )}
    </div>
  );
};

export default FleetOverview;
