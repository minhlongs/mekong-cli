/**
 * Tool approval endpoint functions.
 * GET /v1/tools, POST /v1/tools/:id/approve, GET /v1/tools/calls
 */

import { apiClient } from "../api-client";
import type { ToolDef, ToolCall, ApiResult } from "../api-types";

export function listTools(): Promise<ApiResult<ToolDef[]>> {
  return apiClient.get<ToolDef[]>("/v1/tools");
}

export function approveTool(id: string): Promise<ApiResult<{ approved: boolean }>> {
  return apiClient.post<{ approved: boolean }>(`/v1/tools/${id}/approve`);
}

export function getToolCalls(limit = 50): Promise<ApiResult<ToolCall[]>> {
  return apiClient.get<ToolCall[]>(`/v1/tools/calls?limit=${limit}`);
}
