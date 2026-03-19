/**
 * Telemetry Types
 * RaaS UX Kit v2.1.79
 */

import { TimeRange } from './robot';

// ============================================
// Telemetry Stream Types
// ============================================

export type TelemetryStreamType = 'line' | 'area' | 'bar' | 'gauge' | 'scatter';

export type ChartType = 'line' | 'area' | 'area-stacked' | 'bar' | 'multi-line' | 'gauge' | 'scatter';

export interface TelemetryStream {
  id: string;
  name: string;
  unit: string;
  type: TelemetryStreamType;
  data: TimeSeriesPoint[];
  color?: string;
  min?: number;
  max?: number;
  threshold?: ThresholdConfig;
}

export interface TimeSeriesPoint {
  timestamp: Date;
  value: number;
  [key: string]: unknown;
}

export interface ThresholdConfig {
  warning: number;
  critical: number;
}

// ============================================
// Chart Configuration
// ============================================

export interface ChartConfig {
  type: ChartType;
  title: string;
  streamId?: string;
  streams?: ChartStream[];
  yAxis?: AxisConfig;
  xAxis?: AxisConfig;
  annotations?: Annotation[];
  zones?: ChartZone[];
}

export interface ChartStream {
  id: string;
  label: string;
  color?: string;
}

export interface AxisConfig {
  label?: string;
  min?: number;
  max?: number;
  ticks?: number[];
  format?: (value: number) => string;
}

export interface Annotation {
  type: 'threshold' | 'event' | 'region';
  value?: number;
  label?: string;
  style?: 'dashed' | 'solid' | 'dotted';
  color?: string;
}

export interface ChartZone {
  min: number;
  max: number;
  color: string;
  label?: string;
}

// ============================================
// Telemetry Data
// ============================================

export interface TelemetryData {
  robotId: string;
  streams: TelemetryStream[];
  startTime: Date;
  endTime: Date;
  pointCount: number;
}

export interface TelemetryPoint {
  timestamp: Date;
  [streamId: string]: number | Date;
}

// ============================================
// Threshold Breach
// ============================================

export interface ThresholdBreach {
  streamId: string;
  value: number;
  threshold: number;
  type: 'warning' | 'critical';
  timestamp: Date;
  duration?: number; // ms
}

// ============================================
// Telemetry Dashboard Props
// ============================================

export interface TelemetryDashboardProps {
  robotId: string;
  streams: TelemetryStream[];
  defaultRange?: TimeRange;
  availableRanges?: TimeRange[];
  onRangeChange?: (range: TimeRange) => void;
  charts?: ChartConfig[];
  layout?: 'single' | 'grid-2' | 'grid-4' | 'custom';
  customLayout?: GridConfiguration;
  onExport?: (format: ExportFormat, data: TelemetryData) => void;
  exportEnabled?: boolean;
  liveMode?: boolean;
  refreshInterval?: number;
  onLiveToggle?: (enabled: boolean) => void;
  className?: string;
}

export interface GridConfiguration {
  columns: number;
  rows: number;
  cells: GridCell[];
}

export interface GridCell {
  chart: string; // chart id
  colspan?: number;
  rowspan?: number;
}

export type ExportFormat = 'csv' | 'json' | 'pdf';

// ============================================
// Telemetry Context
// ============================================

export interface TelemetryContextType {
  isConnected: boolean;
  isOffline: boolean;
  lastSync?: Date;
  cachedData: TelemetryData | null;
  refreshData: () => Promise<void>;
  exportData: (format: ExportFormat) => Promise<void>;
}

// ============================================
// WebSocket Message Types
// ============================================

export interface TelemetryWebSocketMessage {
  type: 'data' | 'threshold_breach' | 'connection_change';
  robotId: string;
  timestamp: Date;
  data?: TelemetryPoint;
  breach?: ThresholdBreach;
  connectionState?: 'connected' | 'disconnected';
}

// ============================================
// Cache Configuration
// ============================================

export interface CacheConfig {
  memory: {
    maxPoints: number;
    streams: 'all' | 'configured';
  };
  indexedDB: {
    maxAge: number; // ms
    streams: 'all' | 'configured';
  };
  syncStrategy: 'merge' | 'replace' | 'local-first';
}

// ============================================
// Metric Types (for StatCard)
// ============================================

export type MetricType = 'battery' | 'signal' | 'temperature' | 'uptime' | 'custom';

export type TrendDirection = 'up' | 'down' | 'stable';

export interface Trend {
  direction: TrendDirection;
  value: number;
  period: string; // e.g., '1h', '24h', '7d'
}

export interface MetricThresholds {
  min: number;
  max: number;
  critical: number;
}

export interface StatCardProps {
  type: MetricType;
  value: number;
  label?: string;
  unit?: string;
  trend?: Trend;
  quality?: SignalQuality;
  duration?: string;
  thresholds?: MetricThresholds;
  variant?: 'default' | 'compact' | 'minimal';
  colorize?: boolean;
  className?: string;
}

// Reuse SignalQuality from robot types
type SignalQuality = 'excellent' | 'good' | 'fair' | 'poor';
