/**
 * Mock trading data — 5 positions, 10 fair values, 20 signals.
 */

import type { Position, FairValue, LlmSignal, TradingStats } from "@/lib/types/trading-types";

export const MOCK_TRADING_STATS: TradingStats = {
  mode: "paper",
  balance: 100_000,
  totalPnl: 3_241.50,
  totalPnlPct: 3.24,
  openPositions: 5,
};

export const MOCK_POSITIONS: Position[] = [
  {
    id: "p1", ticker: "AAPL", side: "long", size: 50,
    entryPrice: 185.20, currentPrice: 192.45,
    unrealizedPnl: 362.50, unrealizedPnlPct: 3.91, status: "open",
  },
  {
    id: "p2", ticker: "NVDA", side: "long", size: 20,
    entryPrice: 820.00, currentPrice: 845.30,
    unrealizedPnl: 506.00, unrealizedPnlPct: 3.09, status: "open",
  },
  {
    id: "p3", ticker: "TSLA", side: "short", size: 30,
    entryPrice: 180.00, currentPrice: 175.60,
    unrealizedPnl: 132.00, unrealizedPnlPct: 2.44, status: "open",
  },
  {
    id: "p4", ticker: "MSFT", side: "long", size: 25,
    entryPrice: 415.00, currentPrice: 408.20,
    unrealizedPnl: -170.00, unrealizedPnlPct: -1.64, status: "open",
  },
  {
    id: "p5", ticker: "SPY", side: "long", size: 10,
    entryPrice: 505.00, currentPrice: 512.30,
    unrealizedPnl: 73.00, unrealizedPnlPct: 1.44, status: "open",
  },
];

export const MOCK_FAIR_VALUES: FairValue[] = [
  { ticker: "AAPL", fairValue: 198.00, currentPrice: 192.45, edgePct: 2.88, confidence: 82, updatedAt: "10:45" },
  { ticker: "NVDA", fairValue: 870.00, currentPrice: 845.30, edgePct: 2.92, confidence: 78, updatedAt: "10:44" },
  { ticker: "TSLA", fairValue: 165.00, currentPrice: 175.60, edgePct: -6.03, confidence: 88, updatedAt: "10:43" },
  { ticker: "MSFT", fairValue: 400.00, currentPrice: 408.20, edgePct: -2.01, confidence: 71, updatedAt: "10:42" },
  { ticker: "SPY", fairValue: 520.00, currentPrice: 512.30, edgePct: 1.50, confidence: 85, updatedAt: "10:41" },
  { ticker: "AMZN", fairValue: 195.00, currentPrice: 188.40, edgePct: 3.50, confidence: 74, updatedAt: "10:40" },
  { ticker: "GOOGL", fairValue: 172.00, currentPrice: 170.50, edgePct: 0.88, confidence: 66, updatedAt: "10:39" },
  { ticker: "META", fairValue: 510.00, currentPrice: 525.20, edgePct: -2.89, confidence: 69, updatedAt: "10:38" },
  { ticker: "BTC", fairValue: 72_000, currentPrice: 68_500, edgePct: 5.11, confidence: 55, updatedAt: "10:37" },
  { ticker: "ETH", fairValue: 3_400, currentPrice: 3_250, edgePct: 4.62, confidence: 60, updatedAt: "10:36" },
];

export const MOCK_SIGNALS: LlmSignal[] = [
  { id: "s1", model: "Sonnet", modelVariant: "architect", ticker: "AAPL", direction: "buy", confidence: 85, reasoning: "Strong earnings momentum", timestamp: "10:45" },
  { id: "s2", model: "Opus", modelVariant: "reasoning", ticker: "NVDA", direction: "hold", confidence: 60, reasoning: "Overbought short-term, fair medium-term", timestamp: "10:44" },
  { id: "s3", model: "DeepSeek", modelVariant: "trading", ticker: "TSLA", direction: "sell", confidence: 90, reasoning: "Downtrend confirmed, bearish momentum", timestamp: "10:43" },
  { id: "s4", model: "Sonnet", modelVariant: "architect", ticker: "MSFT", direction: "hold", confidence: 55, reasoning: "Mixed signals, wait for breakout", timestamp: "10:42" },
  { id: "s5", model: "Qwen", modelVariant: "audit", ticker: "SPY", direction: "buy", confidence: 72, reasoning: "Market breadth improving", timestamp: "10:41" },
  { id: "s6", model: "DeepSeek", modelVariant: "trading", ticker: "AMZN", direction: "buy", confidence: 88, reasoning: "Cloud revenue beat, undervalued", timestamp: "10:40" },
  { id: "s7", model: "Opus", modelVariant: "reasoning", ticker: "GOOGL", direction: "buy", confidence: 65, reasoning: "AI tailwinds not priced in", timestamp: "10:39" },
  { id: "s8", model: "Sonnet", modelVariant: "architect", ticker: "META", direction: "sell", confidence: 78, reasoning: "Ad spend plateauing, elevated valuation", timestamp: "10:38" },
  { id: "s9", model: "DeepSeek", modelVariant: "trading", ticker: "BTC", direction: "buy", confidence: 82, reasoning: "ETF inflows accelerating, halving near", timestamp: "10:37" },
  { id: "s10", model: "Qwen", modelVariant: "audit", ticker: "ETH", direction: "buy", confidence: 70, reasoning: "Staking yield attractive vs risk", timestamp: "10:36" },
  { id: "s11", model: "Sonnet", modelVariant: "architect", ticker: "NVDA", direction: "buy", confidence: 91, reasoning: "Data center demand secular growth", timestamp: "10:35" },
  { id: "s12", model: "Opus", modelVariant: "reasoning", ticker: "TSLA", direction: "sell", confidence: 83, reasoning: "Volume declining, chart breakdown", timestamp: "10:34" },
  { id: "s13", model: "DeepSeek", modelVariant: "trading", ticker: "AAPL", direction: "buy", confidence: 77, reasoning: "Services segment margin expansion", timestamp: "10:33" },
  { id: "s14", model: "Qwen", modelVariant: "audit", ticker: "MSFT", direction: "buy", confidence: 68, reasoning: "Copilot traction exceeding estimates", timestamp: "10:32" },
  { id: "s15", model: "Sonnet", modelVariant: "architect", ticker: "SPY", direction: "hold", confidence: 58, reasoning: "Awaiting macro clarity", timestamp: "10:31" },
];
