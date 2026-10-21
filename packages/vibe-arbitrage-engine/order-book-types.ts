/**
 * OrderBookAnalyzer types and interfaces.
 */

export interface OrderBookLevel {
  price: number;
  amount: number;  // Base currency quantity at this level
}

export interface OrderBook {
  exchange: string;
  symbol: string;
  bids: OrderBookLevel[];  // Sorted descending (highest first)
  asks: OrderBookLevel[];  // Sorted ascending (lowest first)
  timestamp: number;
}

export interface SlippageEstimate {
  side: 'buy' | 'sell';
  exchange: string;
  symbol: string;
  requestedAmount: number;
  avgFillPrice: number;
  worstPrice: number;
  slippageBps: number;        // Slippage from best price in basis points
  slippageCostUsd: number;    // Dollar cost of slippage
  levelsConsumed: number;     // Number of orderbook levels needed
  fillable: boolean;          // Whether full amount can be filled
  filledAmount: number;       // Actual filled amount (may be less if illiquid)
  depthUsd: number;           // Total USD depth available
}

export interface LiquidityScore {
  exchange: string;
  symbol: string;
  bidDepthUsd: number;        // Total bid side depth in USD
  askDepthUsd: number;        // Total ask side depth in USD
  midPrice: number;           // Mid-market price
  bidAskSpreadBps: number;    // Native bid-ask spread in bps
  score: number;              // 0-100 liquidity score
  timestamp: number;
}

export interface ArbitrageFillSimulation {
  buyEstimate: SlippageEstimate;
  sellEstimate: SlippageEstimate;
  totalSlippageBps: number;
  totalSlippageCostUsd: number;
  effectiveSpreadPercent: number;   // Spread after accounting for slippage
  feasible: boolean;                // Whether trade is still profitable
}
