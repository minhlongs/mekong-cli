/**
 * CashClaw Trading type definitions — positions, fair values, signals.
 */

export type TradeSide = "long" | "short";
export type PositionStatus = "open" | "closed" | "liquidated";
export type SignalDirection = "buy" | "sell" | "hold";
export type TradingMode = "paper" | "live";

export interface Position {
  id: string;
  ticker: string;
  side: TradeSide;
  size: number;
  entryPrice: number;
  currentPrice: number;
  /** Unrealized PnL in USD */
  unrealizedPnl: number;
  /** PnL as % of entry */
  unrealizedPnlPct: number;
  status: PositionStatus;
}

export interface FairValue {
  ticker: string;
  /** Model-computed fair value */
  fairValue: number;
  /** Current market price */
  currentPrice: number;
  /** Edge = (fairValue - currentPrice) / currentPrice * 100 */
  edgePct: number;
  /** 0–100 */
  confidence: number;
  updatedAt: string;
}

export interface LlmSignal {
  id: string;
  model: string;
  /** Color token key, e.g. "trading" | "architect" | "reasoning" */
  modelVariant: "trading" | "architect" | "reasoning" | "audit";
  ticker: string;
  direction: SignalDirection;
  /** 0–100 */
  confidence: number;
  reasoning: string;
  timestamp: string;
}

export interface TradingStats {
  mode: TradingMode;
  balance: number;
  totalPnl: number;
  totalPnlPct: number;
  openPositions: number;
}
