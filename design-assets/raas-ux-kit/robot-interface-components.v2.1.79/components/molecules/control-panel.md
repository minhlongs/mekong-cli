# Control Panel

**Version:** 2.1.79 | **Type:** Molecule | **Status:** Stable

---

## Overview

Robot action control component that groups operational controls including action buttons, mode selection, speed adjustment, and emergency functions. Primary interface for direct robot interaction.

---

## Anatomy

```
┌─────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────┐    │
│  │  Mode: [● Auto] [○ Manual] [○ Teleop]           │    │  ← Mode Selector
│  └─────────────────────────────────────────────────┘    │
│  ───────────────────────────────────────────────────────  │
│  Speed: [−] ████████░░ [80%] [+]                       │  ← Speed Control
│  ───────────────────────────────────────────────────────  │
│  [▶ Start]  [⏸ Pause]  [⏹ Stop]  [🏠 Home]             │  ← Action Buttons
│  ───────────────────────────────────────────────────────  │
│  [⚠ STOP]  ← Emergency (always visible, prominent)      │  ← Emergency
└─────────────────────────────────────────────────────────┘
```

### Components

| Element | Atom Reference | Description |
|---------|----------------|-------------|
| Mode Toggle | `toggle-group` | Auto/Manual/Teleop selector |
| Speed Slider | `slider` | 0-100% speed control |
| Action Buttons | `button-group` | Primary action cluster |
| Emergency Button | `danger-button` | E-stop override |
| Section Divider | `divider` | Visual separation |

---

## Variants

### Action Buttons Group

Standard operational controls.

```tsx
<ActionButtons
  actions={[
    { id: 'start', label: 'Start', icon: '▶', variant: 'primary' },
    { id: 'pause', label: 'Pause', icon: '⏸', variant: 'default' },
    { id: 'stop', label: 'Stop', icon: '⏹', variant: 'warning' },
    { id: 'home', label: 'Home', icon: '🏠', variant: 'default' },
  ]}
  onAction={handleAction}
  disabled={['start']}  // Disabled action IDs
/>
```

**Visual:**
```
[▶ Start]  [⏸ Pause]  [⏹ Stop]  [🏠 Home]
```

---

### Mode Selector

Robot operation mode switching.

```tsx
<ModeSelector
  mode="auto"
  options={[
    { value: 'auto', label: 'Auto', description: 'Autonomous' },
    { value: 'manual', label: 'Manual', description: 'Manual override' },
    { value: 'teleop', label: 'Teleop', description: 'Remote control' },
  ]}
  onModeChange={handleModeChange}
  locked={false}
/>
```

**Visual:**
```
┌─────────────────────────────────────────┐
│  [● Auto]     [○ Manual]     [○ Teleop] │
│  Autonomous   Manual override  Remote   │
└─────────────────────────────────────────┘
```

---

### Speed Control

Percentage-based speed adjustment.

```tsx
<SpeedControl
  value={80}
  onChange={setSpeed}
  min={0}
  max={100}
  step={5}
  showPercentage={true}
  presets={[25, 50, 75, 100]}
/>
```

**Visual:**
```
Speed: [−] ████████░░ [80%] [+]
       [25%]  [50%]  [75%]  [100%]  ← Presets
```

---

### Emergency Controls

Always-accessible emergency functions.

```tsx
<EmergencyControls
  onEStop={handleEStop}
  onReset={handleReset}
  eStopActive={false}
  confirmReset={true}
/>
```

**Visual:**

**Normal State:**
```
┌─────────────────────────────────────────┐
│           ⚠ EMERGENCY STOP              │  ← Red, prominent
└─────────────────────────────────────────┘
```

**E-Stop Active:**
```
┌─────────────────────────────────────────┐
│    🚨 EMERGENCY ACTIVE - CLICK TO RESET │  ← Flashing red
└─────────────────────────────────────────┘
```

---

## Props

### ControlPanel (Main)

```typescript
interface ControlPanelProps {
  // Mode
  mode: 'auto' | 'manual' | 'teleop';
  onModeChange: (mode: string) => void;
  modeLocked?: boolean;

  // Speed
  speed: number;  // 0-100
  onSpeedChange: (speed: number) => void;
  speedPresets?: number[];

  // Actions
  availableActions: RobotAction[];
  onAction: (action: RobotAction) => void;
  disabledActions?: string[];

  // Emergency
  eStopActive: boolean;
  onEStop: () => void;
  onEStopReset: () => void;

  // State
  robotConnected: boolean;
  robotBusy?: boolean;

  // Styling
  variant?: 'full' | 'compact' | 'minimal';
  orientation?: 'vertical' | 'horizontal';
  className?: string;
}

interface RobotAction {
  id: string;
  label: string;
  icon: string;
  variant: 'primary' | 'default' | 'warning' | 'danger';
  confirm?: boolean;  // Require confirmation
}
```

---

## States

| State | Behavior |
|-------|----------|
| `connected` | All controls enabled |
| `disconnected` | All controls disabled, "Connect" shown |
| `busy` | Action buttons disabled, mode/speed enabled |
| `emergency` | E-stop active, only reset enabled |
| `locked` | Mode selector disabled (admin override) |

---

## Action Button Variants

| Variant | Use Case | Color |
|---------|----------|-------|
| `primary` | Main action (Start, Resume) | Blue/Green |
| `default` | Secondary actions (Pause, Home) | Gray |
| `warning` | Caution actions (Stop, Abort) | Amber |
| `danger` | Destructive (Emergency, Reset) | Red |

---

## Usage

### Full Control Panel

```tsx
<ControlPanel
  mode={robot.mode}
  onModeChange={setMode}
  speed={robot.speed}
  onSpeedChange={setSpeed}
  availableActions={ROBOT_ACTIONS}
  onAction={executeAction}
  disabledActions={robot.state === 'running' ? ['start'] : ['pause', 'stop']}
  eStopActive={robot.eStopActive}
  onEStop={triggerEStop}
  onEStopReset={resetEStop}
  robotConnected={robot.connected}
  variant="full"
/>
```

### Compact (Tablet)

```tsx
<ControlPanel
  mode={robot.mode}
  onModeChange={setMode}
  speed={robot.speed}
  onSpeedChange={setSpeed}
  availableActions={CORE_ACTIONS}
  onAction={executeAction}
  eStopActive={robot.eStopActive}
  onEStop={triggerEStop}
  variant="compact"
  orientation="vertical"
/>
```

### Minimal (Mobile/Widget)

```tsx
<ControlPanel
  mode={robot.mode}
  onModeChange={setMode}
  availableActions={['start', 'pause', 'stop']}
  onAction={executeAction}
  eStopActive={robot.eStopActive}
  onEStop={triggerEStop}
  variant="minimal"
  showSpeed={false}
/>
```

---

## Safety Features

### Confirmation Dialogs

```tsx
// Actions requiring confirmation
<ActionButtons
  actions={[
    { id: 'stop', label: 'Stop', icon: '⏹', confirm: true, message: 'Stop all operations?' },
    { id: 'reset', label: 'Reset', icon: '🔄', confirm: true, message: 'Reset robot state?' },
  ]}
  showConfirmation={true}
/>
```

### E-Stop Priority

- E-stop **ALWAYS** visible and enabled (when connected)
- E-stop overrides all other controls
- Visual + auditory feedback on activation
- Requires explicit reset action

### Mode Locking

```tsx
// Admin can lock mode to prevent changes
<ModeSelector
  mode="auto"
  locked={true}
  lockReason="Mission in progress"
/>
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Toggle Start/Pause |
| `S` | Stop |
| `H` | Return Home |
| `E` | Emergency Stop |
| `1/2/3` | Mode: Auto/Manual/Teleop |
| `↑/↓` | Speed +/- 10% |

---

## Accessibility

```html
<!-- Control Panel Container -->
<div role="region" aria-label="Robot controls" aria-describedby="robot-status">

  <!-- Mode Selector -->
  <div role="radiogroup" aria-label="Operation mode">
    <input type="radio" name="mode" value="auto" checked aria-label="Auto mode" />
    <input type="radio" name="mode" value="manual" aria-label="Manual mode" />
  </div>

  <!-- Speed Control -->
  <div>
    <label id="speed-label">Speed: 80%</label>
    <input
      type="range"
      min="0"
      max="100"
      value="80"
      aria-labelledby="speed-label"
    />
  </div>

  <!-- Action Buttons -->
  <div role="group" aria-label="Robot actions">
    <button aria-label="Start robot">▶ Start</button>
    <button aria-label="Pause robot" disabled>⏸ Pause</button>
  </div>

  <!-- Emergency -->
  <button
    aria-label="Emergency stop"
    aria-pressed="false"
    class="emergency-button"
  >⚠ STOP</button>
</div>
```

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| `sm` (<640px) | Vertical stack, E-stop fixed bottom |
| `md` (640-1024px) | 2-column, mode/speed | action buttons |
| `lg` (>1024px) | Full horizontal layout |

---

## Related Components

- **Organisms:** `RobotDetailView`, `FleetControlPanel`
- **Atoms:** `Button`, `ToggleButton`, `Slider`, `IconButton`, `Divider`

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial molecule documentation |
