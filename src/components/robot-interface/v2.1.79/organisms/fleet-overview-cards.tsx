/**
 * FleetOverview Cards & Stats Bar - RaaS UX Kit v2.1.79
 */
import React, { useMemo } from 'react';
import { Button } from '../atoms/Button';
import { Icon } from '../atoms/Icon';
import { StatusBadge } from '../atoms/StatusBadge';
import { Robot, RobotStatus } from '../types/robot';

export const FleetStatsBar: React.FC<{ robots: Robot[] }> = ({ robots }) => {
  const stats = useMemo(
    () => ({
      total: robots.length,
      online: robots.filter((r) => r.status === 'online' || r.status === 'busy').length,
      offline: robots.filter((r) => r.status === 'offline').length,
      charging: robots.filter((r) => r.status === 'charging').length,
      error: robots.filter((r) => r.status === 'error' || r.status === 'warning').length,
      maintenance: robots.filter((r) => r.status === 'maintenance').length,
    }),
    [robots]
  );

  const items = [
    { label: 'Total Robots', value: stats.total, color: 'text-[var(--color-text-primary)]' },
    { label: 'Online', value: stats.online, color: 'text-[var(--color-success)]' },
    { label: 'Offline', value: stats.offline, color: 'text-[var(--color-text-secondary)]' },
    { label: 'Charging', value: stats.charging, color: 'text-[var(--color-caution)]' },
    { label: 'Error', value: stats.error, color: 'text-[var(--color-error)]' },
    { label: 'Maintenance', value: stats.maintenance, color: 'text-[var(--color-text-tertiary)]' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
      {items.map((item) => (
        <div key={item.label} className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
          <span className="text-xs text-[var(--color-text-secondary)] mb-1">{item.label}</span>
          <span className={`text-lg font-semibold tabular-nums ${item.color}`}>{item.value}</span>
        </div>
      ))}
    </div>
  );
};

const statusLabelMap: Record<RobotStatus, string> = {
  online: 'Online', busy: 'Busy', offline: 'Offline', charging: 'Charging', error: 'Error',
  warning: 'Warning', idle: 'Idle', paused: 'Paused', maintenance: 'Maintenance',
};

export interface RobotItemCardProps {
  robot: Robot;
  isSelected?: boolean;
  onSelect?: (robotId: string) => void;
  onClick?: (robotId: string) => void;
  onQuickAction?: (robotId: string, action: string) => void;
}

const SelectCheck: React.FC<{ isSelected?: boolean; name: string; onSelect?: () => void }> = ({ isSelected, name, onSelect }) => (
  <button
    type="button"
    className={`w-5 h-5 rounded border flex items-center justify-center transition-colors cursor-pointer ${
      isSelected ? 'bg-[var(--color-primary)] border-[var(--color-primary)] text-white' : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'
    }`}
    onClick={(e) => { e.stopPropagation(); onSelect?.(); }}
    aria-label={`Select ${name}`}
  >
    {isSelected && (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <polyline points="20,6 9,17 4,12" strokeWidth="3" />
      </svg>
    )}
  </button>
);

export const RobotGridCard: React.FC<RobotItemCardProps> = ({ robot, isSelected, onSelect, onClick, onQuickAction }) => {
  const level = robot.battery?.level || 0;
  const barColor = level < 20 ? 'bg-[var(--color-error)]' : level < 50 ? 'bg-[var(--color-caution)]' : 'bg-[var(--color-success)]';

  return (
    <div
      className={`flex flex-col p-4 rounded-[var(--radius-lg)] border transition-all duration-150 cursor-pointer ${
        isSelected ? 'bg-[var(--color-surface-tertiary)] border-[var(--color-primary)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:border-[var(--color-primary)]'
      }`}
      onClick={() => onClick?.(robot.id)}
      role="article"
      aria-label={`Robot ${robot.name}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <SelectCheck isSelected={isSelected} name={robot.name} onSelect={() => onSelect?.(robot.id)} />
          <div>
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{robot.name}</h3>
            <p className="text-xs text-[var(--color-text-tertiary)]">{robot.location?.zone || 'Unknown'}</p>
          </div>
        </div>
        <StatusBadge variant={robot.status} size="sm">{statusLabelMap[robot.status] || 'Offline'}</StatusBadge>
      </div>

      <div className="w-full h-1.5 bg-[var(--color-surface-tertiary)] rounded-full overflow-hidden mb-3">
        <div className={`h-full transition-all duration-300 ${barColor}`} style={{ width: `${level}%` }} />
      </div>

      <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] mb-3 tabular-nums">
        <span>{level}%</span>
        <span>{robot.mode.toUpperCase()}</span>
      </div>

      <div className="flex items-center gap-1 pt-3 border-t border-[var(--color-border)]">
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onQuickAction?.(robot.id, 'locate'); }} aria-label="Locate robot">
          <Icon size="sm"><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" /></Icon>
        </Button>
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onQuickAction?.(robot.id, 'details'); }} aria-label="View details">
          <Icon size="sm"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></Icon>
        </Button>
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onQuickAction?.(robot.id, 'more'); }} aria-label="More actions">
          <Icon size="sm"><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /><circle cx="5" cy="12" r="1" /></Icon>
        </Button>
      </div>
    </div>
  );
};

export const RobotListRow: React.FC<RobotItemCardProps> = ({ robot, isSelected, onSelect, onClick, onQuickAction }) => {
  const level = robot.battery?.level || 0;
  const barColor = level < 20 ? 'bg-[var(--color-error)]' : level < 50 ? 'bg-[var(--color-caution)]' : 'bg-[var(--color-success)]';

  return (
    <div
      className={`grid grid-cols-12 gap-4 items-center p-3 rounded-[var(--radius-md)] border transition-colors cursor-pointer ${
        isSelected ? 'bg-[var(--color-surface-tertiary)] border-[var(--color-primary)]' : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:border-[var(--color-primary)]'
      }`}
      onClick={() => onClick?.(robot.id)}
      role="row"
    >
      <div className="col-span-1"><SelectCheck isSelected={isSelected} name={robot.name} onSelect={() => onSelect?.(robot.id)} /></div>
      <div className="col-span-2">
        <p className="text-sm font-medium text-[var(--color-text-primary)]">{robot.name}</p>
        <p className="text-xs text-[var(--color-text-tertiary)]">{robot.serialNumber}</p>
      </div>
      <div className="col-span-2"><p className="text-sm text-[var(--color-text-secondary)]">{robot.location?.zone || 'Unknown'}</p></div>
      <div className="col-span-2"><StatusBadge variant={robot.status} size="sm">{statusLabelMap[robot.status] || 'Offline'}</StatusBadge></div>
      <div className="col-span-2 flex items-center gap-2">
        <div className="flex-1 h-2 bg-[var(--color-surface-tertiary)] rounded-full overflow-hidden">
          <div className={`h-full transition-all ${barColor}`} style={{ width: `${level}%` }} />
        </div>
        <span className="text-xs text-[var(--color-text-secondary)] w-8 tabular-nums">{level}%</span>
      </div>
      <div className="col-span-1"><span className="text-xs text-[var(--color-text-secondary)] uppercase">{robot.mode}</span></div>
      <div className="col-span-2 flex items-center justify-end gap-1">
        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onQuickAction?.(robot.id, 'locate'); }} aria-label="Locate robot">
          <Icon size="sm"><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" /></Icon>
        </Button>
      </div>
    </div>
  );
};
