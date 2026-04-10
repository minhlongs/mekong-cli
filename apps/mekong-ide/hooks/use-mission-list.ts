/**
 * Hook: fetches mission list for a given department.
 * Calls GET /v1/tasks?department=X&limit=20 via apiClient.
 * Falls back to empty mock array when API unreachable (demo mode).
 */
"use client";

import { useCallback, useState } from "react";
import { useApi } from "./use-api";
import { apiClient } from "@/lib/api/api-client";
import type { MissionResult } from "@/lib/types/report-types";
import type { ApiResult } from "@/lib/api/api-types";

/** Empty fallback — no missions means empty list in demo mode */
const MOCK_MISSIONS: MissionResult[] = [];

function listMissions(department: string, limit = 20) {
  return (): Promise<ApiResult<MissionResult[]>> =>
    apiClient.get<MissionResult[]>(
      `/v1/tasks?department=${encodeURIComponent(department)}&limit=${limit}`
    );
}

interface UseMissionListResult {
  missions: MissionResult[] | null;
  loading: boolean;
  error: string | null;
}

/**
 * Fetch missions filtered by department.
 * @param department - department slug, e.g. "marketing"
 * @param limit - max results to fetch (default 20)
 */
export function useMissionList(
  department: string,
  limit = 20
): UseMissionListResult {
  const { data, isLoading, error } = useApi<MissionResult[]>(
    listMissions(department, limit),
    MOCK_MISSIONS
  );

  return { missions: data, loading: isLoading, error };
}
