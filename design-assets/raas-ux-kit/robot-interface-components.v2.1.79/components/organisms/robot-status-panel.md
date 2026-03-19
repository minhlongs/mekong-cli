# Robot Status Panel

**Version:** 2.1.79 | **Type:** Organism | **Status:** Production Ready

---

## Overview

Multi-metric health dashboard providing real-time visibility into robot operational status. Combines battery, signal strength, temperature, and mode indicators with connection state awareness.

---

## Anatomy

```
┌─────────────────────────────────────────────────────────┐
│  [○] ROBOT-001                              [Online ●]  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Battery │ │ Signal  │ │  Temp   │ │  Mode   │       │
│  │  ▓▓▓▓░  │ │   ▓▓▓░  │ │  42°C   │ │ AUTO    │       │
│  │   78%   │ │  -67dBm │ │  Normal │ │ Active  │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Components

| Element | Type | Purpose |
|---------|------|---------|
| Robot ID | Header | Unique identifier + quick actions menu |
| Connection Badge | Status | Online/Offline/Reconnecting/Unknown |
| Battery Gauge | Metric | Charge level + charging state |
| Signal Meter | Metric | WiFi/cellular strength |
| Temperature | Metric | Core temperature + thermal state |
| Mode Badge | Status | Current operation mode |

---

## Props Interface

```typescript
interface RobotStatusPanelProps {
  // Identity
  robotId: string;
  robotName?: string;

  // Metrics
  battery: {
    level: number;        // 0-100
    charging: boolean;
    health: 'good' | 'fair' | 'poor';
    estimatedRuntime?: number; // minutes
  };

  signal: {
    strength: number;     // -100 to -30 dBm
    type: 'wifi' | 'cellular' | 'ethernet';
    quality: 'excellent' | 'good' | 'fair' | 'poor';
  };

  temperature: {
    current: number;      // Celsius
    max: number;
    state: 'cold' | 'normal' | 'warm' | 'hot' | 'critical';
  };

  mode: {
    current: 'manual' | 'auto' | 'charging' | 'sleep' | 'error';
    subMode?: string;
    activeSince: Date;
  };

  // Connection
  connectionState: 'online' | 'offline' | 'reconnecting' | 'unknown';
  lastSeen?: Date;

  // Behavior
  refreshInterval?: number;  // ms (default: 2000)
  onExpand?: () => void;
  onQuickAction?: (action: string) => void;

  // Styling
  className?: string;
  compact?: boolean;
}
```

---

## Real-Time Data Handling

### Polling Strategy

```typescript
// Default: Aggressive polling for critical metrics
const REFRESH_RATES = {
  battery: 5000,        // 5s - slow changing
  signal: 2000,         // 2s - moderate changes
  temperature: 3000,    // 3s - safety critical
  mode: 1000,           // 1s - user interaction
  connection: 500,      // 500ms - immediate awareness
};
```

### Optimistic UI Updates

```typescript
// ✅ OPTIMISTIC: Mode changes (user-initiated)
const handleModeChange = async (newMode: RobotMode) => {
  // 1. Immediately update UI
  setMode(newMode);

  // 2. Send to server
  try {
    await api.updateMode(robotId, newMode);
    // 3. Sync with actual server response
    setMode(serverResponse.mode);
  } catch (error) {
    // 4. Rollback on failure
    setMode(previousMode);
    toast.error('Mode change failed');
  }
};

// ⚠️ PESSIMISTIC: Safety-critical metrics
const handleTemperatureUpdate = (data: TelemetryData) => {
  // Never guess with temperature - wait for server truth
  if (data.temperature.state === 'critical') {
    triggerEmergencyProtocol();
  }
  setTemperature(data.temperature);
};
```

---

## Connection State Management

### States & Transitions

```
┌──────────┐    timeout    ┌──────────────┐    success   ┌─────────┐
│  Online  │ ────────────► │ Reconnecting │ ────────────► │ Online  │
└────┬─────┘               └──────┬───────┘              └─────────┘
     │ disconnect                 │ timeout/fail
     ▼                            ▼
┌──────────┐               ┌─────────────┐
│  Offline │ ◄─────────────│  Unknown    │
└──────────┘    no heartbt └─────────────┘
```

### Visual Indicators

| State | Color | Animation | Badge Text |
|-------|-------|-----------|------------|
| Online | Green (#22c55e) | None | `● Online` |
| Reconnecting | Amber (#f59e0b) | Pulse | `◍ Reconnecting...` |
| Offline | Red (#ef4444) | None | `○ Offline` |
| Unknown | Gray (#6b7280) | None | `? Unknown` |

### Offline State Behavior

```typescript
// When connection lost:
const OfflineState = () => {
  const { lastSeen, lastKnownState } = useRobotContext();

  return (
    <Panel faded opacity={0.6}>
      {/* Show last known values, clearly marked stale */}
      <StaleBanner lastSeen={lastSeen} />

      {/* Disable interactive elements */}
      <Button disabled>Change Mode</Button>

      {/* Auto-retry connection */}
      <ReconnectButton interval={5000} maxAttempts={5} />
    </Panel>
  );
};
```

---

## Emergency Stop Integration

### Placement Priority

```
┌─────────────────────────────────────────────────────────┐
│  [○] ROBOT-001                    [🔴 STOP] [Online ●]  │  ← STOP top-right
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ Metrics │ │ Metrics │ │ Metrics │ │ Metrics │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Styling Rules

```scss
.emergency-stop {
  // Always visible, never hidden
  position: absolute;
  top: 1rem;
  right: 6rem; // Left of connection badge
  z-index: 100;

  // High contrast
  background: $red-600;
  color: white;
  border: 2px solid $red-800;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);

  // Hover: intensify
  &:hover {
    background: $red-700;
    transform: scale(1.05);
  }

  // Active: pressed state
  &:active {
    transform: scale(0.95);
  }

  // Disabled ONLY during active emergency
  &[data-active="true"] {
    animation: pulse-danger 1s infinite;
    cursor: not-allowed;
  }
}
```

### Confirmation Flow

```typescript
const handleEmergencyStop = () => {
  // 1. Show confirmation (prevent accidental clicks)
  const confirmed = window.confirm(
    '⚠️ EMERGENCY STOP\n\nThis will immediately halt all robot operations.\n\nAre you sure?'
  );

  if (!confirmed) return;

  // 2. Optimistic UI: show stopping state
  setConnectionState('reconnecting');

  // 3. Send emergency command (high priority)
  api.emergencyStop(robotId, {
    priority: 'critical',
    timeout: 2000, // 2s max
    retry: 3,
  });

  // 4. Update status
  setMode('error');
  toast.warning(`🛑 ${robotId} emergency stopped`);
};
```

---

## Accessibility

```typescript
// ARIA labels for screen readers
<div role="region" aria-label={`Robot status: ${robotName}`}>
  <div role="status" aria-live="polite" aria-atomic="true">
    {connectionState === 'online' ? 'Connected' : 'Disconnected'}
  </div>

  <div role="img" aria-label={`Battery: ${battery.level}%`}>
    {/* Visual gauge */}
  </div>

  <button
    aria-label="Emergency stop"
    aria-describedby="stop-warning"
    id="stop-warning"
  >
    STOP
  </button>
</div>
```

---

## Usage Examples

### Basic

```tsx
<RobotStatusPanel
  robotId="ROB-001"
  robotName="Warehouse Alpha"
  battery={{ level: 78, charging: false, health: 'good' }}
  signal={{ strength: -67, type: 'wifi', quality: 'good' }}
  temperature={{ current: 42, max: 60, state: 'normal' }}
  mode={{ current: 'auto', subMode: 'patrol', activeSince: new Date() }}
  connectionState="online"
/>
```

### With Custom Actions

```tsx
<RobotStatusPanel
  robotId="ROB-001"
  onExpand={() => navigate(`/robots/ROB-001`)}
  onQuickAction={(action) => {
    switch (action) {
      case 'reboot': handleReboot(); break;
      case 'diagnose': runDiagnostics(); break;
      case 'locate': activateLocator(); break;
    }
  }}
/>
```

### Compact Mode (Dashboard Grid)

```tsx
<RobotStatusPanel
  robotId="ROB-001"
  compact
  battery={{ level: 78, charging: false, health: 'good' }}
  // ... other props
/>
```

---

## Related Components

- **Fleet Overview** - Multi-robot aggregation
- **Telemetry Dashboard** - Detailed metric visualization
- **Mission Control** - Active mission management

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial organism documentation |
| 2.1.78 | 2026-03-15 | Added emergency stop confirmation flow |
| 2.1.77 | 2026-03-10 | Optimistic UI for mode changes |
