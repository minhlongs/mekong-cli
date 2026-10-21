/**
 * TelemetryDashboard Component - RaaS UX Kit v2.1.79
 * Data visualization panel for real-time and historical telemetry streams
 */
import React, { useState, useCallback, useMemo } from 'react';
import { Button } from '../atoms/Button';
import { Icon } from '../atoms/Icon';
import { TimeRange } from '../types/robot';
import { TelemetryDashboardProps, TelemetryStream, ExportFormat, ChartConfig } from '../types/telemetry';

const PRESET_RANGES: TimeRange[] = [
  { label: '1H', value: '1h', duration: 3600000 }, { label: '6H', value: '6h', duration: 21600000 },
  { label: '24H', value: '24h', duration: 86400000 }, { label: '1D', value: '1d', duration: 86400000 },
  { label: '7D', value: '7d', duration: 604800000 }, { label: '30D', value: '30d', duration: 2592000000 },
];

const Chart: React.FC<{ config: ChartConfig; data: TelemetryStream[]; timeRange: TimeRange; height?: number }> = ({
  config, timeRange, height = 200,
}) => (
  <div className="relative w-full" style={{ height }} role="img" aria-label={config.title}>
    <div className="absolute top-0 left-0 right-0 flex items-center justify-between p-2 border-b border-[var(--color-border)]">
      <h4 className="text-sm font-semibold text-[var(--color-text-primary)]">{config.title}</h4>
      {config.yAxis && <span className="text-xs text-[var(--color-text-tertiary)]">{config.yAxis.label}</span>}
    </div>
    <div className="absolute top-10 left-0 right-0 bottom-0 flex items-center justify-center bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
      <div className="text-center text-[var(--color-text-tertiary)]">
        <Icon size="xl" color="secondary"><path d="M3 3v18h18M18 9l-5 5-4-4-3 3" strokeWidth="2" /></Icon>
        <p className="text-xs mt-2">Chart: {config.type}</p>
        <p className="text-[10px]">Time range: {timeRange.label}</p>
      </div>
    </div>
  </div>
);

const ExportDialog: React.FC<{ open: boolean; onClose: () => void; onExport: (format: ExportFormat) => void }> = ({
  open, onClose, onExport,
}) => {
  if (!open) return null;
  const options: { format: ExportFormat; label: string; path: string }[] = [
    { format: 'csv', label: 'CSV (Spreadsheet)', path: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM16 13H8M16 17H8' },
    { format: 'json', label: 'JSON (Data interchange)', path: 'M16 18l6-6-6-6M8 6l-6 6 6 6' },
    { format: 'pdf', label: 'PDF Report', path: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM12 18v-6M9 15h6' },
  ];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Export data" onClick={onClose}>
      <div className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-6 max-w-md w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">Export Telemetry Data</h3>
        <div className="grid gap-3">
          {options.map((opt) => (
            <Button
              key={opt.format} variant="outline" size="lg" onClick={() => onExport(opt.format)}
              icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d={opt.path} strokeWidth="2" /></svg>}
            >
              {opt.label}
            </Button>
          ))}
        </div>
        <div className="mt-6 flex justify-end"><Button variant="ghost" size="md" onClick={onClose}>Cancel</Button></div>
      </div>
    </div>
  );
};

export const TelemetryDashboard: React.FC<TelemetryDashboardProps> = ({
  robotId, streams = [], defaultRange = PRESET_RANGES[1], availableRanges = PRESET_RANGES, onRangeChange,
  charts = [], layout = 'grid-4', customLayout, onExport, exportEnabled = true, liveMode = true, onLiveToggle, className = '',
}) => {
  const [selectedRange, setSelectedRange] = useState<TimeRange>(defaultRange);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [isLive, setIsLive] = useState(liveMode);

  const handleRangeChange = useCallback((range: TimeRange) => { setSelectedRange(range); onRangeChange?.(range); }, [onRangeChange]);
  const handleExport = useCallback((format: ExportFormat) => {
    onExport?.(format, {
      robotId, streams, startTime: new Date(Date.now() - selectedRange.duration),
      endTime: new Date(), pointCount: streams.reduce((acc, s) => acc + s.data.length, 0),
    });
    setShowExportDialog(false);
  }, [onExport, robotId, streams, selectedRange]);

  const toggleLiveMode = useCallback(() => { const next = !isLive; setIsLive(next); onLiveToggle?.(next); }, [isLive, onLiveToggle]);
  const gridLayoutClasses = useMemo(() => (layout === 'single' ? 'grid-cols-1' : layout === 'grid-2' ? 'grid-cols-1 md:grid-cols-2' : layout === 'custom' ? '' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'), [layout]);
  const displayCharts = charts.length > 0 ? charts : streams.map((s) => ({ type: s.type as ChartConfig['type'], title: s.name, streamId: s.id, yAxis: { label: s.unit, min: s.min, max: s.max } }));

  const renderRangeGroup = (group: TimeRange[]) => (
    <div className="flex items-center gap-1 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)] p-1">
      {group.map((range) => (
        <button
          key={range.value} type="button" aria-pressed={selectedRange.value === range.value} onClick={() => handleRangeChange(range)}
          className={`px-3 py-1.5 text-xs font-medium rounded-[var(--radius-sm)] transition-all duration-150 cursor-pointer ${
            selectedRange.value === range.value ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className={`flex flex-col gap-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 ${className}`} role="region" aria-label="Telemetry dashboard">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Telemetry Dashboard</h2>
        <div className="flex items-center gap-2 flex-wrap">
          {renderRangeGroup(availableRanges.slice(0, 3))}
          {renderRangeGroup(availableRanges.slice(3, 6))}
          {onLiveToggle && (
            <button
              type="button" onClick={toggleLiveMode} aria-pressed={isLive}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[var(--radius-md)] text-xs font-medium transition-all duration-150 cursor-pointer ${
                isLive ? 'bg-[var(--color-success-subtle)] text-[var(--color-success)]' : 'bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)]'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-[var(--color-success)] animate-pulse' : 'bg-[var(--color-text-tertiary)]'}`} />
              {isLive ? 'Live' : 'Paused'}
            </button>
          )}
          {exportEnabled && onExport && (
            <Button
              variant="outline" size="sm" onClick={() => setShowExportDialog(true)}
              icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" strokeWidth="2" /></svg>}
            >
              Export
            </Button>
          )}
        </div>
      </div>

      <div className={`grid gap-4 ${gridLayoutClasses}`}>
        {displayCharts.map((chart, index) => (
          <div key={chart.title || index} className={`bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)] p-4 ${layout === 'custom' && customLayout?.cells[index]?.colspan ? `col-span-${customLayout.cells[index].colspan}` : ''}`}>
            <Chart config={chart} data={streams} timeRange={selectedRange} height={layout === 'single' ? 400 : 200} />
          </div>
        ))}
      </div>

      {streams.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-[var(--color-border)]">
          {streams.slice(0, 4).map((stream) => {
            const latestValue = stream.data.length > 0 ? stream.data[stream.data.length - 1].value : 0;
            return (
              <div key={stream.id} className="flex flex-col p-3 bg-[var(--color-surface-tertiary)] rounded-[var(--radius-md)]">
                <span className="text-xs text-[var(--color-text-secondary)] mb-1">{stream.name}</span>
                <span className="text-lg font-semibold text-[var(--color-text-primary)] tabular-nums">
                  {typeof latestValue === 'number' ? latestValue.toFixed(2) : latestValue}
                  {stream.unit && <span className="ml-1 text-sm text-[var(--color-text-tertiary)]">{stream.unit}</span>}
                </span>
              </div>
            );
          })}
        </div>
      )}

      <ExportDialog open={showExportDialog} onClose={() => setShowExportDialog(false)} onExport={handleExport} />
    </div>
  );
};

export default TelemetryDashboard;
