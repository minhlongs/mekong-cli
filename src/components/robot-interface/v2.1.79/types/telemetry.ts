/**
 * Telemetry Types — RaaS UX Kit v2.1.79
 */
import { TimeRange, SignalQuality } from './robot';

export type TelemetryStreamType = 'line' | 'area' | 'bar' | 'gauge' | 'scatter';
export type ChartType = 'line' | 'area' | 'area-stacked' | 'bar' | 'multi-line' | 'gauge' | 'scatter';

export interface TelemetryStream {
  id: string;
  name: string;
  unit: string;
  type: TelemetryStreamType;
  displayType?: ChartType;
  data: TimeSeriesPoint[];
  color?: string;
  min?: number;
  max?: number;
  threshold?: ThresholdConfig;
  thresholds?: { min?: number; max?: number; warning?: number; critical?: number };
}

export interface TimeSeriesPoint {
  timestamp: Date | number;
  value: number;
  [key: string]: unknown;
}

export interface ThresholdConfig { warning: number; critical: number; }
export interface ChartStream { id: string; label: string; color?: string; }

export interface AxisConfig {
  key?: string;
  type?: string;
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

export interface ChartZone { min: number; max: number; color: string; label?: string; }

export interface ChartConfig {
  id?: string;
  type: ChartType;
  title: string;
  streamId?: string;
  streams?: Array<ChartStream | string>;
  yAxis?: AxisConfig;
  xAxis?: AxisConfig;
  annotations?: Annotation[];
  zones?: ChartZone[];
  showLegend?: boolean;
  showTooltip?: boolean;
  smooth?: boolean;
}

export interface TelemetryData {
  robotId: string;
  streams: TelemetryStream[];
  startTime: Date;
  endTime: Date;
  pointCount: number;
}

export interface TelemetryPoint { timestamp: Date; [streamId: string]: number | Date; }

export interface ThresholdBreach {
  streamId: string;
  value: number;
  threshold: number;
  type: 'warning' | 'critical';
  timestamp: Date;
  duration?: number;
}

export interface GridCell { chart: string; colspan?: number; rowspan?: number; }
export interface GridConfiguration { columns: number; rows: number; cells: GridCell[]; }
export type ExportFormat = 'csv' | 'json' | 'pdf';

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

export interface TelemetryContextType {
  isConnected: boolean;
  isOffline: boolean;
  lastSync?: Date;
  cachedData: TelemetryData | null;
  refreshData: () => Promise<void>;
  exportData: (format: ExportFormat) => Promise<void>;
}

export interface TelemetryWebSocketMessage {
  type: 'data' | 'threshold_breach' | 'connection_change';
  robotId: string;
  timestamp: Date;
  data?: TelemetryPoint;
  breach?: ThresholdBreach;
  connectionState?: 'connected' | 'disconnected';
}

export interface CacheConfig {
  memory: { maxPoints: number; streams: 'all' | 'configured' };
  indexedDB: { maxAge: number; streams: 'all' | 'configured' };
  syncStrategy: 'merge' | 'replace' | 'local-first';
}

export type MetricType = 'battery' | 'signal' | 'temperature' | 'uptime' | 'custom';
export type TrendDirection = 'up' | 'down' | 'stable';
export interface Trend { direction: TrendDirection; value: number; period: string; }
export interface MetricThresholds {
  min: number;
  max: number;
  critical: number;
  good?: { min: number; max: number };
  warning?: { min: number; max: number };
}

export interface StatCardProps {
  type: MetricType;
  value: number;
  label?: string;
  unit?: string;
  trend?: Trend;
  quality?: SignalQuality | 'good' | 'warning' | 'critical';
  duration?: string;
  thresholds?: MetricThresholds;
  variant?: 'default' | 'compact' | 'minimal';
  colorize?: boolean;
  className?: string;
}
