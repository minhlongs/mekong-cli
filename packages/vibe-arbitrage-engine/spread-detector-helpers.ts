/**
 * SpreadDetectorEngine helper functions for signal scoring, orderbook validation, and refresh.
 */

import { ArbitrageOpportunity } from './arbitrage-types';
import { ArbitrageSignalScorer, ScoredSignal, SignalFactors } from './signal-scorer';
import { OrderBookAnalyzer } from './order-book-analyzer';
import { SpreadZScore } from './spread-history-tracker';
import { MultiExchangeConnector } from './multi-exchange-connector';
import { SpreadDetectorConfig } from './spread-detector-types';

export function evaluateDetectionSignal(
  opp: ArbitrageOpportunity,
  config: SpreadDetectorConfig,
  orderbook: OrderBookAnalyzer,
  connector: MultiExchangeConnector,
  scorer: ArbitrageSignalScorer,
  zScore: SpreadZScore | null
): ScoredSignal {
  const liquidityScore = orderbook.hasOrderBook(opp.buyExchange, opp.symbol)
    ? orderbook.getLiquidityScore(opp.buyExchange, opp.symbol).score : 50;

  const factors: SignalFactors = {
    spreadPercent: opp.spreadPercent,
    netProfitPercent: opp.netProfitPercent,
    liquidityScore,
    latencyMs: opp.latency.buy + opp.latency.sell,
    feeCostPercent: (config.scanner.feeRatePerSide || 0.001) * 2 * 100,
    spreadZScore: zScore?.zScore || 0,
    fillable: true,
    exchangeHealthy: connector.isHealthy(opp.buyExchange) &&
                     connector.isHealthy(opp.sellExchange),
  };

  return scorer.score(factors);
}

export function validateOrderbookFeasibility(
  opp: ArbitrageOpportunity,
  config: SpreadDetectorConfig,
  orderbook: OrderBookAnalyzer
): { feasible: boolean; slippageBps: number } {
  const positionUsd = Math.min(
    config.executor.maxPositionSizeUsd || 1000,
    opp.estimatedProfitUsd * 100
  );
  const amount = positionUsd / opp.buyPrice;

  if (orderbook.hasOrderBook(opp.buyExchange, opp.symbol) &&
      orderbook.hasOrderBook(opp.sellExchange, opp.symbol)) {
    const sim = orderbook.simulateArbitrageFill(
      opp.buyExchange, opp.sellExchange, opp.symbol,
      amount, config.scanner.feeRatePerSide || 0.001
    );
    return { feasible: sim.feasible, slippageBps: sim.totalSlippageBps };
  }
  return { feasible: true, slippageBps: 0 };
}

export async function refreshOrderBooksOnce(
  connector: MultiExchangeConnector,
  orderbook: OrderBookAnalyzer,
  symbols: string[]
): Promise<void> {
  const clients = connector.getActiveClients();
  for (const [name, client] of clients) {
    for (const symbol of symbols) {
      try {
        const rawBook = await client.fetchOrderBook(symbol);
        if (rawBook) {
          orderbook.updateOrderBook({
            exchange: name, symbol,
            bids: rawBook.bids, asks: rawBook.asks,
            timestamp: Date.now(),
          });
        }
      } catch { /* orderbook is optional enhancement */ }
    }
  }
}
