/**
 * Context Visualizer hook — token usage, compression events, polling or WS.
 */
"use client";

import { useEffect } from "react";
import { useApi } from "./use-api";
import { getContextMetrics } from "@/lib/api/endpoints/context-api";
import { useWsSubscription } from "@/lib/ws/use-ws-subscription";
import type { ContextMetrics } from "@/lib/types/context-types";
import type { ContextUpdateEvent } from "@/lib/ws/ws-events";
import { MOCK_CONTEXT } from "@/lib/mock/context-mock-data";

interface UseContextMetricsResult {
  metrics: ContextMetrics | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  refetch: () => void;
}

export function useContextMetrics(): UseContextMetricsResult {
  const { data, isLoading, error, isDemoMode, refetch } = useApi<ContextMetrics>(
    getContextMetrics,
    MOCK_CONTEXT,
    { refreshIntervalMs: 5_000 }
  );

  // WS push for immediate updates on compression events
  const { messages } = useWsSubscription<ContextUpdateEvent>("/ws/events", {
    eventTypes: ["context.update"],
  });

  useEffect(() => {
    if (messages.length > 0) refetch();
  }, [messages.length]); // eslint-disable-line react-hooks/exhaustive-deps

  return { metrics: data, isLoading, error, isDemoMode, refetch };
}
