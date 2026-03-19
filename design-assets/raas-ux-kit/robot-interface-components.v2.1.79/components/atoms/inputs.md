# Component: Inputs

## Purpose
Form input components for robot configuration, mission parameters, and system settings. Designed for precision control in industrial environments where accuracy and safety are paramount.

## Anatomy

### Text Input
```
┌─────────────────────────────────────────┐
│  Label                          (▼)    │
│  ─────────────────────────────────────  │
│  [Icon] Placeholder text       [Clear] │
│  ─────────────────────────────────────  │
│  Helper text / Error message           │
└─────────────────────────────────────────┘
```

### Toggle
```
Label          [○═══]  On/Off text
─────          ───────  ───────────
               Track + Thumb
               State indicator
```

### Slider
```
Label
─────
○─────────●─────────○
│         │         │
Min      Value     Max
         (draggable)
```

## Types

### Text Input
Standard single-line text entry.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | `text|email|number|password|tel|url` | `text` | HTML input type |
| `value` | `string` | — | Controlled value |
| `placeholder` | `string` | — | Hint text |
| `prefix` | `ReactNode` | — | Icon/text before input |
| `suffix` | `ReactNode` | — | Icon/text after input |
| `clearable` | `boolean` | `false` | Show clear button |

### Textarea
Multi-line text entry for descriptions, notes, logs.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `rows` | `number` | `3` | Visible rows |
| `maxRows` | `number` | `10` | Max rows before scroll |
| `autoResize` | `boolean` | `false` | Auto-expand to content |
| `value` | `string` | — | Controlled value |

### Select
Dropdown selection from predefined options.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `options` | `Option[]` | — | Available choices |
| `value` | `string` | — | Selected value |
| `placeholder` | `string` | — | Default prompt |
| `searchable` | `boolean` | `false` | Enable filtering |
| `multi` | `boolean` | `false` | Multiple selection |

### Checkbox
Binary selection, independent of other checkboxes.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `checked` | `boolean` | — | Checked state |
| `indeterminate` | `boolean` | `false` | Partial selection |
| `label` | `string` | — | Inline label |

### Radio
Single selection from mutually exclusive options.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `options` | `Option[]` | — | Available choices |
| `value` | `string` | — | Selected value |
| `orientation` | `horizontal|vertical` | `vertical` | Layout direction |

### Toggle (Switch)
Binary on/off toggle for settings and modes.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `checked` | `boolean` | — | On/off state |
| `size` | `sm|md|lg` | `md` | Physical size |
| `labels` | `{on: string, off: string}` | — | Text labels |

### Slider
Continuous value selection within range.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `min` | `number` | `0` | Minimum value |
| `max` | `number` | `100` | Maximum value |
| `step` | `number` | `1` | Increment size |
| `value` | `number` | — | Current value |
| `marks` | `number[]` | — | Position markers |
| `range` | `boolean` | `false` | Dual-handle range |

## States

| State | Visual Treatment |
|-------|------------------|
| `default` | Standard styling, `--color-border-default` |
| `focus` | Ring 2px, `--color-focus-ring`, border `--color-action-primary` |
| `error` | Border `--color-feedback-error`, message below |
| `disabled` | Background `--color-surface-disabled`, no interaction |
| `readonly` | Border only, no background, non-editable |

## Sizing

| Size | Height | Font | Use Case |
|------|--------|------|----------|
| `sm` | 32px | 13px | Dense forms, inline editing |
| `md` | 40px | 14px | Default, settings, dialogs |
| `lg` | 48px | 16px | Hero forms, critical inputs |

## Robot-Specific Controls

### Speed Slider
```tsx
<SpeedSlider
  min={0}
  max={100}
  step={5}
  value={speedPercent}
  marks={[25, 50, 75, 100]}
  renderMark={(val) => `${val}%`}
  warningThreshold={80}
  maxSafeSpeed={robot.maxSpeed}
/>
```

### Mode Selector
```tsx
<Radio.Group
  name="operation-mode"
  options={[
    { value: 'manual', label: 'Manual', icon: <ManualIcon /> },
    { value: 'auto', label: 'Autonomous', icon: <AutoIcon /> },
    { value: 'teleop', label: 'Teleoperated', icon: <TeleopIcon /> },
  ]}
  value={operationMode}
  orientation="horizontal"
/>
```

### Coordinate Inputs
```tsx
<CoordinateInputGroup
  x={{ value: 1250, unit: 'mm', min: 0, max: 5000 }}
  y={{ value: 3400, unit: 'mm', min: 0, max: 5000 }}
  z={{ value: 0, unit: 'mm', min: -500, max: 500 }}
  onChange={handleCoordinateChange}
  precision={1}
/>
```

### Emergency Override
```tsx
<Toggle
  checked={overrideEnabled}
  labels={{ on: 'Override Active', off: 'Normal Mode' }}
  variant="danger"
  confirmRequired={true}
  confirmMessage="Enable safety override?"
/>
```

## Accessibility

- **WCAG 2.1 AA**: 4.5:1 contrast for text and placeholders
- **Labels**: Every input must have associated `<label>` or `aria-label`
- **Error Association**: `aria-describedby` links input to error message
- **Keyboard**: Full navigation, Arrow keys for select/slider
- **Focus**: Visible 3px ring, `--color-focus-ring`
- **Touch**: Minimum 44x44px touch target

## Token Usage

```json
{
  "input": {
    "height": {
      "sm": "32px",
      "md": "40px",
      "lg": "48px"
    },
    "border": {
      "default": "--color-border-default",
      "focus": "--color-action-primary",
      "error": "--color-feedback-error",
      "disabled": "--color-border-disabled"
    },
    "focus-ring": "--color-focus-ring",
    "background": {
      "default": "--color-surface-primary",
      "disabled": "--color-surface-disabled"
    }
  },
  "slider": {
    "track": "--color-surface-tertiary",
    "fill": "--color-action-primary",
    "thumb": "--color-surface-inverse",
    "warning": "--color-feedback-warning"
  },
  "toggle": {
    "track-off": "--color-surface-tertiary",
    "track-on": "--color-action-primary",
    "thumb": "--color-surface-inverse"
  }
}
```

## Code Example

```tsx
import {
  Input,
  Textarea,
  Select,
  Checkbox,
  Radio,
  Toggle,
  Slider,
  CoordinateInput
} from '@raas/atom-components';

// Text input with validation
<Input
  label="Robot Name"
  value={robotName}
  onChange={setRobotName}
  placeholder="Enter robot identifier"
  error={errors.robotName}
  required
  maxLength={32}
/>

// Number input with units
<Input
  type="number"
  label="Max Speed"
  value={maxSpeed}
  onChange={setMaxSpeed}
  suffix="mm/s"
  min={0}
  max={5000}
  step={10}
/>

// Select with search
<Select
  label="Mission Template"
  options={missionTemplates}
  value={selectedTemplate}
  onChange={setSelectedTemplate}
  searchable
  placeholder="Select or search..."
/>

// Toggle for safety-critical setting
<Toggle
  label="Collision Avoidance"
  checked={collisionAvoidance}
  onChange={setCollisionAvoidance}
  labels={{ on: 'Enabled', off: 'Disabled' }}
  variant="success"
/>

// Speed slider with warning zone
<Slider
  label="Speed Limit"
  min={0}
  max={100}
  step={5}
  value={speedLimit}
  onChange={setSpeedLimit}
  marks={[25, 50, 75, 100]}
  warningThreshold={80}
  renderMark={(v) => `${v}%`}
/>

// Coordinate inputs for waypoint
<CoordinateInput
  label="Waypoint Position"
  axes={['x', 'y', 'z']}
  value={position}
  onChange={setPosition}
  unit="mm"
  precision={2}
/>

// Checkbox group
<Checkbox.Group
  label="Enabled Sensors"
  options={[
    { value: 'lidar', label: 'LiDAR' },
    { value: 'camera', label: 'Vision Camera' },
    { value: 'imu', label: 'IMU' },
  ]}
  value={enabledSensors}
  onChange={setEnabledSensors}
/>
```

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Use text input for predefined options | Use Select or Radio for limited choices |
| Disable inputs without explanation | Provide helper text for disabled state |
| Remove labels for "cleaner" look | Labels are mandatory for accessibility |
| Use sliders for precise numeric entry | Provide both slider + number input |
| Chain multiple toggles without group labels | Group related toggles under section |
| Allow unlimited input without validation | Set appropriate min/max/maxLength |
| Use error state for warnings | Use warning variant, reserve error for validation failures |
| Toggle for irreversible actions | Use explicit button with confirmation |

## Validation Patterns

```tsx
// Required field
<Input
  label="Mission Name"
  required
  validate={(v) => v.length >= 3 ? null : 'Minimum 3 characters'}
/>

// Pattern validation
<Input
  type="email"
  label="Alert Email"
  validate={(v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
    ? null
    : 'Invalid email format'}
/>

// Async validation
<Input
  label="Robot ID"
  validate={async (v) => {
    const exists = await checkRobotId(v);
    return exists ? 'Robot ID already exists' : null;
  }}
/>
```
