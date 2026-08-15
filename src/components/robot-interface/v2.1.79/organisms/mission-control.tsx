/**
 * MissionControl Component - RaaS UX Kit v2.1.79
 * Mission management interface with playback controls, progress tracking, and logs terminal
 */

import React, { useState, useCallback, useMemo, useRef } from 'react';
import { Button } from '../../atoms/Button';
import { Icon } from '../../atoms/Icon';
import { StatusBadge } from '../../atoms/StatusBadge';
import {
  MissionControlProps,
  Mission,
  MissionLog,
  LogLevel,
  MissionProgress as MissionProgressType,
} from '../../types/mission';

// ============================================
// Mission Progress Bar Component
// ============================================

interface MissionProgressProps {
  percentage: number;
  currentWaypoint: number;
  totalWaypoints: number;
  elapsed: string;
  remaining?: string;
}

const MissionProgress: React.FC<MissionProgressProps> = ({
  percentage,
  currentWaypoint,
  totalWaypoints,
  elapsed,
  remaining,
}) => {
  return (
    <div className="w-full">
      {/* Progress Bar */}
      <div className="relative h-2 bg-[var(--color-surface-tertiary)] rounded-full overflow-hidden mb-2">
        <div
          className="absolute top-0 left-0 h-full bg-[var(--color-primary)] transition-all duration-300"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Progress Info */}
      <div className="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
        <span>
          Waypoint {currentWaypoint + 1}/{totalWaypoints}
        </span>
        <span>{percentage.toFixed(0)}%</span>
      </div>

      {/* Time Info */}
      <div className="flex items-center gap-4 mt-2 text-xs text-[var(--color-text-tertiary)]">
        <span className="flex items-center gap-1">
          <Icon size="sm" color="secondary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" strokeWidth="2" />
              <polyline points="12,6 12,12 16,14" strokeWidth="2" />
            </svg>
          </Icon>
          Elapsed: {elapsed}
        </span>
        {remaining && (
          <span className="flex items-center gap-1">
            <Icon size="sm" color="secondary">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M12 2v20M2 12l10-10 10 10" strokeWidth="2" />
              </svg>
            </Icon>
            ETA: {remaining}
          </span>
        )}
      </div>
    </div>
  );
};

// ============================================
// Mission List Item Component
// ============================================

interface MissionListItemProps {
  mission: Mission;
  isSelected?: boolean;
  onSelect?: () => void;
  onQuickAction?: (action: string) => void;
}

const MissionListItem: React.FC<MissionListItemProps> = ({
  mission,
  isSelected,
  onSelect,
  onQuickAction,
}) => {
  const statusConfig = {
    pending: { label: 'Scheduled', variant: 'secondary' as const },
    queued: { label: 'Queued', variant: 'info' as const },
    running: { label: 'In Progress', variant: 'success' as const },
    paused: { label: 'Paused', variant: 'warning' as const },
    completed: { label: 'Completed', variant: 'success' as const },
    aborted: { label: 'Aborted', variant: 'danger' as const },
    failed: { label: 'Failed', variant: 'danger' as const },
  };

  const config = statusConfig[mission.status];

  return (
    <div
      className={`
        flex items-center justify-between p-3 rounded-[var(--radius-md)]
        border border-[var(--color-border)]
        ${isSelected ? 'bg-[var(--color-surface-tertiary)]' : 'bg-[var(--color-surface)]'}
        hover:border-[var(--color-primary)] transition-colors cursor-pointer
      `}
      onClick={onSelect}
      role="listitem"
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <StatusBadge status={mission.status} variant={config.variant}>
          {config.label}
        </StatusBadge>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
            {mission.name}
          </p>
          <p className="text-xs text-[var(--color-text-tertiary)] truncate">
            {mission.type}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {mission.status === 'running' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onQuickAction?.('pause');
            }}
          >
            <Icon size="sm">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" strokeWidth="2" />
                <rect x="14" y="4" width="4" height="16" strokeWidth="2" />
              </svg>
            </Icon>
          </Button>
        )}
        {mission.status === 'paused' && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onQuickAction?.('resume');
            }}
          >
            <Icon size="sm">
              <svg fill="currentColor" viewBox="0 0 24 24">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            </Icon>
          </Button>
        )}
        <Icon size="sm" color="tertiary">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="1" strokeWidth="2" />
            <circle cx="12" cy="5" r="1" strokeWidth="2" />
            <circle cx="12" cy="19" r="1" strokeWidth="2" />
          </svg>
        </Icon>
      </div>
    </div>
  );
};

// ============================================
// Mission Logs Terminal Component
// ============================================

interface MissionLogsTerminalProps {
  logs: MissionLog[];
  filter?: LogLevel[];
  onFilterChange?: (levels: LogLevel[]) => void;
  onExport?: (format: 'txt' | 'json') => void;
  onClear?: () => void;
  autoScroll?: boolean;
  followMode?: boolean;
  onFollowToggle?: () => void;
}

const MissionLogsTerminal: React.FC<MissionLogsTerminalProps> = ({
  logs,
  filter,
  onFilterChange,
  onExport,
  onClear,
  autoScroll = true,
  followMode = true,
  onFollowToggle,
}) => {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  React.useEffect(() => {
    if (autoScroll && followMode && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, followMode]);

  // Filter logs by level
  const filteredLogs = useMemo(() => {
    if (!filter || filter.length === 0) return logs;
    return logs.filter((log) => filter.includes(log.level));
  }, [logs, filter]);

  // Get level styling
  const getLevelStyles = (level: LogLevel): string => {
    const styles = {
      debug: 'bg-[var(--color-gray-100)] text-[var(--color-gray-600)]',
      info: 'bg-[var(--color-blue-100)] text-[var(--color-blue-600)]',
      warn: 'bg-[var(--color-amber-100)] text-[var(--color-amber-600)]',
      error: 'bg-[var(--color-red-100)] text-[var(--color-red-600)]',
      critical: 'bg-[var(--color-red-600)] text-white animate-pulse',
    };
    return styles[level] || styles.debug;
  };

  const allLevels: LogLevel[] = ['debug', 'info', 'warn', 'error', 'critical'];

  return (
    <div className="flex flex-col h-full bg-[var(--color-surface-tertiary)] rounded-[var(--radius-lg)] border border-[var(--color-border)]">
      {/* Terminal Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-[var(--color-text-secondary)]">
            Mission Logs
          </span>
          {/* Level Filter Buttons */}
          <div className="flex items-center gap-1">
            {allLevels.map((level) => (
              <button
                key={level}
                className={`
                  px-2 py-0.5 text-[10px] font-medium uppercase rounded-[var(--radius-sm)]
                  transition-colors
                  ${!filter || filter.includes(level)
                    ? getLevelStyles(level)
                    : 'bg-[var(--color-surface)] text-[var(--color-text-tertiary)] opacity-50'
                  }
                `}
                onClick={() => {
                  if (!filter) {
                    onFilterChange?.(allLevels.filter((l) => l !== level));
                  } else if (filter.includes(level)) {
                    const newFilter = filter.filter((l) => l !== level);
                    onFilterChange?.(newFilter.length === 0 ? [] : newFilter);
                  } else {
                    onFilterChange?.([...filter, level]);
                  }
                }}
                title={`${level} logs`}
              >
                {level.slice(0, 4)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-1">
          {/* Follow Toggle */}
          <button
            className={`
              flex items-center gap-1 px-2 py-1 text-xs rounded-[var(--radius-sm)]
              ${followMode
                ? 'bg-[var(--color-primary-subtle)] text-[var(--color-primary)]'
                : 'bg-[var(--color-surface)] text-[var(--color-text-tertiary)]'
              }
            `}
            onClick={onFollowToggle}
            title="Auto-scroll to latest log"
          >
            <Icon size="xs">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M19 14l-7 7m0 0l-7-7m7 7V3" strokeWidth="2" />
              </svg>
            </Icon>
            Follow
          </button>

          {/* Export */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onExport?.('txt')}
            title="Export logs"
          >
            <Icon size="sm">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" strokeWidth="2" />
                <polyline points="7,10 12,15 17,10" strokeWidth="2" />
                <line x1="12" y1="15" x2="12" y2="3" strokeWidth="2" />
              </svg>
            </Icon>
          </Button>

          {/* Clear */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            title="Clear logs"
          >
            <Icon size="sm" color="danger">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <polyline points="3,6 5,6 21,6" strokeWidth="2" />
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeWidth="2" />
              </svg>
            </Icon>
          </Button>
        </div>
      </div>

      {/* Logs Content */}
      <div
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-2 font-mono text-xs"
        style={{ maxHeight: '300px' }}
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center text-[var(--color-text-tertiary)] py-8">
            <p>No logs to display</p>
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id || log.timestamp.toISOString()}
              className="flex items-start gap-2 py-1 hover:bg-[var(--color-surface)] rounded px-1"
            >
              <span className="text-[var(--color-text-tertiary)] flex-shrink-0">
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-semibold flex-shrink-0 ${getLevelStyles(log.level)}`}
              >
                {log.level.toUpperCase()}
              </span>
              {log.source && (
                <span className="text-[var(--color-text-secondary)] flex-shrink-0">
                  [{log.source}]
                </span>
              )}
              <span className="text-[var(--color-text-primary)] flex-1 break-all">
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

// ============================================
// Emergency Stop Dialog Component
// ============================================

interface EmergencyStopDialogProps {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const EmergencyStopDialog: React.FC<EmergencyStopDialogProps> = ({
  open,
  onConfirm,
  onCancel,
}) => {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="Emergency stop confirmation"
      onClick={onCancel}
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
          Emergency Stop
        </h3>

        <p className="text-center text-[var(--color-text-secondary)] mb-4">
          This will immediately halt all robot operations.
        </p>

        <ul className="text-sm text-[var(--color-text-secondary)] space-y-1 mb-6 list-disc list-inside">
          <li>Mission will be aborted</li>
          <li>Robot will engage brakes</li>
          <li>Systems will enter safe mode</li>
          <li>Manual restart required</li>
        </ul>

        <div className="flex gap-3">
          <Button
            variant="ghost"
            size="lg"
            onClick={onCancel}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            size="lg"
            onClick={onConfirm}
            className="flex-1"
          >
            <span className="flex items-center justify-center gap-2">
              <span>🛑</span> CONFIRM STOP
            </span>
          </Button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// Main MissionControl Component
// ============================================

export const MissionControl: React.FC<MissionControlProps> = ({
  robotId,
  missions = [],
  activeMission,
  onCreateMission,
  onLaunchMission,
  onPauseMission,
  onResumeMission,
  onAbortMission,
  isPlaying,
  isPaused,
  onPlayPauseToggle,
  onStop,
  progress,
  logs = [],
  logFilter,
  onLogsExport,
  onLogsClear,
  statusFilter,
  onStatusFilterChange,
  className = '',
  compact = false,
}) => {
  const [showAbortDialog, setShowAbortDialog] = useState(false);
  const [followLogs, setFollowLogs] = useState(true);
  const [localLogFilter, setLocalLogFilter] = useState<LogLevel[]>(
    logFilter || ['info', 'warn', 'error', 'critical']
  );

  // Format duration from seconds
  const formatDuration = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs.toString().padStart(2, '0')}s`;
  }, []);

  // Get filtered missions
  const filteredMissions = useMemo(() => {
    if (!statusFilter || statusFilter.length === 0) return missions;
    return missions.filter((m) => statusFilter.includes(m.status));
  }, [missions, statusFilter]);

  // Handle abort with confirmation
  const handleAbort = useCallback(async () => {
    if (!activeMission?.id) return;
    setShowAbortDialog(true);
  }, [activeMission]);

  const confirmAbort = useCallback(async () => {
    if (!activeMission?.id) return;
    try {
      await onAbortMission(activeMission.id);
    } finally {
      setShowAbortDialog(false);
    }
  }, [activeMission, onAbortMission]);

  // Control button states based on mission status
  const controlStates = useMemo(() => {
    if (!activeMission) {
      return {
        play: { disabled: false, label: 'Play' },
        pause: { disabled: true, label: 'Pause' },
        stop: { disabled: true, label: 'Stop' },
        abort: { disabled: true, label: 'Abort' },
      };
    }

    switch (activeMission.status) {
      case 'running':
        return {
          play: { disabled: true, label: 'Play' },
          pause: { disabled: false, label: 'Pause' },
          stop: { disabled: false, label: 'Stop' },
          abort: { disabled: false, label: 'Abort' },
        };
      case 'paused':
        return {
          play: { disabled: false, label: 'Resume' },
          pause: { disabled: true, label: 'Pause' },
          stop: { disabled: false, label: 'Stop' },
          abort: { disabled: false, label: 'Abort' },
        };
      case 'completed':
      case 'aborted':
      case 'failed':
        return {
          play: { disabled: true, label: 'Play' },
          pause: { disabled: true, label: 'Pause' },
          stop: { disabled: true, label: 'Stop' },
          abort: { disabled: true, label: 'Abort' },
        };
      default:
        return {
          play: { disabled: false, label: 'Play' },
          pause: { disabled: true, label: 'Pause' },
          stop: { disabled: true, label: 'Stop' },
          abort: { disabled: false, label: 'Abort' },
        };
    }
  }, [activeMission]);

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
        aria-label="Mission control"
      >
        {/* Active Mission Summary */}
        {activeMission ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
                  {activeMission.name}
                </h3>
                <p className="text-xs text-[var(--color-text-tertiary)]">
                  {activeMission.type}
                </p>
              </div>
              <StatusBadge status={activeMission.status}>
                {activeMission.status}
              </StatusBadge>
            </div>

            <MissionProgress
              percentage={progress.percentage}
              currentWaypoint={progress.currentWaypoint}
              totalWaypoints={progress.totalWaypoints}
              elapsed={formatDuration(progress.elapsedSeconds)}
              remaining={
                progress.estimatedRemainingSeconds
                  ? formatDuration(progress.estimatedRemainingSeconds)
                  : undefined
              }
            />

            {/* Mini Controls */}
            <div className="flex items-center justify-center gap-2">
              <Button
                variant={isPlaying ? 'primary' : 'outline'}
                size="sm"
                onClick={onPlayPauseToggle}
                disabled={controlStates.play.disabled && controlStates.pause.disabled}
              >
                <Icon size="sm">
                  {isPlaying ? (
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <rect x="6" y="4" width="4" height="16" strokeWidth="2" />
                      <rect x="14" y="4" width="4" height="16" strokeWidth="2" />
                    </svg>
                  ) : (
                    <svg fill="currentColor" viewBox="0 0 24 24">
                      <polygon points="5,3 19,12 5,21" />
                    </svg>
                  )}
                </Icon>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleAbort}
                disabled={controlStates.abort.disabled}
              >
                <Icon size="sm" color="danger">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" strokeWidth="2" />
                    <line x1="15" y1="9" x2="9" y2="15" strokeWidth="2" />
                    <line x1="9" y1="9" x2="15" y2="15" strokeWidth="2" />
                  </svg>
                </Icon>
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <Icon size="lg" color="tertiary">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0121 18.382V7.618a1 1 0 01-.806-.982l-3.747-.894M9 7v10" strokeWidth="2" />
              </svg>
            </Icon>
            <p className="text-sm text-[var(--color-text-secondary)] mt-2">
              No active mission
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={onCreateMission}
              className="mt-2"
            >
              Create Mission
            </Button>
          </div>
        )}
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
      aria-label="Mission control"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Mission Control
        </h2>
        <Button
          variant="primary"
          size="sm"
          onClick={onCreateMission}
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <line x1="12" y1="5" x2="12" y2="19" strokeWidth="2" />
              <line x1="5" y1="12" x2="19" y2="12" strokeWidth="2" />
            </svg>
          }
        >
          New Mission
        </Button>
      </div>

      {/* Active Mission Card */}
      {activeMission && (
        <div className="bg-[var(--color-surface-tertiary)] rounded-[var(--radius-lg)] p-4 border border-[var(--color-border)]">
          {/* Mission Header with Controls */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--color-primary-subtle)] flex items-center justify-center">
                <Icon size="md" color="primary">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z" strokeWidth="2" />
                  </svg>
                </Icon>
              </div>
              <div>
                <h3 className="text-base font-semibold text-[var(--color-text-primary)]">
                  {activeMission.name}
                </h3>
                <p className="text-sm text-[var(--color-text-tertiary)]">
                  {activeMission.type} • Robot: {robotId}
                </p>
              </div>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center gap-2">
              <Button
                variant={isPlaying ? 'primary' : 'outline'}
                size="md"
                onClick={onPlayPauseToggle}
                disabled={controlStates.play.disabled && controlStates.pause.disabled}
                title={isPlaying ? 'Pause' : 'Play'}
              >
                <Icon>
                  {isPlaying ? (
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <rect x="6" y="4" width="4" height="16" strokeWidth="2" />
                      <rect x="14" y="4" width="4" height="16" strokeWidth="2" />
                    </svg>
                  ) : (
                    <svg fill="currentColor" viewBox="0 0 24 24">
                      <polygon points="5,3 19,12 5,21" />
                    </svg>
                  )}
                </Icon>
              </Button>
              <Button
                variant="outline"
                size="md"
                onClick={onStop}
                disabled={controlStates.stop.disabled}
                title="Stop"
              >
                <Icon>
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <rect x="4" y="4" width="16" height="16" strokeWidth="2" />
                  </svg>
                </Icon>
              </Button>
              <Button
                variant="danger"
                size="md"
                onClick={handleAbort}
                disabled={controlStates.abort.disabled}
                title="Abort"
              >
                <Icon>
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" strokeWidth="2" />
                    <line x1="15" y1="9" x2="9" y2="15" strokeWidth="2" />
                    <line x1="9" y1="9" x2="15" y2="15" strokeWidth="2" />
                  </svg>
                </Icon>
              </Button>
            </div>
          </div>

          {/* Progress */}
          <MissionProgress
            percentage={progress.percentage}
            currentWaypoint={progress.currentWaypoint}
            totalWaypoints={progress.totalWaypoints}
            elapsed={formatDuration(progress.elapsedSeconds)}
            remaining={
              progress.estimatedRemainingSeconds
                ? formatDuration(progress.estimatedRemainingSeconds)
                : undefined
            }
          />
        </div>
      )}

      {/* Recent Missions List */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
            Recent Missions
          </h3>
          {/* Status Filter */}
          {onStatusFilterChange && (
            <div className="flex items-center gap-1">
              {(['pending', 'running', 'completed', 'failed'] as const).map(
                (status) => (
                  <button
                    key={status}
                    className={`
                      px-2 py-1 text-xs rounded-[var(--radius-sm)] capitalize
                      transition-colors
                      ${!statusFilter || statusFilter.includes(status)
                        ? 'bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]'
                        : 'bg-[var(--color-surface)] text-[var(--color-text-tertiary)] opacity-50'
                      }
                    `}
                    onClick={() => {
                      const newFilter = statusFilter?.includes(status)
                        ? statusFilter.filter((s) => s !== status)
                        : [...(statusFilter || []), status];
                      onStatusFilterChange(newFilter.length === 0 ? [] : newFilter);
                    }}
                  >
                    {status}
                  </button>
                )
              )}
            </div>
          )}
        </div>

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {filteredMissions.slice(0, 5).map((mission) => (
            <MissionListItem
              key={mission.id}
              mission={mission}
              isSelected={activeMission?.id === mission.id}
              onSelect={() => {
                // Navigate to mission details or select for action
              }}
              onQuickAction={(action) => {
                switch (action) {
                  case 'pause':
                    onPauseMission(mission.id);
                    break;
                  case 'resume':
                    onResumeMission(mission.id);
                    break;
                }
              }}
            />
          ))}
        </div>
      </div>

      {/* Mission Logs Terminal */}
      <div className="h-64">
        <MissionLogsTerminal
          logs={logs}
          filter={localLogFilter}
          onFilterChange={setLocalLogFilter}
          onExport={onLogsExport}
          onClear={onLogsClear}
          followMode={followLogs}
          onFollowToggle={() => setFollowLogs(!followLogs)}
        />
      </div>

      {/* Emergency Stop Dialog */}
      <EmergencyStopDialog
        open={showAbortDialog}
        onConfirm={confirmAbort}
        onCancel={() => setShowAbortDialog(false)}
      />
    </div>
  );
};

export default MissionControl;
