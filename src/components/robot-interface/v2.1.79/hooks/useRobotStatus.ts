/**
 * useRobotStatus Hook - RaaS UX Kit v2.1.79
 * Real-time robot status monitoring with WebSocket support
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Robot, RobotStatus, RobotEvent } from '../types/robot';

export interface UseRobotStatusOptions {
  robotId: string;
  pollingInterval?: number; // ms, default: 5000
  enableWebSocket?: boolean;
  wsUrl?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number; // ms, default: 3000
}

export interface UseRobotStatusReturn {
  robot: Robot | null;
  status: RobotStatus;
  isConnected: boolean;
  isConnecting: boolean;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  acknowledgeEvent: (eventId: string) => Promise<void>;
  events: RobotEvent[];
  clearEvents: () => void;
}

export const useRobotStatus = ({
  robotId,
  pollingInterval = 5000,
  enableWebSocket = false,
  wsUrl,
  autoReconnect = true,
  reconnectInterval = 3000,
}: UseRobotStatusOptions): UseRobotStatusReturn => {
  const [robot, setRobot] = useState<Robot | null>(null);
  const [status, setStatus] = useState<RobotStatus>('offline');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<RobotEvent[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch robot status
  const fetchRobotStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // TODO: Replace with actual API endpoint
      const response = await fetch(`/api/robots/${robotId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch robot status: ${response.status}`);
      }

      const data: Robot = await response.json();
      setRobot(data);
      setStatus(data.status);
      setIsConnected(data.connectionState === 'online');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setStatus('offline');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [robotId]);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket || !wsUrl) return;

    setIsConnecting(true);

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        console.log(`WebSocket connected to ${wsUrl}`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'status_update' && data.robotId === robotId) {
            setStatus(data.status);
            setRobot((prev) => prev ? { ...prev, status: data.status } : null);
          }

          if (data.type === 'event' && data.robotId === robotId) {
            setEvents((prev) => [...prev, data.event]);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = () => {
        setIsConnected(false);
        setIsConnecting(false);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);

        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setIsConnecting(false);
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [enableWebSocket, wsUrl, robotId, autoReconnect, reconnectInterval]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Acknowledge event
  const acknowledgeEvent = useCallback(async (eventId: string) => {
    // TODO: Replace with actual API endpoint
    await fetch(`/api/robots/${robotId}/events/${eventId}/acknowledge`, {
      method: 'POST',
    });

    setEvents((prev) =>
      prev.map((e) =>
        e.id === eventId
          ? { ...e, acknowledged: true, acknowledgedAt: new Date() }
          : e
      )
    );
  }, [robotId]);

  // Clear events
  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  // Refresh function
  const refresh = useCallback(async () => {
    await fetchRobotStatus();
  }, [fetchRobotStatus]);

  // Initial connection and polling
  useEffect(() => {
    fetchRobotStatus();

    // Set up polling
    pollIntervalRef.current = setInterval(fetchRobotStatus, pollingInterval);

    // Set up WebSocket if enabled
    if (enableWebSocket) {
      connectWebSocket();
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      disconnectWebSocket();
    };
  }, [fetchRobotStatus, pollingInterval, enableWebSocket, connectWebSocket, disconnectWebSocket]);

  return {
    robot,
    status,
    isConnected,
    isConnecting,
    isLoading,
    error,
    refresh,
    acknowledgeEvent,
    events,
    clearEvents,
  };
};

export default useRobotStatus;
