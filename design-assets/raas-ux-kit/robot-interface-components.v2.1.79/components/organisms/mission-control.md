# Mission Control

**Version:** 2.1.79 | **Type:** Organism | **Status:** Production Ready

---

## Overview

Mission management interface for creating, launching, monitoring, and controlling robot missions. Includes mission list, playback controls, progress tracking, and real-time mission logs terminal.

---

## Anatomy

```
┌─────────────────────────────────────────────────────────────────────┐
│  MISSION CONTROL                              [+ New Mission]        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 🚀 MISSION-2024-003                    [▶] [⏸] [⏹] [⚠️ ABORT]  ││
│  │    Warehouse Patrol Zone A                                      ││
│  │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  67%       ││
│  │    ⏱️ 2h 15m elapsed  |  📍 45/67 waypoints  |  ⚡ 78% battery  ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  RECENT MISSIONS                                          [Filter ▼]│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ✅ MISSION-002  │  Inventory Scan  │  1h 30m  │  Completed     ││
│  │ ⏸️ MISSION-001  │  Dock Charging   │  Paused    │  23% battery  ││
│  │ ⏹️ MISSION-000  │  Perimeter Check │  45m       │  Aborted     ││
│  └─────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────┤
│  MISSION LOGS                                        [Clear] [⬇️]   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ [10:45:23] [INFO] Mission started                              ││
│  │ [10:45:24] [INFO] Navigating to waypoint WP-001                ││
│  │ [10:47:12] [INFO] Waypoint WP-001 reached                      ││
│  │ [10:47:15] [WARN] Obstacle detected, rerouting                 ││
│  │ [10:48:01] [INFO] New path calculated, resuming                ││
│  │ [10:52:33] [INFO] Waypoint WP-002 reached                      ││
│  │ [10:52:34] [INFO] Executing action: scan_inventory             ││
│  │ > _                                                           ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Props Interface

```typescript
interface MissionControlProps {
  // Data Source
  robotId: string;
  missions: Mission[];
  activeMission?: Mission;

  // Mission Actions
  onCreateMission: () => void;
  onLaunchMission: (missionId: string) => Promise<void>;
  onPauseMission: (missionId: string) => Promise<void>;
  onResumeMission: (missionId: string) => Promise<void>;
  onAbortMission: (missionId: string) => Promise<void>;

  // Playback Controls
  isPlaying: boolean;
  isPaused: boolean;
  onPlayPauseToggle: () => void;
  onStop: () => void;

  // Progress
  progress: {
    percentage: number;
    currentWaypoint: number;
    totalWaypoints: number;
    elapsedSeconds: number;
    estimatedRemainingSeconds?: number;
  };

  // Logs
  logs: MissionLog[];
  logFilter?: LogLevel[];
  onLogsExport?: (format: 'txt' | 'json') => void;
  onLogsClear: () => void;

  // Filtering
  statusFilter?: MissionStatus[];
  onStatusFilterChange?: (statuses: MissionStatus[]) => void;

  // Styling
  className?: string;
  compact?: boolean;
}

interface Mission {
  id: string;
  name: string;
  type: MissionType;
  status: MissionStatus;
  priority: 'low' | 'normal' | 'high' | 'critical';
  createdAt: Date;
  scheduledAt?: Date;
  startedAt?: Date;
  completedAt?: Date;
  waypoints: Waypoint[];
  actions: MissionAction[];
  batteryRequirement?: number;
  estimatedDuration?: number;
}

interface MissionLog {
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error' | 'critical';
  message: string;
  source?: string;
  data?: Record<string, unknown>;
}
```

---

## Mission Playback Controls

### Control Layout

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   [◀◀ Rewind]  [▶ Play]  [⏸ Pause]  [⏹ Stop]  [⏩ FF]  │
│                                                         │
│   ━━━━━━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━  2:15 / 5:30  │
│                                                         │
│   [↺ Retry from Start]  [↻ Retry from Current]         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Control States

| State | Play | Pause | Stop | Abort |
|-------|------|-------|------|-------|
| Idle | Enabled | Disabled | Disabled | Disabled |
| Running | Disabled | Enabled | Enabled | Enabled |
| Paused | Enabled | Disabled | Enabled | Enabled |
| Completed | Disabled | Disabled | Disabled | Disabled |
| Failed | Enabled (retry) | Disabled | Enabled | Disabled |

### Control Handlers

```typescript
// Optimistic UI for user-initiated controls
const handlePlayPause = async () => {
  const newAction = isPlaying ? 'pause' : 'resume';
  const missionId = activeMission.id;

  // 1. Immediately update button state
  setIsPlaying(!isPlaying);

  try {
    // 2. Send command
    await api.missionControl(missionId, newAction);

    // 3. Server response updates actual state
    setMissionState(serverState);
  } catch (error) {
    // 4. Rollback on failure
    setIsPlaying(isPlaying); // revert
    toast.error(`${newAction} failed: ${error.message}`);

    // 5. Refresh state from server
    await refreshMissionState(missionId);
  }
};

// Pessimistic for destructive actions
const handleAbort = async () => {
  // 1. Require confirmation
  const confirmed = await confirmAction({
    title: 'Abort Mission?',
    message: 'This will immediately stop the mission and return robot to base.',
    variant: 'danger',
    confirmText: 'Yes, Abort',
  });

  if (!confirmed) return;

  // 2. Show loading state (no optimistic update)
  setIsAborting(true);

  try {
    // 3. Wait for server confirmation
    await api.abortMission(activeMission.id);

    // 4. Update state after server confirms
    setMissionState('aborted');
    toast.warning('Mission aborted');
  } finally {
    setIsAborting(false);
  }
};
```

---

## Progress Tracking

### Progress Bar Component

```tsx
<MissionProgress
  percentage={progress.percentage}
  currentWaypoint={progress.currentWaypoint}
  totalWaypoints={progress.totalWaypoints}
  elapsed={formatDuration(progress.elapsedSeconds)}
  remaining={progress.estimatedRemainingSeconds
    ? formatDuration(progress.estimatedRemainingSeconds)
    : 'Calculating...'}
  segments={waypoints.map(wp => ({
    id: wp.id,
    status: wp.status, // 'pending' | 'active' | 'completed' | 'skipped'
    label: wp.name,
  }))}
  showWaypointLabels={true}
/>
```

### Progress States

```typescript
const ProgressSegment = ({ status }: { status: WaypointStatus }) => {
  const variants = {
    pending: 'bg-gray-200',
    active: 'bg-blue-500 animate-pulse',
    completed: 'bg-green-500',
    skipped: 'bg-gray-100 pattern-diagonal',
    failed: 'bg-red-500',
  };

  return <div className={`h-2 ${variants[status]}`} />;
};
```

### Time Estimation

```typescript
// Calculate ETA based on historical performance
const calculateETA = (mission: Mission): number | undefined => {
  const completed = mission.waypoints.filter(wp => wp.status === 'completed');
  const remaining = mission.waypoints.filter(wp => wp.status === 'pending');

  if (completed.length === 0 || remaining.length === 0) return undefined;

  // Average time per waypoint
  const avgTimePerWaypoint =
    mission.elapsedSeconds / completed.length;

  // Adjust for remaining distance (if available)
  const adjustedTime = remaining.length * avgTimePerWaypoint;

  return Math.round(adjustedTime);
};
```

---

## Mission Logs Terminal

### Terminal Component

```tsx
<MissionLogsTerminal
  logs={logs}
  filter={logFilter}
  onFilterChange={setLogFilter}
  onExport={handleLogsExport}
  onClear={handleLogsClear}
  autoScroll={true}
  followMode={followLogs}
  maxLines={1000}
  syntaxHighlighting={true}
/>
```

### Log Level Styling

```scss
.log-entry {
  display: flex;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;

  .timestamp {
    color: $gray-500;
    flex-shrink: 0;
  }

  .level {
    flex-shrink: 0;
    font-weight: 600;
    padding: 0 0.5rem;
    border-radius: 2px;
  }

  &.debug .level { background: $gray-100; color: $gray-600; }
  &.info  .level { background: $blue-100; color: $blue-600; }
  &.warn  .level { background: $amber-100; color: $amber-600; }
  &.error .level { background: $red-100; color: $red-600; }
  &.critical .level {
    background: $red-600;
    color: white;
    animation: flash-warning 1s infinite;
  }

  .message {
    flex-grow: 1;
    color: $gray-800;
  }
}
```

### Terminal Toolbar

```tsx
<TerminalToolbar>
  <LogFilter
    levels={['debug', 'info', 'warn', 'error', 'critical']}
    selected={logFilter}
    onChange={setLogFilter}
  />

  <div className="actions">
    <Toggle
      label="Follow"
      icon={<ScrollIcon />}
      checked={followLogs}
      onChange={setFollowLogs}
    />

    <Button
      variant="ghost"
      icon={<DownloadIcon />}
      onClick={() => handleLogsExport('txt')}
      tooltip="Export logs"
    />

    <Button
      variant="ghost"
      icon={<TrashIcon />}
      onClick={handleLogsClear}
      tooltip="Clear logs"
    />
  </div>
</TerminalToolbar>
```

---

## Real-Time Data Handling

### Mission State Sync

```typescript
// WebSocket connection for real-time mission updates
useMissionWebSocket(activeMissionId, {
  onMessage: (message: MissionUpdate) => {
    switch (message.type) {
      case 'waypoint_reached':
        // Optimistic: Update progress immediately
        setProgress(prev => ({
          ...prev,
          currentWaypoint: message.waypointIndex,
          percentage: calculateNewPercentage(message.waypointIndex),
        }));
        break;

      case 'action_started':
      case 'action_completed':
        // Add log entry optimistically
        addLog({
          level: 'info',
          message: formatActionMessage(message),
          timestamp: new Date(),
        });
        break;

      case 'state_change':
        // Pessimistic: Wait for server state
        syncMissionState(message.missionId);
        break;
    }
  },

  onDisconnect: () => {
    // Show disconnected state, continue with cached updates
    setConnectionStatus('reconnecting');
  },
});
```

### Optimistic vs Pessimistic Decision Tree

```
User Action          │ Strategy    │ Reason
─────────────────────┼─────────────┼─────────────────────────────
Launch Mission       │ Pessimistic │ Irreversible, resource alloc
Pause Mission        │ Optimistic  │ Reversible, immediate feedback
Resume Mission       │ Optimistic  │ Reversible, immediate feedback
Stop Mission         │ Pessimistic │ Irreversible, state change
Abort Mission        │ Pessimistic │ Safety-critical, confirmation
Change Priority      │ Optimistic  │ Metadata only, no side effects
Add Waypoint (live)  │ Optimistic  │ Append to queue, sync later
Remove Waypoint      │ Pessimistic │ May affect active navigation
```

---

## Offline State Management

### Offline Behavior

```typescript
const OfflineMissionControl = () => {
  const { isOffline, queuedActions, lastSync } = useMissionContext();

  return (
    <Panel>
      {isOffline && (
        <OfflineBanner>
          <WifiOffIcon />
          <span>
            Offline since {formatDistance(lastSync)}.
            Actions will queue for sync.
          </span>
        </OfflineBanner>
      )}

      {/* Disable actions that require server */}
      <ControlBar>
        <PlayButton
          disabled={isOffline}
          tooltip={isOffline ? 'Cannot launch while offline' : undefined}
        />

        {/* Pause/Resume can work optimistically if mission already running */}
        <PauseButton
          disabled={isOffline && !activeMission}
          onClick={handlePauseOptimistic}
        />

        {/* Abort always requires connection */}
        <AbortButton disabled={isOffline} />
      </ControlBar>

      {/* Show queued actions */}
      {queuedActions.length > 0 && (
        <QueuedActionsList actions={queuedActions} />
      )}

      {/* Logs continue from cache */}
      <MissionLogsTerminal
        logs={cachedLogs}
        autoScroll={false}
        showOfflineNotice={true}
      />
    </Panel>
  );
};
```

### Action Queue

```typescript
interface QueuedAction {
  id: string;
  type: 'launch' | 'pause' | 'resume' | 'abort' | 'add_waypoint';
  missionId: string;
  payload?: unknown;
  queuedAt: Date;
  status: 'pending' | 'syncing' | 'completed' | 'failed';
  retryCount: number;
}

// Sync queue when connection restored
useEffect(() => {
  if (connectionStatus === 'online' && queuedActions.length > 0) {
    processQueue();
  }
}, [connectionStatus]);
```

---

## Emergency Stop Integration

### Placement & Priority

```
┌─────────────────────────────────────────────────────────┐
│  MISSION CONTROL                   [🔴 E-STOP]  [+ New] │
│                                                         │
│  ← E-STOP always top-right, visible from all screens   │
└─────────────────────────────────────────────────────────┘
```

### Styling

```scss
.emergency-stop {
  // Fixed position, always accessible
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;

  // Visual weight
  min-width: 120px;
  height: 48px;
  padding: 0 1.5rem;

  background: $red-600;
  color: white;
  font-weight: 700;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  border: 3px solid $red-800;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.5);

  // Pulse animation when mission is active
  &[data-mission-active="true"] {
    animation: pulse-emergency 2s infinite;
  }

  &:hover {
    background: $red-700;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(220, 38, 38, 0.6);
  }

  &:active {
    transform: translateY(1px);
  }
}

@keyframes pulse-emergency {
  0%, 100% { box-shadow: 0 4px 12px rgba(220, 38, 38, 0.5); }
  50% { box-shadow: 0 4px 24px rgba(220, 38, 38, 0.8); }
}
```

### Confirmation Dialog

```tsx
const EmergencyStopDialog = ({ open, onConfirm, onCancel }) => (
  <Dialog open={open} variant="danger" size="sm">
    <DialogHeader>
      <AlertTriangleIcon className="text-red-600 w-12 h-12" />
      <DialogTitle>Emergency Stop</DialogTitle>
    </DialogHeader>

    <DialogContent>
      <p className="text-lg font-semibold">
        This will immediately halt all robot operations.
      </p>
      <ul className="list-disc pl-4 mt-2 space-y-1">
        <li>Mission will be aborted</li>
        <li>Robot will engage brakes</li>
        <li>Systems will enter safe mode</li>
        <li>Manual restart required</li>
      </ul>
    </DialogContent>

    <DialogFooter>
      <Button variant="ghost" onClick={onCancel}>
        Cancel
      </Button>
      <Button
        variant="danger"
        onClick={onConfirm}
        className="min-w-[140px]"
      >
        🛑 CONFIRM STOP
      </Button>
    </DialogFooter>
  </Dialog>
);
```

---

## Mission List

### List Item

```tsx
<MissionListItem
  mission={mission}
  onSelect={() => navigate(`/missions/${mission.id}`)}
  onQuickAction={(action) => handleQuickAction(mission.id, action)}
  actions={['launch', 'pause', 'resume', 'abort', 'duplicate', 'delete']}
/>
```

### Status Badges

```typescript
const statusConfig = {
  pending: { label: 'Scheduled', color: 'gray' },
  queued: { label: 'Queued', color: 'blue' },
  running: { label: 'In Progress', color: 'green', animated: true },
  paused: { label: 'Paused', color: 'amber' },
  completed: { label: 'Completed', color: 'green' },
  aborted: { label: 'Aborted', color: 'red' },
  failed: { label: 'Failed', color: 'red' },
};
```

---

## Usage Examples

### Full Mission Control

```tsx
<MissionControl
  robotId="ROB-001"
  missions={missions}
  activeMission={activeMission}
  onCreateMission={() => setCreateDialogOpen(true)}
  onLaunchMission={handleLaunch}
  onPauseMission={handlePause}
  onResumeMission={handleResume}
  onAbortMission={handleAbort}
  isPlaying={activeMission?.status === 'running'}
  isPaused={activeMission?.status === 'paused'}
  onPlayPauseToggle={handlePlayPause}
  onStop={handleStop}
  progress={missionProgress}
  logs={missionLogs}
  logFilter={['info', 'warn', 'error']}
  onLogsExport={handleLogsExport}
  onLogsClear={handleLogsClear}
/>
```

### Compact Widget (Dashboard)

```tsx
<MissionControl
  robotId="ROB-001"
  missions={recentMissions}
  compact
  onCreateMission={handleCreate}
  onLaunchMission={handleLaunch}
  progress={missionProgress}
  logs={last10Logs}
/>
```

---

## Related Components

- **Robot Status Panel** - Robot health during mission
- **Telemetry Dashboard** - Mission telemetry visualization
- **Fleet Overview** - Multi-robot mission coordination

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial organism documentation |
| 2.1.78 | 2026-03-15 | Added action queue for offline |
| 2.1.77 | 2026-03-10 | Enhanced logs terminal with filtering |
