/**
 * Generic API hook with loading/error/data state management.
 * Provides domain-specific hooks for all screens with demo-mode fallback.
 */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { ApiResult } from "@/lib/api/api-types";
import { apiClient } from "@/lib/api/api-client";
import { isApiReachable } from "@/lib/api/demo-mode";
import * as engineApi from "@/lib/api/endpoints/engine-api";
import * as taskApi from "@/lib/api/endpoints/task-api";
import * as tradingApi from "@/lib/api/endpoints/trading-api";
import * as contextApi from "@/lib/api/endpoints/context-api";
import * as toolApi from "@/lib/api/endpoints/tool-api";
import * as agentApi from "@/lib/api/endpoints/agent-api";
import { MOCK_ENGINES, MOCK_SYSTEM } from "@/lib/mock/engine-mock-data";
import { MOCK_TASKS } from "@/lib/mock/task-mock-data";
import { MOCK_POSITIONS, MOCK_SIGNALS, MOCK_FAIR_VALUES } from "@/lib/mock/trading-mock-data";
import { MOCK_CONTEXT } from "@/lib/mock/context-mock-data";
import { MOCK_TOOLS, MOCK_TOOL_CALLS } from "@/lib/mock/tool-mock-data";
import type { Engine, SystemResources, Task, Position, FairValue, LlmSignal, ContextMetrics } from "@/lib/api/api-types";
import type { ToolDef, ToolCall } from "@/lib/tool-types";
import type { ModelConfig } from "@/lib/agent-types";

// ---- Generic hook ----

interface UseApiState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  isDemoMode: boolean;
  refetch: () => void;
}

export function useApi<T>(
  fetcher: () => Promise<ApiResult<T>>,
  mockData: T,
  options: { refreshIntervalMs?: number } = {}
): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const mockRef = useRef(mockData);
  mockRef.current = mockData;

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const result = await fetcherRef.current();
    if (result.error) {
      const reachable = await isApiReachable();
      if (!reachable) {
        setData(mockRef.current);
        setIsDemoMode(true);
        setError(null);
      } else {
        setError(result.error);
        setIsDemoMode(false);
      }
    } else {
      setData(result.data);
      setIsDemoMode(false);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    load();
    if (options.refreshIntervalMs) {
      const id = setInterval(load, options.refreshIntervalMs);
      return () => clearInterval(id);
    }
  }, [load, options.refreshIntervalMs]);

  return { data, error, isLoading, isDemoMode, refetch: load };
}

// ---- Domain hooks ----

export function useHealth() {
  return useApi<{ status: string; timestamp: string; version: string }>(
    () => apiClient.get("/health"),
    { status: "ok", timestamp: new Date().toISOString(), version: "demo" },
    { refreshIntervalMs: 30_000 }
  );
}

export function useEngines() {
  return useApi<Engine[]>(
    engineApi.listEngines,
    MOCK_ENGINES,
    { refreshIntervalMs: 5_000 }
  );
}

export function useSystemResources() {
  return useApi<SystemResources>(
    engineApi.getSystemResources,
    MOCK_SYSTEM,
    { refreshIntervalMs: 3_000 }
  );
}

export function useTasks() {
  return useApi<Task[]>(taskApi.listTasks, MOCK_TASKS);
}

export function usePositions() {
  return useApi<Position[]>(tradingApi.getPositions, MOCK_POSITIONS, { refreshIntervalMs: 10_000 });
}

export function useFairValues() {
  return useApi<FairValue[]>(tradingApi.getFairValues, MOCK_FAIR_VALUES, { refreshIntervalMs: 15_000 });
}

export function useSignals(limit = 20) {
  return useApi<LlmSignal[]>(
    () => tradingApi.getSignals(limit),
    MOCK_SIGNALS,
    { refreshIntervalMs: 10_000 }
  );
}

export function useContextMetrics() {
  return useApi<ContextMetrics>(contextApi.getContextMetrics, MOCK_CONTEXT, {
    refreshIntervalMs: 5_000,
  });
}

export function useTools() {
  return useApi<ToolDef[]>(toolApi.listTools, MOCK_TOOLS);
}

export function useToolCalls(limit = 50) {
  return useApi<ToolCall[]>(
    () => toolApi.getToolCalls(limit),
    MOCK_TOOL_CALLS,
    { refreshIntervalMs: 3_000 }
  );
}

export function useModels() {
  return useApi<ModelConfig[]>(agentApi.getModels, []);
}
