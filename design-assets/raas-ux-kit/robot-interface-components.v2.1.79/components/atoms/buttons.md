# Component: Buttons

## Purpose
Interactive button components for robot control operations, from routine actions to emergency stops. Provides consistent tactile feedback and clear visual hierarchy for operational safety.

## Anatomy
```
┌─────────────────────────────────────┐
│  [Icon]  Button Label      [Loader] │
│  ──────  ──────────────    ───────  │
│  Optional  Required      Loading state
│  prefix    text content  indicator
└─────────────────────────────────────┘
```

**Parts:**
- **Container**: Clickable surface with padding
- **Icon** (optional): Leading visual for action type
- **Label**: Action text (required, except icon-only)
- **Loader** (optional): Replaces icon during loading state

## Variants

| Variant | Use Case | Background | Text | Border | Robot Context |
|---------|----------|------------|------|--------|---------------|
| `primary` | Main actions | `--color-action-primary` | `--color-text-inverse` | none | Start mission, deploy task |
| `secondary` | Supporting actions | `--color-surface-tertiary` | `--color-text-primary` | none | Pause, resume, settings |
| `outline` | Low-emphasis actions | transparent | `--color-text-primary` | `--color-border-default` | Cancel, back, secondary ops |
| `ghost` | Minimal actions | transparent | `--color-text-secondary` | none | Quick settings, inline edits |
| `danger` | Destructive actions | `--color-feedback-danger` | `--color-text-inverse` | none | Delete mission, abort, reset |
| `emergency-stop` | Critical safety | `--color-safety-critical` | `--color-text-inverse` | 3px solid white | E-STOP, immediate halt |

## States

| State | Visual Treatment | Interaction |
|-------|------------------|-------------|
| `default` | Base variant styling | Clickable |
| `hover` | +10% brightness, subtle scale (1.02) | Cursor pointer |
| `active` | -10% brightness, scale (0.98) | Click feedback |
| `disabled` | 40% opacity, no cursor | Non-interactive |
| `loading` | Spinner replaces icon, 60% opacity | Non-interactive |

### Emergency Stop Special States
- **Armed**: Pulsing red glow animation (2s interval)
- **Confirmed**: Double-confirmation modal required
- **Activated**: Lockout state, requires physical key reset

## Sizing

| Size | Height | Padding X | Font | Icon Size | Use Case |
|------|--------|-----------|------|-----------|----------|
| `sm` | 32px | 12px | 12px/400 | 16px | Inline actions, dense UI |
| `md` | 40px | 16px | 14px/500 | 20px | Default, forms, dialogs |
| `lg` | 48px | 24px | 16px/600 | 24px | Hero CTAs, critical actions |
| `xl` | 64px | 32px | 18px/700 | 32px | Emergency stop only |

## Accessibility

- **WCAG 2.1 AA**: Contrast ratio minimum 4.5:1 for text
- **Keyboard**: Full Tab navigation, Enter/Space activation
- **Focus**: 3px outline, `--color-focus-ring`, 2px offset
- **ARIA**: `aria-label` for icon-only, `aria-disabled` for disabled
- **Screen Reader**: Announce loading state changes

## Token Usage

```json
{
  "button": {
    "primary": {
      "background": "--color-action-primary",
      "hover": "--color-action-primary-hover",
      "text": "--color-text-inverse"
    },
    "emergency-stop": {
      "background": "--color-safety-critical",
      "pulse-glow": "--color-safety-critical-glow",
      "min-size": "64px"
    }
  },
  "spacing": {
    "sm": "8px",
    "md": "16px",
    "lg": "24px"
  },
  "typography": {
    "button-sm": "12px/400",
    "button-md": "14px/500",
    "button-lg": "16px/600"
  }
}
```

## Code Example

```tsx
import { Button } from '@raas/atom-components';

// Primary action
<Button
  variant="primary"
  size="md"
  onClick={handleStartMission}
  icon={<PlayIcon />}
>
  Start Mission
</Button>

// Emergency stop (requires confirmation)
<Button
  variant="emergency-stop"
  size="xl"
  onClick={handleEmergencyStop}
  confirmRequired={true}
  confirmMessage="Confirm emergency stop?"
  icon={<StopIcon />}
>
  EMERGENCY STOP
</Button>

// Loading state
<Button
  variant="secondary"
  isLoading={isDeploying}
  onClick={handleDeploy}
>
  Deploy to Robot
</Button>

// Disabled state
<Button
  variant="outline"
  isDisabled={!hasSelection}
>
  Delete Selected
</Button>
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Use emergency-stop for non-critical actions | Reserve red E-STOP for true emergencies only |
| More than 1 primary button per view | Single primary action, use secondary for others |
| Disable buttons without explanation | Provide tooltip or helper text for disabled state |
| Use loading state for instant actions (<200ms) | Only show loader for async operations |
| Icon-only buttons without aria-label | Always include accessible label |
| Ghost buttons for critical actions | Use primary or danger for important operations |
