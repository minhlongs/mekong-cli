/**
 * Engine Farm hook — list engines, start/stop with optimistic updates.
 * Merges WS status events for real-time state.
 */
"use client";

import { useEffect } from "react";
import { useApi } from "./use-api";
import { listEngines, startEngine, stopEngine } from "@/lib/api/endpoints/engine-api";
import { useWsSubscription } from "@/lib/ws/use-ws-subscription";
import type { Engine } from "@/lib/types/engine-types";
import type { EngineStatusEvent } from "@/lib/ws/ws-events";
import { MOCK_ENGINES } from "@/lib/mock/engine-mock-data";

interface UseEnginesResult {
  engines: Engine[] | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  start: (id: string) => Promise<void>;
  stop: (id: string) => Promise<void>;
  refetch: () => void;
}

export function useEngines(): UseEnginesResult {
  const { data, isLoading, error, isDemoMode, refetch } = useApi<Engine[]>(
    listEngines,
    MOCK_ENGINES,
    { refreshIntervalMs: 10_000 }
  );

  // Merge real-time status events from WS
  const { messages } = useWsSubscription<EngineStatusEvent>("/ws/events", {
    eventTypes: ["engine.status"],
  });

  useEffect(() => {
    // WS events update engines in-place via refetch (simplest approach)
    if (messages.length > 0) refetch();
  }, [messages.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const start = async (id: string) => {
    if (isDemoMode) return;
    await startEngine(id);
    refetch();
  };

  const stop = async (id: string) => {
    if (isDemoMode) return;
    await stopEngine(id);
    refetch();
  };

  return { engines: data, isLoading, error, isDemoMode, start, stop, refetch };
}
