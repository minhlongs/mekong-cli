# Telemetry Dashboard

**Version:** 2.1.79 | **Type:** Organism | **Status:** Production Ready

---

## Overview

Data visualization panel for real-time and historical telemetry streams. Supports multiple chart types, time range selection, and data export capabilities.

---

## Anatomy

```
┌─────────────────────────────────────────────────────────────────────┐
│  TELEMETRY DASHBOARD                           [Export] [Settings]  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────────┐ │
│  │ 1H │ 6H │ 24H│ │ 1D │ 7D │ 30D│ │ ⚡ 2.4A    │ │ 📊 CSV       │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐ ┌─────────────────────────────────┐   │
│  │     Battery Voltage     │ │      Motor RPM (All Axes)       │   │
│  │   ┌───────────────┐     │ │   ┌─────────────────────────┐   │   │
│  │   │   Line Chart  │     │ │   │    Multi-Line Chart     │   │   │
│  │   │   24V → 23.8V │     │ │   │    M1, M2, M3, M4       │   │   │
│  │   └───────────────┘     │ │   └─────────────────────────┘   │   │
│  │   Now -1H               │ │   Now -6H                       │   │
│  └─────────────────────────┘ └─────────────────────────────────┘   │
│  ┌─────────────────────────┐ ┌─────────────────────────────────┐   │
│  │    Temperature Trend    │ │      IMU Orientation            │   │
│  │   ┌───────────────┐     │ │   ┌─────────────────────────┐   │   │
│  │   │  Area Chart   │     │ │   │    3-Axis Gauge         │   │   │
│  │   │  Core, Motor  │     │ │   │    Roll/Pitch/Yaw       │   │   │
│  │   └───────────────┘     │ │   └─────────────────────────┘   │   │
│  └─────────────────────────┘ └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Props Interface

```typescript
interface TelemetryDashboardProps {
  // Data Source
  robotId: string;
  streams: TelemetryStream[];

  // Time Range
  defaultRange: TimeRange;
  availableRanges: TimeRange[];
  onRangeChange: (range: TimeRange) => void;

  // Chart Configuration
  charts: ChartConfig[];
  layout: 'single' | 'grid-2' | 'grid-4' | 'custom';
  customLayout?: GridConfiguration;

  // Data Export
  onExport?: (format: 'csv' | 'json' | 'pdf', data: TelemetryData) => void;
  exportEnabled?: boolean;

  // Real-time
  liveMode?: boolean;
  refreshInterval?: number;
  onLiveToggle?: (enabled: boolean) => void;

  // Customization
  className?: string;
}

interface TelemetryStream {
  id: string;
  name: string;
  unit: string;
  type: 'line' | 'area' | 'bar' | 'gauge' | 'scatter';
  data: TimeSeriesPoint[];
  color?: string;
  min?: number;
  max?: number;
  threshold?: {
    warning: number;
    critical: number;
  };
}

interface TimeRange {
  label: string;
  value: string;
  duration: number; // milliseconds
}
```

---

## Chart Types

### 1. Line Chart (Single Metric)

```typescript
const batteryVoltage: ChartConfig = {
  type: 'line',
  title: 'Battery Voltage',
  streamId: 'battery.voltage',
  yAxis: { label: 'Volts', min: 20, max: 28 },
  annotations: [
    { type: 'threshold', value: 22, label: 'Low', style: 'dashed' },
    { type: 'threshold', value: 21, label: 'Critical', style: 'solid' },
  ],
};
```

### 2. Multi-Line Chart (Comparison)

```typescript
const motorRPM: ChartConfig = {
  type: 'multi-line',
  title: 'Motor RPM',
  streams: [
    { id: 'motor.m1.rpm', label: 'M1', color: '#3b82f6' },
    { id: 'motor.m2.rpm', label: 'M2', color: '#10b981' },
    { id: 'motor.m3.rpm', label: 'M3', color: '#f59e0b' },
    { id: 'motor.m4.rpm', label: 'M4', color: '#ef4444' },
  ],
  yAxis: { label: 'RPM', min: 0, max: 5000 },
};
```

### 3. Area Chart (Stacked)

```typescript
const powerDistribution: ChartConfig = {
  type: 'area-stacked',
  title: 'Power Distribution',
  streams: [
    { id: 'power.compute', label: 'Compute', color: '#8b5cf6' },
    { id: 'power.motors', label: 'Motors', color: '#3b82f6' },
    { id: 'power.sensors', label: 'Sensors', color: '#10b981' },
  ],
  yAxis: { label: 'Watts' },
};
```

### 4. Gauge (Instant Value)

```typescript
const temperatureGauge: ChartConfig = {
  type: 'gauge',
  title: 'Core Temperature',
  streamId: 'temp.core',
  min: 0,
  max: 100,
  unit: '°C',
  zones: [
    { min: 0, max: 40, color: '#22c55e', label: 'Normal' },
    { min: 40, max: 60, color: '#f59e0b', label: 'Warm' },
    { min: 60, max: 80, color: '#ef4444', label: 'Hot' },
    { min: 80, max: 100, color: '#7f1d1d', label: 'Critical' },
  ],
};
```

---

## Time Range Handling

### Preset Ranges

```typescript
const PRESET_RANGES: TimeRange[] = [
  { label: '1H', value: '1h', duration: 3600000 },
  { label: '6H', value: '6h', duration: 21600000 },
  { label: '24H', value: '24h', duration: 86400000 },
  { label: '1D', value: '1d', duration: 86400000 },
  { label: '7D', value: '7d', duration: 604800000 },
  { label: '30D', value: '30d', duration: 2592000000 },
  { label: 'Custom', value: 'custom', duration: 0 },
];
```

### Custom Range Picker

```tsx
<TimeRangeSelector
  presets={PRESET_RANGES}
  selectedRange={selectedRange}
  onRangeChange={handleRangeChange}
  customRange={{
    from: customFrom,
    to: customTo,
  }}
  onCustomRangeChange={({ from, to }) => {
    setCustomFrom(from);
    setCustomTo(to);
    setSelectedRange({ label: 'Custom', value: 'custom', duration: to - from });
  }}
/>
```

---

## Data Export

### Export Function

```typescript
const handleExport = async (format: ExportFormat) => {
  const data = await fetchTelemetryData({
    robotId,
    streams: activeStreams,
    range: selectedRange,
  });

  switch (format) {
    case 'csv':
      const csv = convertToCSV(data);
      downloadFile(`${robotId}-telemetry-${Date.now()}.csv`, csv, 'text/csv');
      break;

    case 'json':
      const json = JSON.stringify(data, null, 2);
      downloadFile(`${robotId}-telemetry-${Date.now()}.json`, json, 'application/json');
      break;

    case 'pdf':
      // Generate PDF report with charts
      await generatePDFReport({ data, charts, range: selectedRange });
      break;
  }

  toast.success(`Exported ${format.toUpperCase()} successfully`);
};
```

### Export Modal

```tsx
<ExportDialog
  open={showExportDialog}
  onOpenChange={setShowExportDialog}
  formats={[
    { value: 'csv', label: 'CSV', icon: <TableIcon /> },
    { value: 'json', label: 'JSON', icon: <CodeIcon /> },
    { value: 'pdf', label: 'PDF Report', icon: <DocumentIcon /> },
  ]}
  onExport={handleExport}
  dataPreview={{
    rows: 1247,
    columns: 8,
    timeRange: selectedRange.label,
  }}
/>
```

---

## Real-Time Data Handling

### Optimistic Updates (Chart Rendering)

```typescript
// ✅ OPTIMISTIC: Render incoming data immediately
useTelemetryStream(robotId, {
  onData: (point: TelemetryPoint) => {
    // 1. Append to chart immediately (no waiting)
    setChartData(prev => [...prev.slice(-MAX_POINTS), point]);

    // 2. Background: Server sync for validation
    syncWithServer(point);
  },
  onError: (error) => {
    // 3. Only rollback if server explicitly rejects
    if (error.type === 'invalid_data') {
      removeLastPoint();
    }
    // Network errors = keep local data, retry connection
  },
});
```

### Pessimistic Updates (Threshold Alerts)

```typescript
// ⚠️ PESSIMISTIC: Safety-critical thresholds
useTelemetryStream(robotId, {
  onThreshold: async (breach: ThresholdBreach) => {
    // 1. Wait for server confirmation
    const confirmed = await api.confirmThreshold(breach);

    // 2. Only alert if server confirms
    if (confirmed.alert) {
      triggerAlert(breach);
    }
  },
});
```

---

## Offline State Management

### Behavior When Disconnected

```typescript
const OfflineTelemetry = () => {
  const { isOffline, lastSync, cachedData } = useTelemetryContext();

  if (!isOffline) return null;

  return (
    <OfflineOverlay>
      <Banner variant="warning">
        <WifiOffIcon />
        <div>
          <strong>Connection Lost</strong>
          <p>Displaying cached data from {formatDistance(lastSync)}</p>
        </div>
      </Banner>

      {/* Charts show cached data with visual fade */}
      <ChartContainer faded={true} data={cachedData} />

      {/* Disable time range changes requiring server fetch */}
      <TimeRangeSelector disabled={['7D', '30D']} />

      {/* Queue export requests for when online */}
      <ExportButton
        onClick={queueExport}
        tooltip="Export will start when connection restored"
      />
    </OfflineOverlay>
  );
};
```

### Cache Strategy

```typescript
// Cache layers for offline resilience
const cacheConfig = {
  // L1: Memory (current session)
  memory: {
    maxPoints: 10000,
    streams: 'all',
  },

  // L2: IndexedDB (persistent)
  indexedDB: {
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    streams: 'configured',
  },

  // Sync on reconnect
  syncStrategy: 'merge', // 'merge' | 'replace' | 'local-first'
};
```

---

## Layout Configurations

### Single Chart (Focus Mode)

```tsx
<TelemetryDashboard
  layout="single"
  charts={[batteryDetail]}
  className="h-full"
/>
```

### Grid 2x2 (Default)

```tsx
<TelemetryDashboard
  layout="grid-4"
  charts={[
    batteryVoltage,
    motorRPM,
    temperatureTrend,
    imuOrientation,
  ]}
/>
```

### Custom Grid

```tsx
<TelemetryDashboard
  layout="custom"
  customLayout={{
    columns: 3,
    rows: 2,
    cells: [
      { chart: 'batteryVoltage', colspan: 2, rowspan: 1 },
      { chart: 'motorRPM', colspan: 1, rowspan: 2 },
      { chart: 'temperatureTrend', colspan: 1, rowspan: 1 },
      { chart: 'powerDistribution', colspan: 1, rowspan: 1 },
    ],
  }}
/>
```

---

## Accessibility

```tsx
<TelemetryDashboard
  charts={charts}
  // Screen reader descriptions
  chartDescriptions={{
    batteryVoltage: 'Line chart showing battery voltage over time, ranging from 20 to 28 volts',
    motorRPM: 'Multi-line chart comparing RPM of four motors over 6 hours',
  }}
  // Keyboard navigation
  enableKeyboardNav={true}
  // Live region for critical updates
  liveRegionProps={{
    'aria-live': 'polite',
    'aria-atomic': true,
  }}
/>
```

---

## Usage Examples

### Basic Dashboard

```tsx
<TelemetryDashboard
  robotId="ROB-001"
  streams={defaultStreams}
  defaultRange={{ label: '6H', value: '6h', duration: 21600000 }}
  availableRanges={PRESET_RANGES}
  charts={STANDARD_CHARTS}
  layout="grid-4"
  liveMode={true}
  refreshInterval={2000}
/>
```

### Export-Focused

```tsx
<TelemetryDashboard
  robotId="ROB-001"
  streams={allStreams}
  exportEnabled={true}
  onExport={(format, data) => handleExport(format, data)}
  defaultRange={{ label: '24H', value: '24h', duration: 86400000 }}
/>
```

### Read-Only Viewer

```tsx
<TelemetryDashboard
  robotId="ROB-001"
  streams={streams}
  charts={charts}
  liveMode={false}
  exportEnabled={false}
  layout="single"
/>
```

---

## Related Components

- **Robot Status Panel** - Quick metric overview
- **Mission Control** - Active mission telemetry
- **Fleet Overview** - Aggregated fleet metrics

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 2.1.79 | 2026-03-19 | Initial organism documentation |
| 2.1.78 | 2026-03-15 | Added IndexedDB caching for offline |
| 2.1.77 | 2026-03-10 | Multi-line chart support |
