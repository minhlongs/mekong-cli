/**
 * Context Visualizer endpoint functions.
 * GET /v1/context/usage, GET /v1/context/compression
 */

import { apiClient } from "../api-client";
import type { TokenUsage, CompressionEvent, ContextMetrics, ApiResult } from "../api-types";

export function getTokenUsage(): Promise<ApiResult<TokenUsage>> {
  return apiClient.get<TokenUsage>("/v1/context/usage");
}

export function getCompressionHistory(): Promise<ApiResult<CompressionEvent[]>> {
  return apiClient.get<CompressionEvent[]>("/v1/context/compression");
}

export function getContextMetrics(): Promise<ApiResult<ContextMetrics>> {
  return apiClient.get<ContextMetrics>("/v1/context/metrics");
}
