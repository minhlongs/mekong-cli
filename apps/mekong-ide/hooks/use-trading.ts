/**
 * CashClaw Trading hook — positions, fair values, signals, trade execution.
 * Signals refresh via WS events channel.
 */
"use client";

import { useEffect } from "react";
import { useApi } from "./use-api";
import {
  getPositions,
  getFairValues,
  getSignals,
  executeTrade,
  type TradeAction,
} from "@/lib/api/endpoints/trading-api";
import { useWsSubscription } from "@/lib/ws/use-ws-subscription";
import type { Position, FairValue, LlmSignal } from "@/lib/types/trading-types";
import type { SignalEvent } from "@/lib/ws/ws-events";
import {
  MOCK_POSITIONS,
  MOCK_FAIR_VALUES,
  MOCK_SIGNALS,
} from "@/lib/mock/trading-mock-data";

interface UseTradingResult {
  positions: Position[] | null;
  fairValues: FairValue[] | null;
  signals: LlmSignal[] | null;
  isLoading: boolean;
  error: string | null;
  isDemoMode: boolean;
  trade: (action: TradeAction) => Promise<{ orderId: string } | null>;
  refetch: () => void;
}

export function useTrading(): UseTradingResult {
  const posState = useApi<Position[]>(getPositions, MOCK_POSITIONS, { refreshIntervalMs: 10_000 });
  const fvState = useApi<FairValue[]>(getFairValues, MOCK_FAIR_VALUES, { refreshIntervalMs: 15_000 });
  const sigState = useApi<LlmSignal[]>(() => getSignals(20), MOCK_SIGNALS, { refreshIntervalMs: 10_000 });

  // Real-time signal events via WS
  const { messages } = useWsSubscription<SignalEvent>("/ws/events", {
    eventTypes: ["trading.signal"],
  });

  useEffect(() => {
    if (messages.length > 0) sigState.refetch();
  }, [messages.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const trade = async (action: TradeAction) => {
    if (sigState.isDemoMode) return null;
    const result = await executeTrade(action);
    if (result.data) posState.refetch();
    return result.data;
  };

  return {
    positions: posState.data,
    fairValues: fvState.data,
    signals: sigState.data,
    isLoading: posState.isLoading || fvState.isLoading || sigState.isLoading,
    error: posState.error ?? fvState.error ?? sigState.error,
    isDemoMode: posState.isDemoMode || sigState.isDemoMode,
    trade,
    refetch: () => {
      posState.refetch();
      fvState.refetch();
      sigState.refetch();
    },
  };
}
