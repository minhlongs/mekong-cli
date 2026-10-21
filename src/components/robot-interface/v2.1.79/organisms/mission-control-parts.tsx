/**
 * MissionControl Subcomponents - RaaS UX Kit v2.1.79
 * MissionProgress, MissionListItem, MissionLogsTerminal, and EmergencyStopDialog
 */
import React, { useMemo, useRef, useEffect } from 'react';
import { Button } from '../atoms/Button';
import { Icon } from '../atoms/Icon';
import { StatusBadge } from '../atoms/StatusBadge';
import { Mission, MissionLog, LogLevel } from '../types/mission';

export const MissionProgress: React.FC<{
  percentage: number; currentWaypoint: number; totalWaypoints: number; elapsed: string; remaining?: string;
}> = ({ percentage, currentWaypoint, totalWaypoints, elapsed, remaining }) => (
  <div className="w-full">
    <div className="relative h-2 bg-[var(--color-surface-tertiary)] rounded-full overflow-hidden mb-2">
      <div
        className="absolute top-0 left-0 h-full bg-[var(--color-primary)] transition-all duration-300"
        style={{ width: `${percentage}%` }} role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}
      />
    </div>
    <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)] tabular-nums">
      <span>Waypoint {currentWaypoint + 1}/{totalWaypoints}</span>
      <span>{percentage.toFixed(0)}%</span>
    </div>
    <div className="flex items-center gap-4 mt-2 text-xs text-[var(--color-text-tertiary)] tabular-nums">
      <span className="flex items-center gap-1">
        <Icon size="sm" color="secondary"><circle cx="12" cy="12" r="10" /><polyline points="12,6 12,12 16,14" /></Icon>
        Elapsed: {elapsed}
      </span>
      {remaining && (
        <span className="flex items-center gap-1">
          <Icon size="sm" color="secondary"><path d="M12 2v20M2 12l10-10 10 10" /></Icon>
          ETA: {remaining}
        </span>
      )}
    </div>
  </div>
);

const missionStatusMap = {
  pending: { label: 'Scheduled', variant: 'idle' as const }, queued: { label: 'Queued', variant: 'busy' as const },
  running: { label: 'In Progress', variant: 'online' as const }, paused: { label: 'Paused', variant: 'warning' as const },
  completed: { label: 'Completed', variant: 'online' as const }, aborted: { label: 'Aborted', variant: 'error' as const },
  failed: { label: 'Failed', variant: 'error' as const },
};

export const MissionListItem: React.FC<{
  mission: Mission; isSelected?: boolean; onSelect?: () => void; onQuickAction?: (action: string) => void;
}> = ({ mission, isSelected, onSelect, onQuickAction }) => {
  const config = missionStatusMap[mission.status];
  return (
    <div
      className={`flex items-center justify-between p-3 rounded-[var(--radius-md)] border border-[var(--color-border)] ${
        isSelected ? 'bg-[var(--color-surface-tertiary)]' : 'bg-[var(--color-surface)]'
      } hover:border-[var(--color-primary)] transition-colors cursor-pointer`}
      onClick={onSelect} role="listitem"
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <StatusBadge variant={config.variant} size="sm">{config.label}</StatusBadge>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">{mission.name}</p>
          <p className="text-xs text-[var(--color-text-tertiary)] truncate">{mission.type}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {mission.status === 'running' && (
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onQuickAction?.('pause'); }} aria-label="Pause mission">
            <Icon size="sm"><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></Icon>
          </Button>
        )}
        {mission.status === 'paused' && (
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); onQuickAction?.('resume'); }} aria-label="Resume mission">
            <Icon size="sm"><polygon points="5,3 19,12 5,21" fill="currentColor" stroke="none" /></Icon>
          </Button>
        )}
      </div>
    </div>
  );
};

const allLevels: LogLevel[] = ['debug', 'info', 'warn', 'error', 'critical'];
const levelStyles: Record<LogLevel, string> = {
  debug: 'bg-[var(--color-surface-variant)] text-[var(--color-text-secondary)]',
  info: 'bg-[var(--color-primary-container)] text-[var(--color-primary-on-container)]',
  warn: 'bg-[var(--color-status-warning-subtle)] text-[var(--color-caution)]',
  error: 'bg-[var(--color-error-container)] text-[var(--color-error)]',
  critical: 'bg-[var(--color-safety-critical)] text-white animate-pulse',
};

export const MissionLogsTerminal: React.FC<{
  logs: MissionLog[]; filter?: LogLevel[]; onFilterChange?: (levels: LogLevel[]) => void; onExport?: (format: 'txt' | 'json') => void;
  onClear?: () => void; autoScroll?: boolean; followMode?: boolean; onFollowToggle?: () => void;
}> = ({ logs, filter, onFilterChange, onExport, onClear, autoScroll = true, followMode = true, onFollowToggle }) => {
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && followMode && logsEndRef.current) logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [logs, autoScroll, followMode]);

  const filteredLogs = useMemo(() => (!filter || filter.length === 0 ? logs : logs.filter((log) => filter.includes(log.level))), [logs, filter]);

  return (
    <div className="flex flex-col h-full bg-[var(--color-surface-tertiary)] rounded-[var(--radius-lg)] border border-[var(--color-border)]">
      <div className="flex items-center justify-between p-2 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-[var(--color-text-secondary)]">Mission Logs</span>
          <div className="flex items-center gap-1">
            {allLevels.map((level) => (
              <button
                key={level} type="button"
                className={`px-2 py-0.5 text-[10px] font-medium uppercase rounded-[var(--radius-sm)] transition-colors cursor-pointer ${
                  !filter || filter.includes(level) ? levelStyles[level] : 'bg-[var(--color-surface)] text-[var(--color-text-tertiary)] opacity-50'
                }`}
                onClick={() => {
                  if (!filter) onFilterChange?.(allLevels.filter((l) => l !== level));
                  else if (filter.includes(level)) onFilterChange?.(filter.filter((l) => l !== level));
                  else onFilterChange?.([...filter, level]);
                }}
              >
                {level.slice(0, 4)}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button" onClick={onFollowToggle}
            className={`flex items-center gap-1 px-2 py-1 text-xs rounded-[var(--radius-sm)] cursor-pointer ${
              followMode ? 'bg-[var(--color-primary-container)] text-[var(--color-primary)]' : 'bg-[var(--color-surface)] text-[var(--color-text-tertiary)]'
            }`}
          >
            Follow
          </button>
          <Button variant="ghost" size="sm" onClick={() => onExport?.('txt')} aria-label="Export logs">Export</Button>
          <Button variant="ghost" size="sm" onClick={onClear} aria-label="Clear logs">Clear</Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 font-mono text-xs max-h-[300px]">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-[var(--color-text-tertiary)] py-8"><p>No logs to display</p></div>
        ) : (
          filteredLogs.map((log) => (
            <div key={log.id || log.timestamp.toISOString()} className="flex items-start gap-2 py-1 hover:bg-[var(--color-surface)] rounded px-1">
              <span className="text-[var(--color-text-tertiary)] flex-shrink-0 tabular-nums">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold flex-shrink-0 ${levelStyles[log.level]}`}>{log.level.toUpperCase()}</span>
              {log.source && <span className="text-[var(--color-text-secondary)] flex-shrink-0">[{log.source}]</span>}
              <span className="text-[var(--color-text-primary)] flex-1 break-all">{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export const EmergencyStopDialog: React.FC<{ open: boolean; onConfirm: () => void; onCancel: () => void }> = ({ open, onConfirm, onCancel }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Emergency stop confirmation" onClick={onCancel}>
      <div className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-6 max-w-md w-full mx-4 shadow-xl border-2 border-[var(--color-error)]" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-center text-[var(--color-text-primary)] mb-2">Emergency Stop</h3>
        <p className="text-center text-[var(--color-text-secondary)] mb-4">This will immediately halt all robot operations.</p>
        <ul className="text-sm text-[var(--color-text-secondary)] space-y-1 mb-6 list-disc list-inside">
          <li>Mission will be aborted</li><li>Robot will engage brakes</li><li>Systems will enter safe mode</li><li>Manual restart required</li>
        </ul>
        <div className="flex gap-3">
          <Button variant="ghost" size="lg" onClick={onCancel} className="flex-1">Cancel</Button>
          <Button variant="danger" size="lg" onClick={onConfirm} className="flex-1">CONFIRM STOP</Button>
        </div>
      </div>
    </div>
  );
};
