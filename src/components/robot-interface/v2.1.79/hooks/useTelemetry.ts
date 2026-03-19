/**
 * useTelemetry Hook - RaaS UX Kit v2.1.79
 * Real-time telemetry data streaming and chart management
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  TelemetryStream,
  TelemetryStreamType,
  TimeSeriesPoint,
  ChartConfig,
} from '../types/telemetry';

export interface UseTelemetryOptions {
  robotId: string;
  streams?: TelemetryStream[];
  pollingInterval?: number; // ms, default: 1000
  enableWebSocket?: boolean;
  wsUrl?: string;
  historySize?: number; // max data points, default: 100
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

  // Initialize streams and charts
  useEffect(() => {
    // Create chart configs for each stream
    const chartConfigs: ChartConfig[] = streamsState.map((stream) => ({
      id: `chart-${stream.id}`,
      title: stream.name,
      type: stream.displayType || 'line',
      streams: [stream.id],
      xAxis: {
        key: 'timestamp',
        label: 'Time',
        type: 'time',
      },
      yAxis: {
        key: 'value',
        label: stream.unit || '',
        min: stream.thresholds?.min,
        max: stream.thresholds?.max,
      },
      showLegend: true,
      showTooltip: true,
      smooth: true,
    }));

    setCharts(chartConfigs);
  }, [streamsState]);

  // Fetch telemetry data
  const fetchTelemetry = useCallback(async () => {
    try {
      setError(null);

      // TODO: Replace with actual API endpoint
      const response = await fetch(`/api/robots/${robotId}/telemetry`);

      if (!response.ok) {
        throw new Error(`Failed to fetch telemetry: ${response.status}`);
      }

      const streamData: Record<string, number> = await response.json();

      setData((prev) => {
        const newData = { ...prev };
        const timestamp = Date.now();

        streamsState.forEach((stream) => {
          const value = streamData[stream.id] ?? 0;

          if (!newData[stream.id]) {
            newData[stream.id] = [];
          }

          newData[stream.id] = [
            ...newData[stream.id].slice(-(historySize - 1)),
            {
              timestamp,
              value,
              metadata: {
                robotId,
                streamId: stream.id,
              },
            },
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

  // Connect to WebSocket for real-time updates
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || !wsUrl) return;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsStreaming(true);
        console.log(`Telemetry WebSocket connected to ${wsUrl}`);
      };

      ws.onmessage = (event) => {
        try {
          const telemetryData = JSON.parse(event.data);

          if (telemetryData.robotId !== robotId) return;

          const timestamp = telemetryData.timestamp || Date.now();

          setData((prev) => {
            const newData = { ...prev };

            if (telemetryData.streamId && telemetryData.value !== undefined) {
              if (!newData[telemetryData.streamId]) {
                newData[telemetryData.streamId] = [];
              }

              newData[telemetryData.streamId] = [
                ...newData[telemetryData.streamId].slice(-(historySize - 1)),
                {
                  timestamp,
                  value: telemetryData.value,
                  metadata: {
                    robotId,
                    streamId: telemetryData.streamId,
                  },
                },
              ];
            }

            return newData;
          });
        } catch (err) {
          console.error('Failed to parse telemetry data:', err);
        }
      };

      ws.onerror = () => {
        setIsStreaming(false);
        setError('Telemetry WebSocket error');
      };

      ws.onclose = () => {
        setIsStreaming(false);
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [enableWebSocket, wsUrl, robotId, historySize]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Stream management
  const addStream = useCallback((stream: TelemetryStream) => {
    setStreamsState((prev) => [...prev, stream]);
    setData((prev) => ({ ...prev, [stream.id]: [] }));
  }, []);

  const removeStream = useCallback((streamId: string) => {
    setStreamsState((prev) => prev.filter((s) => s.id !== streamId));
    setData((prev) => {
      const newData = { ...prev };
      delete newData[streamId];
      return newData;
    });
  }, []);

  const updateStream = useCallback(
    (streamId: string, updates: Partial<TelemetryStream>) => {
      setStreamsState((prev) =>
        prev.map((stream) =>
          stream.id === streamId ? { ...stream, ...updates } : stream
        )
      );
    },
    []
  );

  const clearData = useCallback(() => {
    setData({});
  }, []);

  // Export data
  const exportData = useCallback(
    (format: 'csv' | 'json'): string => {
      if (format === 'json') {
        return JSON.stringify(data, null, 2);
      }

      // CSV export
      const streamIds = Object.keys(data);
      if (streamIds.length === 0) return '';

      const headers = ['timestamp', ...streamIds];
      const rows = data[streamIds[0]]?.map((point) => [
        point.timestamp,
        ...streamIds.map((id) => data[id]?.find((p) => p.timestamp === point.timestamp)?.value ?? ''),
      ]) ?? [];

      return [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
    },
    [data]
  );

  // Initial fetch and polling
  useEffect(() => {
    fetchTelemetry();

    pollIntervalRef.current = setInterval(fetchTelemetry, pollingInterval);

    if (enableWebSocket) {
      connectWebSocket();
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      disconnectWebSocket();
    };
  }, [fetchTelemetry, pollingInterval, enableWebSocket, connectWebSocket, disconnectWebSocket]);

  return useMemo(
    () => ({
      streams: streamsState,
      data,
      charts,
      isLoading,
      isStreaming,
      error,
      addStream,
      removeStream,
      updateStream,
      clearData,
      exportData,
    }),
    [
      streamsState,
      data,
      charts,
      isLoading,
      isStreaming,
      error,
      addStream,
      removeStream,
      updateStream,
      clearData,
      exportData,
    ]
  );
};

export default useTelemetry;
