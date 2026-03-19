# Component: Icon System

## Purpose
Unified visual language for robot interface communication. Icons provide instant recognition of robot states, actions, and navigation elements across all AgencyOS touchpoints.

## Anatomy
```
┌──────────────────────┐
│   ┌────────────┐     │
│   │            │     │  24x24 grid
│   │   [●]      │     │  2px stroke
│   │            │     │  2px padding
│   └────────────┘     │
│     │← 24px →│       │
│     │← 20px →│       │  Icon canvas (safe zone)
└──────────────────────┘
```

**Grid System:**
- Canvas: 24x24px
- Safe zone: 20x20px (2px padding)
- Stroke: 2px consistent weight
- Corner radius: 2px for rounded elements

## Categories

### Robot Status Icons

| Icon Name | Visual | Use Case |
|-----------|--------|----------|
| `robot-online` | Circle with check | Robot connected and operational |
| `robot-offline` | Circle with X | Robot disconnected or powered down |
| `robot-charging` | Battery with lightning | Charging station docked |
| `robot-battery-low` | Battery at 20% | Battery warning (<15%) |
| `robot-battery-critical` | Battery at 5%, red | Critical battery (<5%) |
| `robot-moving` | Wheels with motion lines | Robot in transit |
| `robot-idle` | Circle, static | Robot stationary, ready |
| `robot-error` | Triangle with exclamation | Hardware/software fault |
| `robot-calibrating` | Crosshair target | Sensor calibration in progress |
| `robot-homing` | Home icon with arrow | Returning to base |

### Action Icons

| Icon Name | Visual | Use Case |
|-----------|--------|----------|
| `play` | Right triangle | Start mission/task |
| `pause` | Two vertical bars | Pause current operation |
| `stop` | Square | Stop operation |
| `restart` | Circular arrow | Restart mission |
| `abort` | X in circle | Cancel/abort operation |
| `upload` | Arrow up from tray | Upload mission/program |
| `download` | Arrow down to tray | Download logs/data |
| `sync` | Two circular arrows | Sync robot state |
| `refresh` | Circular arrow CW | Refresh data |
| `edit` | Pencil | Edit mission/waypoint |
| `delete` | Trash bin | Delete item |
| `duplicate` | Two overlapping squares | Copy mission |
| `export` | Arrow pointing out | Export data |
| `import` | Arrow pointing in | Import configuration |

### Navigation Icons

| Icon Name | Visual | Use Case |
|-----------|--------|----------|
| `home` | House outline | Dashboard/home |
| `missions` | Map with route | Missions list |
| `robots` | Robot silhouette | Fleet view |
| `analytics` | Bar chart | Analytics/reports |
| `settings` | Gear/cog | Settings |
| `map` | Folded map | Map view |
| `calendar` | Calendar grid | Schedule |
| `users` | Multiple people | Team management |
| `logs` | Document list | System logs |
| `help` | Question mark | Help/support |

### Communication Icons

| Icon Name | Visual | Use Case |
|-----------|--------|----------|
| `message` | Speech bubble | Chat/messages |
| `notification` | Bell | Alerts/notifications |
| `notification-muted` | Bell with slash | Notifications off |
| `broadcast` | Signal waves | Broadcast to fleet |
| `signal-strong` | Full bars | Strong connection |
| `signal-weak` | 1 bar | Weak connection |
| `signal-lost` | X over bars | No connection |
| `wifi` | WiFi symbol | Network status |
| `bluetooth` | Bluetooth rune | BT connection |
| `usb` | USB trident | USB connected |

### Alert Icons

| Icon Name | Visual | Use Case |
|-----------|--------|----------|
| `alert-info` | Circle with i | Informational |
| `alert-success` | Circle with check | Success confirmation |
| `alert-warning` | Triangle with ! | Warning/caution |
| `alert-error` | Circle with X | Error/failure |
| `alert-critical` | Skull or hazard | Critical danger |
| `bell` | Bell outline | Notification |
| `bell-ring` | Bell with waves | Active alert |
| `siren` | Siren light | Emergency alert |

## States

| State | Treatment |
|-------|-----------|
| `default` | Standard stroke, `--color-icon-default` |
| `hover` | +10% opacity, cursor pointer |
| `active` | Scale 0.95, pressed effect |
| `disabled` | 40% opacity, no interaction |
| `animated` | CSS animation for status (pulse, spin) |

## Sizing

| Size | Dimensions | Use Case |
|------|------------|----------|
| `xs` | 12x12px | Inline text, badges |
| `sm` | 16x16px | Buttons (sm), labels |
| `md` | 20x20px | Buttons (md), default |
| `lg` | 24x24px | Buttons (lg), navigation |
| `xl` | 32x32px | Hero, empty states |
| `2xl` | 48x48px | Marketing, illustrations |

## Accessibility

- **WCAG 2.1 AA**: 3:1 contrast for UI components
- **Decorative icons**: `aria-hidden="true"`
- **Functional icons**: `aria-label` or `title`
- **Animated icons**: Respect `prefers-reduced-motion`
- **Color independence**: Never use color alone to convey meaning

## Token Usage

```json
{
  "icon": {
    "size": {
      "xs": "12px",
      "sm": "16px",
      "md": "20px",
      "lg": "24px",
      "xl": "32px",
      "2xl": "48px"
    },
    "stroke": {
      "default": "2px",
      "bold": "2.5px"
    },
    "color": {
      "default": "--color-icon-default",
      "secondary": "--color-icon-secondary",
      "success": "--color-feedback-success",
      "warning": "--color-feedback-warning",
      "error": "--color-feedback-error",
      "critical": "--color-safety-critical"
    }
  }
}
```

## Code Example

```tsx
import {
  RobotOnlineIcon,
  AlertWarningIcon,
  PlayIcon,
  EmergencyStopIcon
} from '@raas/atom-components';

// Status indicator with animation
<RobotOnlineIcon
  size="lg"
  color="success"
  isAnimated={true}  // Pulsing effect
  aria-label="Robot online"
/>

// Warning state
<AlertWarningIcon
  size="md"
  color="warning"
  aria-label="Warning: Low battery"
/>

// Action button icon
<button aria-label="Start mission">
  <PlayIcon size="md" />
</button>

// Navigation icon
<nav aria-label="Main navigation">
  <a href="/robots">
    <RobotsIcon size="lg" aria-hidden="true" />
    <span className="sr-only">Robots</span>
  </a>
</nav>
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Mix stroke weights in same icon set | Maintain 2px stroke consistency |
| Use icons without labels for actions | Always pair with text or aria-label |
| Create custom icons for common actions | Use existing system icons first |
| Animate all icons simultaneously | Animate only status indicators |
| Use color alone for status meaning | Combine color + shape + label |
| Scale icons non-proportionally | Maintain aspect ratio always |
| Export icons without viewBox | Always include `viewBox="0 0 24 24"` |

## Icon Request Template

```markdown
**Icon Name**: robot-obstacle-detected
**Category**: Robot Status
**Description**: Robot has detected an obstacle in path
**Visual Concept**: Robot silhouette with warning triangle overlay
**Priority**: High (used in navigation error states)
**Variants Needed**: Default, animated (pulsing)
```
