/**
 * useMissionControl Hook - RaaS UX Kit v2.1.79
 * Robot mission management with WebSocket real-time updates
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Mission,
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
    percentage: 0, currentWaypoint: 0, totalWaypoints: 0, elapsedSeconds: 0,
    completedWaypoints: 0, failedWaypoints: 0, skippedWaypoints: 0,
  });
  const [logs, setLogs] = useState<MissionLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [, setQueuedActions] = useState<QueuedAction[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchMissionData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`/api/robots/${robotId}/mission`);
      if (!response.ok) {
        if (response.status === 404) { setActiveMission(null); return; }
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

  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || !wsUrl) return;
    try {
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => setIsConnected(true);
      ws.onmessage = (event) => {
        try {
          const eventData: MissionWebSocketEvent = JSON.parse(event.data);
          if (eventData.robotId !== robotId) return;
          if (eventData.type === 'mission_started' || eventData.type === 'mission_resumed') {
            setIsPlaying(true); setIsPaused(false);
          } else if (eventData.type === 'mission_paused') {
            setIsPlaying(false); setIsPaused(true);
          } else if (['mission_completed', 'mission_aborted', 'mission_failed'].includes(eventData.type)) {
            setIsPlaying(false); setIsPaused(false);
          } else if (eventData.type === 'progress_update' && eventData.data) {
            setProgress(eventData.data as MissionProgress);
          } else if (eventData.type === 'log_entry' && eventData.data) {
            setLogs((prev) => [...prev, eventData.data as MissionLog]);
          }
        } catch { /* ignore malformed frame */ }
      };
      ws.onerror = () => { setIsConnected(false); setError('Mission control WebSocket error'); };
      ws.onclose = () => {
        setIsConnected(false);
        if (autoReconnect) setTimeout(connectWebSocket, 3000);
      };
      wsRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [enableWebSocket, wsUrl, robotId, autoReconnect]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
  }, []);

  const postMissionAction = useCallback(
    async (action: 'launch' | 'pause' | 'resume' | 'abort', explicitMissionId?: string) => {
      const targetId = explicitMissionId || missionId || activeMission?.id;
      if (!targetId) return;
      const response = await fetch(`/api/robots/${robotId}/missions/${targetId}/${action}`, { method: 'POST' });
      if (!response.ok) throw new Error(`Failed to ${action} mission: ${response.status}`);
      if (action === 'launch' || action === 'resume') { setIsPlaying(true); setIsPaused(false); setError(null); }
      if (action === 'pause') { setIsPlaying(false); setIsPaused(true); }
      if (action === 'abort') { setIsPlaying(false); setIsPaused(false); }
      if (action === 'launch' && !isConnected && offlineSupport) {
        setQueuedActions((prev) => [
          ...prev,
          { id: `queued-${Date.now()}`, type: 'launch', missionId: targetId, queuedAt: new Date(), status: 'pending', retryCount: 0 },
        ]);
      }
    },
    [robotId, missionId, activeMission, isConnected, offlineSupport]
  );

  const launchMission = useCallback((id: string) => postMissionAction('launch', id), [postMissionAction]);
  const pauseMission = useCallback(() => postMissionAction('pause'), [postMissionAction]);
  const resumeMission = useCallback(() => postMissionAction('resume'), [postMissionAction]);
  const abortMission = useCallback(() => postMissionAction('abort'), [postMissionAction]);

  const exportLogs = useCallback(
    (format: 'txt' | 'json'): void => {
      const content = format === 'json'
        ? JSON.stringify(logs, null, 2)
        : logs.map((l) => `[${new Date(l.timestamp).toISOString()}] [${l.level.toUpperCase()}] ${l.source ? `${l.source}: ` : ''}${l.message}`).join('\n');
      const url = URL.createObjectURL(new Blob([content], { type: format === 'json' ? 'application/json' : 'text/plain' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `mission-logs-${robotId}-${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    [logs, robotId]
  );

  const clearLogs = useCallback(() => setLogs([]), []);

  useEffect(() => {
    if (autoConnect) {
      fetchMissionData();
      if (enableWebSocket) connectWebSocket();
      refreshIntervalRef.current = setInterval(fetchMissionData, refreshInterval);
    }
    return () => {
      if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current);
      disconnectWebSocket();
    };
  }, [autoConnect, fetchMissionData, enableWebSocket, connectWebSocket, disconnectWebSocket, refreshInterval]);

  return useMemo(
    () => ({ activeMission, progress, logs, isConnected, isPlaying, isPaused, isLoading, error, launchMission, pauseMission, resumeMission, abortMission, exportLogs, clearLogs }),
    [activeMission, progress, logs, isConnected, isPlaying, isPaused, isLoading, error, launchMission, pauseMission, resumeMission, abortMission, exportLogs, clearLogs]
  );
};

export default useMissionControl;
