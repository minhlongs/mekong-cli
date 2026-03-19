# Component: Status Badges

## Purpose
Compact status indicators that communicate robot state, connection status, and operational mode at a glance. Essential for fleet monitoring dashboards and robot status headers.

## Anatomy
```
┌──────────────────────────────────────────┐
│  ●  Status Text                   [▼]   │
│  │   ────────────                ───    │
│  │   Label                         │    │
│  │                                 │    │
│  Dot indicator              Optional    │
│  (colored)                    dropdown  │
└──────────────────────────────────────────┘
```

**Parts:**
- **Dot Indicator**: Circular status color (8px md size)
- **Label**: Status text (required)
- **Dropdown Arrow**: Optional, for selectable statuses

## Variants

| Variant | Dot Color | Background | Use Case |
|---------|-----------|------------|----------|
| `online` | `--color-status-online` (#22c55e) | `--color-status-online-subtle` | Robot operational, connected |
| `offline` | `--color-status-offline` (#6b7280) | `--color-status-offline-subtle` | Robot disconnected, powered down |
| `charging` | `--color-status-charging` (#f59e0b) | `--color-status-charging-subtle` | Docked and charging |
| `error` | `--color-status-error` (#ef4444) | `--color-status-error-subtle` | Critical fault, needs attention |
| `warning` | `--color-status-warning` (#f59e0b) | `--color-status-warning-subtle` | Non-critical issue |
| `paused` | `--color-status-paused` (#8b5cf6) | `--color-status-paused-subtle` | Mission paused by user |
| `busy` | `--color-status-busy` (#3b82f6) | `--color-status-busy-subtle` | Executing task, do not disturb |
| `idle` | `--color-status-idle` (#22c55e) | `--color-status-idle-subtle` | Ready for assignment |
| `maintenance` | `--color-status-maintenance` (#ec4899) | `--color-status-maintenance-subtle` | Scheduled maintenance |

## States

| State | Visual Treatment |
|-------|------------------|
| `default` | Standard variant styling |
| `hover` | +5% background darkening, cursor pointer (if clickable) |
| `pulsing` | Dot animates (scale 1.0→1.3, 1.5s infinite) |
| `disabled` | 40% opacity, no interaction |

### Pulsing Animation (Critical Statuses)
```css
@keyframes badge-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}
```

Apply to: `error`, `warning`, `charging` variants by default.

## Sizing

| Size | Height | Dot Size | Font | Padding X | Use Case |
|------|--------|----------|------|-----------|----------|
| `sm` | 20px | 6px | 11px/500 | 8px | Dense tables, list views |
| `md` | 24px | 8px | 12px/500 | 10px | Default, headers, cards |
| `lg` | 32px | 12px | 14px/600 | 14px | Hero status, detail views |

## Accessibility

- **WCAG 2.1 AA**: 4.5:1 contrast for text
- **Color + Shape**: Dot indicator supplemented with text label
- **Screen Reader**: Announce full status (e.g., "Robot status: online")
- **Animation**: Respect `prefers-reduced-motion`, use static dot
- **Keyboard**: Clickable badges focusable with Tab

## Token Usage

```json
{
  "badge": {
    "online": {
      "dot": "--color-status-online",
      "background": "--color-status-online-subtle",
      "text": "--color-status-online-text"
    },
    "error": {
      "dot": "--color-status-error",
      "background": "--color-status-error-subtle",
      "text": "--color-status-error-text",
      "pulse": true
    }
  },
  "size": {
    "sm": { "height": "20px", "dot": "6px", "font": "11px" },
    "md": { "height": "24px", "dot": "8px", "font": "12px" },
    "lg": { "height": "32px", "dot": "12px", "font": "14px" }
  }
}
```

## Code Example

```tsx
import { StatusBadge } from '@raas/atom-components';

// Basic status
<StatusBadge variant="online" size="md">
  Online
</StatusBadge>

// Pulsing error state
<StatusBadge
  variant="error"
  size="lg"
  isPulsing={true}
>
  Connection Lost
</StatusBadge>

// Clickable with dropdown
<StatusBadge
  variant="busy"
  size="md"
  onClick={handleStatusChange}
  isDropdown={true}
>
  Executing Mission A-42
</StatusBadge>

// In robot card header
<Card.Header>
  <RobotAvatar robotId="R-001" />
  <div>
    <RobotName>WALL-E</RobotName>
    <StatusBadge variant="charging" size="sm">
      Charging (87%)
    </StatusBadge>
  </div>
</Card.Header>

// In fleet table
<Table.Row>
  <Table.Cell>
    <StatusBadge variant={robot.status} size="sm">
      {robot.statusText}
    </StatusBadge>
  </Table.Cell>
</Table.Row>
```

## Composite Badge Patterns

### Battery + Status
```tsx
<div className="flex items-center gap-2">
  <StatusBadge variant="online">Online</StatusBadge>
  <BatteryIndicator level={87} />
</div>
```

### Multi-Status (Fleet Summary)
```tsx
<div className="flex items-center gap-1">
  <StatusBadge variant="online" size="sm">12</StatusBadge>
  <StatusBadge variant="offline" size="sm">2</StatusBadge>
  <StatusBadge variant="error" size="sm">1</StatusBadge>
</div>
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Use badges for long text (>20 chars) | Keep labels concise, truncate if needed |
| More than 3 badges in a row | Use summary pattern for multiple statuses |
| Rely on color alone for status | Always include text label |
| Use pulsing for stable statuses | Reserve animation for urgent states |
| Mix sizes within same context | Consistent sizing within components |
| Use error variant for non-errors | Match variant to actual severity |

## Robot Status Mappings

| Robot State | Badge Variant | Label Pattern |
|-------------|---------------|---------------|
| `connected + ready` | `online` | "Online" or "Ready" |
| `disconnected` | `offline` | "Offline" |
| `dock_state == charging` | `charging` | "Charging (XX%)" |
| `battery < 15%` | `warning` | "Low Battery (XX%)" |
| `battery < 5%` | `error` | "Critical Battery" |
| `mission_state == paused` | `paused` | "Paused" |
| `mission_state == running` | `busy` | "Executing: {mission_name}" |
| `error_code != null` | `error` | "{error_message}" |
| `maintenance_mode == true` | `maintenance` | "Maintenance" |
