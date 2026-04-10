/**
 * Engine Farm endpoint functions.
 * GET /v1/engines, POST /v1/engines/:id/start|stop, GET /v1/system/resources
 */

import { apiClient } from "../api-client";
import type { Engine, SystemResources, ApiResult } from "../api-types";

export function listEngines(): Promise<ApiResult<Engine[]>> {
  return apiClient.get<Engine[]>("/v1/engines");
}

export function startEngine(id: string): Promise<ApiResult<Engine>> {
  return apiClient.post<Engine>(`/v1/engines/${id}/start`);
}

export function stopEngine(id: string): Promise<ApiResult<Engine>> {
  return apiClient.post<Engine>(`/v1/engines/${id}/stop`);
}

export function getSystemResources(): Promise<ApiResult<SystemResources>> {
  return apiClient.get<SystemResources>("/v1/system/resources");
}
