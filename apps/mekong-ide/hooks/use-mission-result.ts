/**
 * useMissionResult — fetches mission execution result by ID.
 * Uses apiClient which auto-routes through Tauri IPC or native fetch.
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api/api-client";
import type { MissionResult } from "@/lib/types/report-types";

interface UseMissionResultState {
  data: MissionResult | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Fetch result for a completed mission by its ID.
 * Endpoint: GET /v1/tasks/{id}/result
 */
export function useMissionResult(missionId: string | null): UseMissionResultState {
  const [data, setData] = useState<MissionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!missionId) return;

    setLoading(true);
    setError(null);

    const result = await apiClient.get<MissionResult>(`/v1/tasks/${missionId}/result`);

    if (result.error) {
      setError(result.error);
      setData(null);
    } else {
      setData(result.data);
    }

    setLoading(false);
  }, [missionId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}
