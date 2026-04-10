/**
 * CashClaw Trading endpoint functions.
 * GET /v1/positions, GET /v1/fair-values, GET /v1/signals, POST /v1/trade
 */

import { apiClient } from "../api-client";
import type { Position, FairValue, LlmSignal, TradingStats, ApiResult } from "../api-types";

export interface TradeAction {
  ticker: string;
  side: "long" | "short";
  size: number;
  /** Optional limit price; omit for market order */
  price?: number;
}

export function getPositions(): Promise<ApiResult<Position[]>> {
  return apiClient.get<Position[]>("/v1/positions");
}

export function getFairValues(): Promise<ApiResult<FairValue[]>> {
  return apiClient.get<FairValue[]>("/v1/fair-values");
}

export function getSignals(limit = 20): Promise<ApiResult<LlmSignal[]>> {
  return apiClient.get<LlmSignal[]>(`/v1/signals?limit=${limit}`);
}

export function getTradingStats(): Promise<ApiResult<TradingStats>> {
  return apiClient.get<TradingStats>("/v1/trading/stats");
}

export function executeTrade(action: TradeAction): Promise<ApiResult<{ orderId: string }>> {
  return apiClient.post<{ orderId: string }>("/v1/trade", action);
}
