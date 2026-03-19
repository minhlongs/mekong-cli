# Stat Card

**Version:** 2.1.79 | **Type:** Molecule | **Status:** Stable

---

## Overview

Single metric display component for robot telemetry and status indicators. Combines value, label, icon, and trend indicator in a compact card format.

---

## Anatomy

```
┌─────────────────┐
│  🔋  Battery    │  ← Icon + Label (header)
│  87%            │  ← Value (large)
│  ▲ 12% vs 1h    │  ← Trend indicator
└─────────────────┘
```

### Components

| Element | Atom Reference | Description |
|---------|----------------|-------------|
| Icon | `icon` | Metric type indicator |
| Label | `text-label` | Metric name |
| Value | `text-display` | Primary metric value |
| Trend | `trend-indicator` | Directional change |
| Container | `card` | Outer shell |

---

## Variants

### Battery Level

```tsx
<StatCard
  type="battery"
  value={87}
  unit="%"
  trend={{ direction: 'up', value: 12, period: '1h' }}
/>
```

**Visual:**
```
┌─────────────────┐
│  🔋  Battery    │
│  87%            │
│  ▲ 12% vs 1h    │
└─────────────────┘
```

---

### Signal Strength

```tsx
<StatCard
  type="signal"
  value={-42}
  unit="dBm"
  trend={{ direction: 'stable', value: 0, period: '5m' }}
  quality="excellent"  // excellent | good | fair | poor
/>
```

**Visual:**
```
┌─────────────────┐
│  📶  Signal     │
│  -42 dBm        │
│  ● Stable       │
└─────────────────┘
```

---

### Temperature

```tsx
<StatCard
  type="temperature"
  value={45.2}
  unit="°C"
  trend={{ direction: 'down', value: 3.1, period: '10m' }}
  thresholds={{ min: 10, max: 60, critical: 75 }}
/>
```

**Visual:**
```
┌─────────────────┐
│  🌡️  Temp       │
│  45.2°C         │
│  ▼ 3.1° vs 10m  │
└─────────────────┘
```

---

### Uptime

```tsx
<StatCard
  type="uptime"
  value={99.97}
  unit="%"
  trend={{ direction: 'up', value: 0.02, period: '24h' }}
  duration="14d 6h 32m"  // Optional: show actual duration
/>
```

**Visual:**
```
┌─────────────────┐
│  ⏱️  Uptime     │
│  99.97%         │
│  ▲ 0.02% vs 24h │
│  14d 6h 32m     │  ← Optional duration
└─────────────────┘
```

---

## Props

```typescript
interface StatCardProps {
  // Core
  type: 'battery' | 'signal' | 'temperature' | 'uptime' | 'custom';
  value: number;
  label?: string;  // Auto-derived from type if omitted
  unit?: string;

  // Trend
  trend?: {
    direction: 'up' | 'down' | 'stable';
    value: number;
    period: string;  // e.g., '1h', '24h', '7d'
  };

  // Type-specific
  quality?: 'excellent' | 'good' | 'fair' | 'poor';  // For signal
  duration?: string;  // For uptime
  thresholds?: { min: number; max: number; critical: number };  // For temperature

  // Styling
  variant?: 'default' | 'compact' | 'minimal';
  colorize?: boolean;  // Default: true
  className?: string;
}
```

---

## States

| State | Description | Visual Treatment |
|-------|-------------|------------------|
| `normal` | Within thresholds | Neutral/positive color |
| `warning` | Approaching limits | Amber background |
| `critical` | Exceeded thresholds | Red background, pulse |
| `loading` | Fetching data | Skeleton animation |
| `stale` | No recent data | Grayed out, timestamp |

---

## Color Coding

### Battery

| Level | Color |
|-------|-------|
| 80-100% | Green |
| 50-79% | Blue |
| 20-49% | Amber |
| 0-19% | Red (pulse) |

### Signal Strength

| dBm Range | Quality | Color |
|-----------|---------|-------|
| > -50 | Excellent | Green |
| -50 to -60 | Good | Blue |
| -61 to -70 | Fair | Amber |
| < -70 | Poor | Red |

### Temperature

| Range | Status | Color |
|-------|--------|-------|
| < max | Normal | Green |
| max to critical | Warning | Amber |
| > critical | Critical | Red (pulse) |

### Uptime

| Percentage | Color |
|------------|-------|
| 99.9%+ | Green |
| 99-99.89% | Blue |
| 95-98.99% | Amber |
| < 95% | Red |

---

## Trend Indicators

```tsx
// Up (positive change)
<StatCard trend={{ direction: 'up', value: 12, period: '1h' }} />
// Renders: ▲ 12% vs 1h  (green)

// Down (negative change)
<StatCard trend={{ direction: 'down', value: 3.1, period: '10m' }} />
// Renders: ▼ 3.1° vs 10m  (red for temp, green for battery charging)

// Stable (no significant change)
<StatCard trend={{ direction: 'stable', value: 0, period: '5m' }} />
// Renders: ● Stable  (gray)
```

---

## Usage

### Dashboard Grid

```tsx
<div className="stats-grid">
  <StatCard
    type="battery"
    value={robot.battery}
    unit="%"
    trend={robot.batteryTrend}
  />
  <StatCard
    type="signal"
    value={robot.signal}
    unit="dBm"
    quality={getSignalQuality(robot.signal)}
  />
  <StatCard
    type="temperature"
    value={robot.temperature}
    unit="°C"
    thresholds={TEMP_THRESHOLDS}
  />
  <StatCard
    type="uptime"
    value={robot.uptime}
    unit="%"
    duration={formatDuration(robot.uptimeSeconds)}
  />
</div>
```

### Compact Mode (Mobile)

```tsx
<StatCard
  type="battery"
  value={87}
  variant="compact"
  showTrend={false}
/>
```

### Minimal (Widget)

```tsx
<StatCard
  type="signal"
  value={-42}
  variant="minimal"
  showLabel={false}
  showTrend={false}
/>
// Shows: 📶 -42 dBm
```

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| `sm` (<640px) | Full width, stacked |
| `md` (640-1024px) | 2-column grid |
| `lg` (>1024px) | 4-column grid |

---

## Accessibility

```html
<div
  role="region"
  aria-label="Battery status: 87 percent, up 12 percent in the last hour"
  aria-live="polite"
>
  <span aria-hidden="true">🔋</span>
  <span class="label">Battery</span>
  <span class="value">87%</span>
  <span class="trend positive">▲ 12% vs 1h</span>
</div>
```

---

## Related Components

- **Organisms:** `StatsGrid`, `RobotOverview`
- **Atoms:** `Icon`, `TextLabel`, `TextDisplay`, `TrendIndicator`, `Card`

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial molecule documentation |
