/**
 * useTelemetry Hook - RaaS UX Kit v2.1.79
 * Real-time telemetry data streaming and chart management
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { TelemetryStream, TimeSeriesPoint, ChartConfig } from '../types/telemetry';

export interface UseTelemetryOptions {
  robotId: string;
  streams?: TelemetryStream[];
  pollingInterval?: number;
  enableWebSocket?: boolean;
  wsUrl?: string;
  historySize?: number;
}

export interface UseTelemetryReturn {
  streams: TelemetryStream[];
  data: Record<string, TimeSeriesPoint[]>;
  charts: ChartConfig[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  addStream: (stream: TelemetryStream) => void;
  removeStream: (streamId: string) => void;
  updateStream: (streamId: string, updates: Partial<TelemetryStream>) => void;
  clearData: () => void;
  exportData: (format: 'csv' | 'json') => string;
}

export const useTelemetry = ({
  robotId,
  streams = [],
  pollingInterval = 1000,
  enableWebSocket = false,
  wsUrl,
  historySize = 100,
}: UseTelemetryOptions): UseTelemetryReturn => {
  const [streamsState, setStreamsState] = useState<TelemetryStream[]>(streams);
  const [data, setData] = useState<Record<string, TimeSeriesPoint[]>>({});
  const [charts, setCharts] = useState<ChartConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setCharts(
      streamsState.map((stream) => ({
        id: `chart-${stream.id}`,
        title: stream.name,
        type: stream.displayType || 'line',
        streams: [stream.id],
        xAxis: { key: 'timestamp', label: 'Time', type: 'time' },
        yAxis: { key: 'value', label: stream.unit || '', min: stream.thresholds?.min, max: stream.thresholds?.max },
        showLegend: true,
        showTooltip: true,
        smooth: true,
      }))
    );
  }, [streamsState]);

  const fetchTelemetry = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`/api/robots/${robotId}/telemetry`);
      if (!response.ok) throw new Error(`Failed to fetch telemetry: ${response.status}`);
      const streamData: Record<string, number> = await response.json();

      setData((prev) => {
        const newData = { ...prev };
        const timestamp = Date.now();
        streamsState.forEach((stream) => {
          const prevSeries = newData[stream.id] || [];
          newData[stream.id] = [
            ...prevSeries.slice(-(historySize - 1)),
            { timestamp, value: streamData[stream.id] ?? 0, metadata: { robotId, streamId: stream.id } },
          ];
        });
        return newData;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [robotId, streamsState, historySize]);

  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || !wsUrl) return;
    try {
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => setIsStreaming(true);
      ws.onmessage = (event) => {
        try {
          const td = JSON.parse(event.data);
          if (td.robotId !== robotId || !td.streamId || td.value === undefined) return;
          const timestamp = td.timestamp || Date.now();
          setData((prev) => ({
            ...prev,
            [td.streamId]: [
              ...(prev[td.streamId] || []).slice(-(historySize - 1)),
              { timestamp, value: td.value, metadata: { robotId, streamId: td.streamId } },
            ],
          }));
        } catch { /* ignore malformed frame */ }
      };
      ws.onerror = () => { setIsStreaming(false); setError('Telemetry WebSocket error'); };
      ws.onclose = () => setIsStreaming(false);
      wsRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [enableWebSocket, wsUrl, robotId, historySize]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
  }, []);

  const addStream = useCallback((stream: TelemetryStream) => {
    setStreamsState((prev) => [...prev, stream]);
    setData((prev) => ({ ...prev, [stream.id]: [] }));
  }, []);

  const removeStream = useCallback((streamId: string) => {
    setStreamsState((prev) => prev.filter((s) => s.id !== streamId));
    setData((prev) => { const next = { ...prev }; delete next[streamId]; return next; });
  }, []);

  const updateStream = useCallback((streamId: string, updates: Partial<TelemetryStream>) => {
    setStreamsState((prev) => prev.map((s) => (s.id === streamId ? { ...s, ...updates } : s)));
  }, []);

  const clearData = useCallback(() => setData({}), []);

  const exportData = useCallback(
    (format: 'csv' | 'json'): string => {
      if (format === 'json') return JSON.stringify(data, null, 2);
      const streamIds = Object.keys(data);
      if (streamIds.length === 0) return '';
      const headers = ['timestamp', ...streamIds];
      const rows = data[streamIds[0]]?.map((pt) => [
        pt.timestamp,
        ...streamIds.map((id) => data[id]?.find((p) => p.timestamp === pt.timestamp)?.value ?? ''),
      ]) ?? [];
      return [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    },
    [data]
  );

  useEffect(() => {
    fetchTelemetry();
    pollIntervalRef.current = setInterval(fetchTelemetry, pollingInterval);
    if (enableWebSocket) connectWebSocket();
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      disconnectWebSocket();
    };
  }, [fetchTelemetry, pollingInterval, enableWebSocket, connectWebSocket, disconnectWebSocket]);

  return useMemo(
    () => ({ streams: streamsState, data, charts, isLoading, isStreaming, error, addStream, removeStream, updateStream, clearData, exportData }),
    [streamsState, data, charts, isLoading, isStreaming, error, addStream, removeStream, updateStream, clearData, exportData]
  );
};

export default useTelemetry;
