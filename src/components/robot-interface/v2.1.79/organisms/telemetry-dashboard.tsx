/**
 * TelemetryDashboard Component - RaaS UX Kit v2.1.79
 * Data visualization panel for real-time and historical telemetry streams
 */

import React, { useState, useCallback, useMemo } from 'react';
import { StatCard } from '../../molecules/StatCard';
import { Button } from '../../atoms/Button';
import { Icon } from '../../atoms/Icon';
import {
  TelemetryDashboardProps,
  TelemetryStream,
  TimeRange,
  ExportFormat,
  ChartConfig,
} from '../../types/telemetry';

// ============================================
// Preset Time Ranges
// ============================================

const PRESET_RANGES: TimeRange[] = [
  { label: '1H', value: '1h', duration: 3600000 },
  { label: '6H', value: '6h', duration: 21600000 },
  { label: '24H', value: '24h', duration: 86400000 },
  { label: '1D', value: '1d', duration: 86400000 },
  { label: '7D', value: '7d', duration: 604800000 },
  { label: '30D', value: '30d', duration: 2592000000 },
];

// ============================================
// Chart Component (Simplified placeholder for actual chart library)
// ============================================

interface ChartProps {
  config: ChartConfig;
  data: TelemetryStream[];
  timeRange: TimeRange;
  height?: number;
}

const Chart: React.FC<ChartProps> = ({ config, data, timeRange, height = 200 }) => {
  // This is a placeholder - in production, integrate with a chart library
  // like Recharts, Chart.js, or D3
  return (
    <div
      className="relative w-full"
      style={{ height }}
      role="img"
      aria-label={config.title}
    >
      {/* Chart Header */}
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between p-2 border-b border-[var(--color-border)]">
        <h4 className="text-sm font-semibold text-[var(--color-text-primary)]">
          {config.title}
        </h4>
        {config.yAxis && (
          <span className="text-xs text-[var(--color-text-tertiary)]">
            {config.yAxis.label}
          </span>
        )}
      </div>

      {/* Chart Area Placeholder */}
      <div className="absolute top-10 left-0 right-0 bottom-0 flex items-center justify-center bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
        <div className="text-center text-[var(--color-text-tertiary)]">
          <Icon size="xl" color="secondary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M3 3v18h18" strokeWidth="2" />
              <path d="M18 9l-5 5-4-4-3 3" strokeWidth="2" />
            </svg>
          </Icon>
          <p className="text-xs mt-2">Chart: {config.type}</p>
          <p className="text-[10px]">Time range: {timeRange.label}</p>
        </div>
      </div>
    </div>
  );
};

// ============================================
// Export Format Selector
// ============================================

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  onExport: (format: ExportFormat) => void;
}

const ExportDialog: React.FC<ExportDialogProps> = ({ open, onClose, onExport }) => {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="Export data"
      onClick={onClose}
    >
      <div
        className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-6 max-w-md w-full mx-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
          Export Telemetry Data
        </h3>

        <div className="grid gap-3">
          <Button
            variant="outline"
            size="lg"
            onClick={() => onExport('csv')}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" strokeWidth="2" />
                <polyline points="14,2 14,8 20,8" strokeWidth="2" />
                <line x1="16" y1="13" x2="8" y2="13" strokeWidth="2" />
                <line x1="16" y1="17" x2="8" y2="17" strokeWidth="2" />
              </svg>
            }
          >
            CSV (Spreadsheet)
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={() => onExport('json')}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <polyline points="16,18 22,12 16,6" strokeWidth="2" />
                <polyline points="8,6 2,12 8,18" strokeWidth="2" />
              </svg>
            }
          >
            JSON (Data interchange)
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={() => onExport('pdf')}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" strokeWidth="2" />
                <polyline points="14,2 14,8 20,8" strokeWidth="2" />
                <line x1="12" y1="18" x2="12" y2="12" strokeWidth="2" />
                <line x1="9" y1="15" x2="15" y2="15" strokeWidth="2" />
              </svg>
            }
          >
            PDF Report
          </Button>
        </div>

        <div className="mt-6 flex justify-end">
          <Button variant="ghost" size="md" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// Main Component
// ============================================

export const TelemetryDashboard: React.FC<TelemetryDashboardProps> = ({
  robotId,
  streams = [],
  defaultRange = PRESET_RANGES[1], // 6H default
  availableRanges = PRESET_RANGES,
  onRangeChange,
  charts = [],
  layout = 'grid-4',
  customLayout,
  onExport,
  exportEnabled = true,
  liveMode = true,
  refreshInterval = 2000,
  onLiveToggle,
  className = '',
}) => {
  const [selectedRange, setSelectedRange] = useState<TimeRange>(defaultRange);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [isLive, setIsLive] = useState(liveMode);

  // Handle range change
  const handleRangeChange = useCallback((range: TimeRange) => {
    setSelectedRange(range);
    onRangeChange?.(range);
  }, [onRangeChange]);

  // Handle export
  const handleExport = useCallback((format: ExportFormat) => {
    if (onExport) {
      // In production, fetch actual telemetry data
      const mockData = {
        robotId,
        streams,
        startTime: new Date(Date.now() - selectedRange.duration),
        endTime: new Date(),
        pointCount: streams.reduce((acc, s) => acc + s.data.length, 0),
      };
      onExport(format, mockData);
    }
    setShowExportDialog(false);
  }, [onExport, robotId, streams, selectedRange]);

  // Toggle live mode
  const toggleLiveMode = useCallback(() => {
    const newLiveMode = !isLive;
    setIsLive(newLiveMode);
    onLiveToggle?.(newLiveMode);
  }, [isLive, onLiveToggle]);

  // Grid layout classes
  const gridLayoutClasses = useMemo(() => {
    switch (layout) {
      case 'single':
        return 'grid-cols-1';
      case 'grid-2':
        return 'grid-cols-1 md:grid-cols-2';
      case 'grid-4':
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      case 'custom':
        return ''; // Custom layout handled separately
      default:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
    }
  }, [layout]);

  // Get charts to display
  const displayCharts = charts.length > 0 ? charts : streams.map((stream) => ({
    type: stream.type as ChartConfig['type'],
    title: stream.name,
    streamId: stream.id,
    yAxis: {
      label: stream.unit,
      min: stream.min,
      max: stream.max,
    },
  }));

  return (
    <div
      className={`
        flex flex-col gap-4
        bg-[var(--color-surface)]
        border border-[var(--color-border)]
        rounded-[var(--radius-lg)]
        p-4
        ${className}
      `}
      role="region"
      aria-label="Telemetry dashboard"
    >
      {/* Header with Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Telemetry Dashboard
        </h2>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Time Range Selector */}
          <div className="flex items-center gap-1 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)] p-1">
            {availableRanges.slice(0, 3).map((range) => (
              <button
                key={range.value}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-[var(--radius-sm)]
                  transition-all duration-150
                  ${selectedRange.value === range.value
                    ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                  }
                `}
                onClick={() => handleRangeChange(range)}
                aria-pressed={selectedRange.value === range.value}
              >
                {range.label}
              </button>
            ))}
          </div>

          {/* Secondary Range Selector */}
          <div className="flex items-center gap-1 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)] p-1">
            {availableRanges.slice(3, 6).map((range) => (
              <button
                key={range.value}
                className={`
                  px-3 py-1.5 text-xs font-medium rounded-[var(--radius-sm)]
                  transition-all duration-150
                  ${selectedRange.value === range.value
                    ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                  }
                `}
                onClick={() => handleRangeChange(range)}
                aria-pressed={selectedRange.value === range.value}
              >
                {range.label}
              </button>
            ))}
          </div>

          {/* Live Mode Toggle */}
          {onLiveToggle && (
            <button
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-md)]
                text-xs font-medium transition-all duration-150
                ${isLive
                  ? 'bg-[var(--color-success-subtle)] text-[var(--color-success)]'
                  : 'bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)]'
                }
              `}
              onClick={toggleLiveMode}
              aria-pressed={isLive}
            >
              <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-[var(--color-success)] animate-pulse' : 'bg-[var(--color-text-tertiary)]'}`} />
              {isLive ? 'Live' : 'Paused'}
            </button>
          )}

          {/* Export Button */}
          {exportEnabled && onExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowExportDialog(true)}
              icon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" strokeWidth="2" />
                  <polyline points="7,10 12,15 17,10" strokeWidth="2" />
                  <line x1="12" y1="15" x2="12" y2="3" strokeWidth="2" />
                </svg>
              }
            >
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Charts Grid */}
      <div className={`grid gap-4 ${gridLayoutClasses}`}>
        {displayCharts.map((chart, index) => (
          <div
            key={chart.title || index}
            className={`
              bg-[var(--color-surface)]
              border border-[var(--color-border)]
              rounded-[var(--radius-lg)]
              p-4
              ${layout === 'custom' && customLayout?.cells[index]?.colspan
                ? `col-span-${customLayout.cells[index].colspan}`
                : ''}
            `}
          >
            <Chart
              config={chart}
              data={streams}
              timeRange={selectedRange}
              height={layout === 'single' ? 400 : 200}
            />
          </div>
        ))}
      </div>

      {/* Stream Summary Cards */}
      {streams.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-[var(--color-border)]">
          {streams.slice(0, 4).map((stream) => {
            const latestValue = stream.data.length > 0
              ? stream.data[stream.data.length - 1].value
              : 0;

            return (
              <div
                key={stream.id}
                className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]"
              >
                <span className="text-xs text-[var(--color-text-secondary)] mb-1">
                  {stream.name}
                </span>
                <span className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {typeof latestValue === 'number'
                    ? latestValue.toFixed(2)
                    : latestValue}
                  {stream.unit && (
                    <span className="ml-1 text-sm text-[var(--color-text-tertiary)]">
                      {stream.unit}
                    </span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Export Dialog */}
      <ExportDialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        onExport={handleExport}
      />
    </div>
  );
};

export default TelemetryDashboard;
