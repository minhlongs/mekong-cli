# Notification

**Version:** 2.1.79 | **Type:** Molecule | **Status:** Stable

---

## Overview

Toast/alert system for robot event notifications, mission status updates, and connection alerts. Supports multiple variants with auto-dismiss and stacking behavior.

---

## Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│  📶  Connection Restored                                   │
│      Robot R-042 reconnected after 3s                      │
│                                      [Dismiss ×]            │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Element | Atom Reference | Description |
|---------|----------------|-------------|
| Icon | `icon` | Status/type indicator |
| Title | `text-label` | Notification headline |
| Message | `text-body` | Detailed description |
| Close Button | `icon-button` | Manual dismiss |
| Progress Bar | `progress` | Auto-dismiss timer (optional) |
| Container | `card` | Outer shell |

---

## Variants

### Info Notification

System information and general updates.

```tsx
<Notification
  variant="info"
  title="Mission Scheduled"
  message="Route A-12 queued for execution at 14:00"
  duration={5000}
/>
```

**Visual:**
```
┌────────────────────────────────────────────────┐
│  ℹ️  Mission Scheduled                         │
│      Route A-12 queued for execution at 14:00 │
│                                          [×]   │
└────────────────────────────────────────────────┘
```

---

### Success Notification

Completed actions and positive confirmations.

```tsx
<Notification
  variant="success"
  title="Charging Complete"
  message="Robot R-015 battery at 100%, ready for deployment"
  duration={4000}
/>
```

**Visual:**
```
┌────────────────────────────────────────────────┐
│  ✅  Charging Complete                         │
│      Robot R-015 battery at 100%, ready...    │
│                                          [×]   │
└────────────────────────────────────────────────┘
```

---

### Warning Notification

Potential issues requiring attention.

```tsx
<Notification
  variant="warning"
  title="Low Battery"
  message="Robot R-023 at 15% - returning to dock"
  duration={6000}
  action={{ label: 'View Robot', onClick: () => viewRobot('R-023') }}
/>
```

**Visual:**
```
┌────────────────────────────────────────────────┐
│  ⚠️  Low Battery                               │
│      Robot R-023 at 15% - returning to dock   │
│                        [View Robot]      [×]   │
└────────────────────────────────────────────────┘
```

---

### Error Notification

Critical failures and system errors.

```tsx
<Notification
  variant="error"
  title="Navigation Failure"
  message="Robot R-007 lost localization in Zone C"
  duration={0}  // No auto-dismiss
  action={{ label: 'Intervene', onClick: () => intervene('R-007') }}
/>
```

**Visual:**
```
┌────────────────────────────────────────────────┐
│  🚨  Navigation Failure                        │
│      Robot R-007 lost localization in Zone C  │
│                        [Intervene]       [×]   │
└────────────────────────────────────────────────┘
```

---

## Props

```typescript
interface NotificationProps {
  // Core
  variant: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;

  // Behavior
  duration?: number;  // ms, 0 = no auto-dismiss
  dismissible?: boolean;  // Default: true
  onClose?: () => void;

  // Action
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'default';
  };

  // Position
  position?: {
    stack: 'top' | 'bottom';
    alignment: 'left' | 'center' | 'right';
  };

  // Styling
  className?: string;
}

// Notification Manager (for programmatic control)
interface NotificationManagerProps {
  notifications: NotificationData[];
  onDismiss: (id: string) => void;
  position?: 'top-right' | 'top-center' | 'bottom-right' | 'bottom-center';
  maxStack?: number;  // Default: 5
}
```

---

## States

| State | Description |
|-------|-------------|
| `entering` | Slide-in animation |
| `visible` | Fully displayed, timer running |
| `leaving` | Slide-out animation |
| `paused` | Hovered (timer paused) |
| `expanded` | Full message visible (if truncated) |

---

## Notification Types by Use Case

### Robot Event Notifications

| Event | Variant | Auto-dismiss |
|-------|---------|--------------|
| Robot online | success | 4s |
| Robot offline | error | No |
| Battery low (<20%) | warning | 6s |
| Battery critical (<5%) | error | No |
| Mission started | info | 3s |
| Mission completed | success | 4s |
| Mission failed | error | No |
| Obstacle detected | warning | 5s |
| Stuck/immobile | error | No |

---

### Mission Status Updates

| Status | Variant | Duration |
|--------|---------|----------|
| Queued | info | 3s |
| In progress | info | 3s |
| Paused | warning | 4s |
| Completed | success | 4s |
| Failed | error | No |
| Cancelled | info | 3s |

---

### Connection Alerts

| Event | Variant | Duration |
|-------|---------|----------|
| Connecting... | info | Until resolved |
| Connected | success | 3s |
| Reconnected | success | 4s |
| Disconnected | error | No |
| Connection unstable | warning | 5s (repeat) |

---

## Usage

### Single Notification

```tsx
<Notification
  variant="success"
  title="Action Complete"
  message="Robot configuration saved successfully"
  duration={4000}
  onClose={() => console.log('Dismissed')}
/>
```

### Notification Manager (Stack)

```tsx
import { useNotifications } from '@agencyos/raas-ui';

function RobotList() {
  const { addNotification, dismiss } = useNotifications();

  const handleRobotConnect = async (robotId: string) => {
    try {
      await connectRobot(robotId);
      addNotification({
        variant: 'success',
        title: 'Connected',
        message: `Robot ${robotId} is now online`,
        duration: 4000,
      });
    } catch (error) {
      addNotification({
        variant: 'error',
        title: 'Connection Failed',
        message: `Could not connect to ${robotId}`,
        duration: 0,
        action: {
          label: 'Retry',
          onClick: () => handleRobotConnect(robotId),
        },
      });
    }
  };

  return <RobotListView onConnect={handleRobotConnect} />;
}
```

### Notification Hooks

```tsx
// Pre-configured notification helpers
const { info, success, warning, error } = useNotifications();

// Usage:
success('Saved', 'Configuration updated');
error('Failed', 'Connection timeout', {
  duration: 0,
  action: { label: 'Retry', onClick: retry },
});
```

---

## Positioning

### Toast Container Positions

```tsx
// Top-right (default)
<NotificationContainer position="top-right" />

// Bottom-center
<NotificationContainer position="bottom-center" />

// Custom
<NotificationContainer
  style={{
    top: '80px',
    right: '20px',
    maxWidth: '400px',
  }}
/>
```

### Stack Behavior

```
┌─────────────────────────────────┐
│  [Notification 1]  ← First      │
│  [Notification 2]               │
│  [Notification 3]  ← Newest     │
└─────────────────────────────────┘
```

- Maximum 5 visible by default
- Oldest dismissed when limit exceeded
- Slide-in from right (top positions)
- Slide-in from bottom (bottom positions)

---

## Animation Timing

| Phase | Duration | Easing |
|-------|----------|--------|
| Enter | 300ms | ease-out |
| Exit | 250ms | ease-in |
| Progress | duration | linear |

---

## Accessibility

```html
<!-- Notification Role -->
<div
  role="alert"
  aria-live="assertive"
  aria-atomic="true"
  class="notification"
>
  <div class="notification-content">
    <span class="icon" aria-hidden="true">✅</span>
    <div class="text">
      <strong class="title">Charging Complete</strong>
      <span class="message">Robot R-015 battery at 100%</span>
    </div>
    <button
      aria-label="Dismiss notification"
      class="close-button"
    >×</button>
  </div>
</div>

<!-- For screen readers, announce on insert -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  Charging Complete: Robot R-015 battery at 100%
</div>
```

**Focus Management:**

- Auto-focus close button on notification open (optional)
- Escape key dismisses topmost notification
- Tab cycles through actionable notifications

---

## Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| `sm` (<640px) | Full width, bottom stack |
| `md` (640-1024px) | 90% width, max 3 visible |
| `lg` (>1024px) | Fixed 400px, max 5 visible |

---

## Best Practices

### Do

- ✅ Use appropriate variant for severity
- ✅ Keep titles under 50 characters
- ✅ Provide actionable info in messages
- ✅ Include action buttons for errors
- ✅ Auto-dismiss non-critical notifications

### Don't

- ❌ Use error for routine info
- ❌ Stack more than 5 notifications
- ❌ Auto-dismiss critical errors
- ❌ Use vague messages like "Error occurred"
- ❌ Block user interaction (use modals instead)

---

## Related Components

- **Organisms:** `NotificationContainer`, `AlertBanner`
- **Atoms:** `Icon`, `TextLabel`, `TextBody`, `IconButton`, `ProgressBar`

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial molecule documentation |
