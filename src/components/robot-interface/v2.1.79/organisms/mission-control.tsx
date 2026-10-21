/**
 * MissionControl Component - RaaS UX Kit v2.1.79
 * Mission management interface with playback controls, progress tracking, and logs terminal
 */
import React, { useState, useCallback, useMemo } from 'react';
import { Button } from '../atoms/Button';
import { Icon } from '../atoms/Icon';
import { StatusBadge } from '../atoms/StatusBadge';
import { MissionControlProps, LogLevel } from '../types/mission';
import { MissionProgress, MissionListItem, MissionLogsTerminal, EmergencyStopDialog } from './mission-control-parts';

export const MissionControl: React.FC<MissionControlProps> = ({
  robotId, missions = [], activeMission, onCreateMission, onPauseMission, onResumeMission, onAbortMission,
  isPlaying, onPlayPauseToggle, onStop, progress, logs = [], logFilter, onLogsExport, onLogsClear,
  statusFilter, onStatusFilterChange, className = '', compact = false,
}) => {
  const [showAbortDialog, setShowAbortDialog] = useState(false);
  const [followLogs, setFollowLogs] = useState(true);
  const [localLogFilter, setLocalLogFilter] = useState<LogLevel[]>(logFilter || ['info', 'warn', 'error', 'critical']);

  const formatDuration = useCallback((seconds: number): string => `${Math.floor(seconds / 60)}m ${(seconds % 60).toString().padStart(2, '0')}s`, []);
  const filteredMissions = useMemo(
    () => (!statusFilter || statusFilter.length === 0 ? missions : missions.filter((m) => statusFilter.includes(m.status))),
    [missions, statusFilter]
  );

  const handleAbort = useCallback(async () => { if (activeMission?.id) setShowAbortDialog(true); }, [activeMission]);
  const confirmAbort = useCallback(async () => {
    if (!activeMission?.id) return;
    try { await onAbortMission(activeMission.id); } finally { setShowAbortDialog(false); }
  }, [activeMission, onAbortMission]);

  const controlStates = useMemo(() => {
    if (!activeMission) return { play: false, pause: true, stop: true, abort: true };
    if (activeMission.status === 'running') return { play: true, pause: false, stop: false, abort: false };
    if (activeMission.status === 'paused') return { play: false, pause: true, stop: false, abort: false };
    if (['completed', 'aborted', 'failed'].includes(activeMission.status)) return { play: true, pause: true, stop: true, abort: true };
    return { play: false, pause: true, stop: true, abort: false };
  }, [activeMission]);

  const progressProps = {
    percentage: progress.percentage, currentWaypoint: progress.currentWaypoint, totalWaypoints: progress.totalWaypoints,
    elapsed: formatDuration(progress.elapsedSeconds),
    remaining: progress.estimatedRemainingSeconds ? formatDuration(progress.estimatedRemainingSeconds) : undefined,
  };

  if (compact) {
    return (
      <div className={`flex flex-col gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 ${className}`} role="region" aria-label="Mission control">
        {activeMission ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{activeMission.name}</h3>
                <p className="text-xs text-[var(--color-text-tertiary)]">{activeMission.type}</p>
              </div>
              <StatusBadge variant={activeMission.status === 'running' ? 'online' : 'warning'} size="sm">{activeMission.status}</StatusBadge>
            </div>
            <MissionProgress {...progressProps} />
            <div className="flex items-center justify-center gap-2">
              <Button variant={isPlaying ? 'primary' : 'outline'} size="sm" onClick={onPlayPauseToggle} disabled={controlStates.play && controlStates.pause}>
                {isPlaying ? 'Pause' : 'Play'}
              </Button>
              <Button variant="outline" size="sm" onClick={handleAbort} disabled={controlStates.abort}>Abort</Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-[var(--color-text-secondary)]">No active mission</p>
            <Button variant="primary" size="sm" onClick={onCreateMission} className="mt-2">Create Mission</Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 ${className}`} role="region" aria-label="Mission control">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Mission Control</h2>
        <Button variant="primary" size="sm" onClick={onCreateMission}>New Mission</Button>
      </div>

      {activeMission && (
        <div className="bg-[var(--color-surface-tertiary)] rounded-[var(--radius-lg)] p-4 border border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--color-primary-container)] flex items-center justify-center">
                <Icon size="md"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></Icon>
              </div>
              <div>
                <h3 className="text-base font-semibold text-[var(--color-text-primary)]">{activeMission.name}</h3>
                <p className="text-sm text-[var(--color-text-tertiary)]">{activeMission.type} • Robot: {robotId}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant={isPlaying ? 'primary' : 'outline'} size="md" onClick={onPlayPauseToggle} disabled={controlStates.play && controlStates.pause}>
                {isPlaying ? 'Pause' : 'Play'}
              </Button>
              <Button variant="outline" size="md" onClick={onStop} disabled={controlStates.stop}>Stop</Button>
              <Button variant="danger" size="md" onClick={handleAbort} disabled={controlStates.abort}>Abort</Button>
            </div>
          </div>
          <MissionProgress {...progressProps} />
        </div>
      )}

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Recent Missions</h3>
          {onStatusFilterChange && (
            <div className="flex items-center gap-1">
              {(['pending', 'running', 'completed', 'failed'] as const).map((status) => (
                <button
                  key={status} type="button"
                  className={`px-2 py-1 text-xs rounded-[var(--radius-sm)] capitalize transition-colors cursor-pointer ${
                    !statusFilter || statusFilter.includes(status) ? 'bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]' : 'bg-[var(--color-surface)] text-[var(--color-text-tertiary)] opacity-50'
                  }`}
                  onClick={() => {
                    const next = statusFilter?.includes(status) ? statusFilter.filter((s) => s !== status) : [...(statusFilter || []), status];
                    onStatusFilterChange(next.length === 0 ? [] : next);
                  }}
                >
                  {status}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {filteredMissions.slice(0, 5).map((mission) => (
            <MissionListItem
              key={mission.id} mission={mission} isSelected={activeMission?.id === mission.id}
              onQuickAction={(action) => { if (action === 'pause') onPauseMission(mission.id); if (action === 'resume') onResumeMission(mission.id); }}
            />
          ))}
        </div>
      </div>

      <div className="h-64">
        <MissionLogsTerminal
          logs={logs} filter={localLogFilter} onFilterChange={setLocalLogFilter}
          onExport={onLogsExport} onClear={onLogsClear} followMode={followLogs} onFollowToggle={() => setFollowLogs(!followLogs)}
        />
      </div>

      <EmergencyStopDialog open={showAbortDialog} onConfirm={confirmAbort} onCancel={() => setShowAbortDialog(false)} />
    </div>
  );
};

export default MissionControl;
