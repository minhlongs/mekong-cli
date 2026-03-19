/**
 * useMissionControl Hook - RaaS UX Kit v2.1.79
 * Robot mission management with WebSocket real-time updates
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Mission,
  MissionStatus,
  MissionProgress,
  MissionLog,
  MissionWebSocketEvent,
  QueuedAction,
  UseMissionControlOptions,
  UseMissionControlReturn,
} from '../types/mission';

export interface UseMissionControlExtendedOptions extends UseMissionControlOptions {
  enableWebSocket?: boolean;
  wsUrl?: string;
  autoReconnect?: boolean;
  offlineSupport?: boolean;
}

export const useMissionControl = ({
  robotId,
  missionId,
  autoConnect = true,
  refreshInterval = 5000,
  enableWebSocket = false,
  wsUrl,
  autoReconnect = true,
  offlineSupport = false,
}: UseMissionControlExtendedOptions): UseMissionControlReturn => {
  const [activeMission, setActiveMission] = useState<Mission | null>(null);
  const [progress, setProgress] = useState<MissionProgress>({
    percentage: 0,
    currentWaypoint: 0,
    totalWaypoints: 0,
    elapsedSeconds: 0,
    completedWaypoints: 0,
    failedWaypoints: 0,
    skippedWaypoints: 0,
  });
  const [logs, setLogs] = useState<MissionLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [queuedActions, setQueuedActions] = useState<QueuedAction[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch mission data
  const fetchMissionData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // TODO: Replace with actual API endpoint
      const response = await fetch(`/api/robots/${robotId}/mission`);

      if (!response.ok) {
        if (response.status === 404) {
          setActiveMission(null);
          return;
        }
        throw new Error(`Failed to fetch mission: ${response.status}`);
      }

      const data: Mission = await response.json();
      setActiveMission(data);
      setIsPlaying(data.status === 'running');
      setIsPaused(data.status === 'paused');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [robotId]);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || !wsUrl) return;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log(`Mission control WebSocket connected to ${wsUrl}`);
      };

      ws.onmessage = (event) => {
        try {
          const eventData: MissionWebSocketEvent = JSON.parse(event.data);

          if (eventData.robotId !== robotId) return;

          // Handle different event types
          switch (eventData.type) {
            case 'mission_started':
            case 'mission_resumed':
              setIsPlaying(true);
              setIsPaused(false);
              break;

            case 'mission_paused':
              setIsPlaying(false);
              setIsPaused(true);
              break;

            case 'mission_completed':
            case 'mission_aborted':
            case 'mission_failed':
              setIsPlaying(false);
              setIsPaused(false);
              break;

            case 'progress_update':
              if (eventData.data) {
                setProgress(eventData.data as MissionProgress);
              }
              break;

            case 'log_entry':
              if (eventData.data) {
                setLogs((prev) => [...prev, eventData.data as MissionLog]);
              }
              break;
          }
        } catch (err) {
          console.error('Failed to parse mission event:', err);
        }
      };

      ws.onerror = () => {
        setIsConnected(false);
        setError('Mission control WebSocket error');
      };

      ws.onclose = () => {
        setIsConnected(false);

        if (autoReconnect) {
          setTimeout(connectWebSocket, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [enableWebSocket, wsUrl, robotId, autoReconnect]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Mission actions
  const launchMission = useCallback(
    async (missionIdToLaunch: string) => {
      try {
        // TODO: Replace with actual API endpoint
        const response = await fetch(`/api/robots/${robotId}/missions/${missionIdToLaunch}/launch`, {
          method: 'POST',
        });

        if (!response.ok) {
          throw new Error(`Failed to launch mission: ${response.status}`);
        }

        setIsPlaying(true);
        setIsPaused(false);
        setError(null);

        // Add to queued actions if offline
        if (!isConnected && offlineSupport) {
          setQueuedActions((prev) => [
            ...prev,
            {
              id: `queued-${Date.now()}`,
              type: 'launch',
              missionId: missionIdToLaunch,
              queuedAt: new Date(),
              status: 'pending',
              retryCount: 0,
            },
          ]);
        }
      } catch (err) {
        throw err;
      }
    },
    [robotId, isConnected, offlineSupport]
  );

  const pauseMission = useCallback(async () => {
    if (!missionId && !activeMission?.id) return;

    try {
      const targetMissionId = missionId || activeMission?.id;
      const response = await fetch(`/api/robots/${robotId}/missions/${targetMissionId}/pause`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to pause mission: ${response.status}`);
      }

      setIsPlaying(false);
      setIsPaused(true);
    } catch (err) {
      throw err;
    }
  }, [robotId, missionId, activeMission]);

  const resumeMission = useCallback(async () => {
    if (!missionId && !activeMission?.id) return;

    try {
      const targetMissionId = missionId || activeMission?.id;
      const response = await fetch(`/api/robots/${robotId}/missions/${targetMissionId}/resume`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to resume mission: ${response.status}`);
      }

      setIsPlaying(true);
      setIsPaused(false);
    } catch (err) {
      throw err;
    }
  }, [robotId, missionId, activeMission]);

  const abortMission = useCallback(async () => {
    if (!missionId && !activeMission?.id) return;

    try {
      const targetMissionId = missionId || activeMission?.id;
      const response = await fetch(`/api/robots/${robotId}/missions/${targetMissionId}/abort`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to abort mission: ${response.status}`);
      }

      setIsPlaying(false);
      setIsPaused(false);
    } catch (err) {
      throw err;
    }
  }, [robotId, missionId, activeMission]);

  // Log management
  const exportLogs = useCallback(
    (format: 'txt' | 'json'): void => {
      let content: string;
      let mimeType: string;
      let extension: string;

      if (format === 'json') {
        content = JSON.stringify(logs, null, 2);
        mimeType = 'application/json';
        extension = 'json';
      } else {
        content = logs
          .map(
            (log) =>
              `[${new Date(log.timestamp).toISOString()}] [${log.level.toUpperCase()}] ${
                log.source ? `${log.source}: ` : ''
              }${log.message}`
          )
          .join('\n');
        mimeType = 'text/plain';
        extension = 'txt';
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mission-logs-${robotId}-${Date.now()}.${extension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    [logs, robotId]
  );

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Initial connection
  useEffect(() => {
    if (autoConnect) {
      fetchMissionData();

      if (enableWebSocket) {
        connectWebSocket();
      }

      refreshIntervalRef.current = setInterval(fetchMissionData, refreshInterval);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
      disconnectWebSocket();
    };
  }, [autoConnect, fetchMissionData, enableWebSocket, connectWebSocket, disconnectWebSocket, refreshInterval]);

  return useMemo(
    () => ({
      activeMission,
      progress,
      logs,
      isConnected,
      isPlaying,
      isPaused,
      isLoading,
      error,
      launchMission,
      pauseMission,
      resumeMission,
      abortMission,
      exportLogs,
      clearLogs,
    }),
    [
      activeMission,
      progress,
      logs,
      isConnected,
      isPlaying,
      isPaused,
      isLoading,
      error,
      launchMission,
      pauseMission,
      resumeMission,
      abortMission,
      exportLogs,
      clearLogs,
    ]
  );
};

export default useMissionControl;
