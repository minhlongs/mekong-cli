/**
 * OrderBookAnalyzer — Orderbook depth analysis for accurate slippage estimation.
 */

import { getArbLogger } from './arb-logger';
import {
  OrderBook, SlippageEstimate, LiquidityScore, ArbitrageFillSimulation,
} from './order-book-types';

export * from './order-book-types';

const logger = getArbLogger();

export class OrderBookAnalyzer {
  private orderbooks: Map<string, OrderBook> = new Map();

  updateOrderBook(orderbook: OrderBook): void {
    this.orderbooks.set(`${orderbook.exchange}:${orderbook.symbol}`, orderbook);
  }

  estimateBuySlippage(exchange: string, symbol: string, amountBase: number): SlippageEstimate {
    return this.estimateSlippage(exchange, symbol, amountBase, 'buy');
  }

  estimateSellSlippage(exchange: string, symbol: string, amountBase: number): SlippageEstimate {
    return this.estimateSlippage(exchange, symbol, amountBase, 'sell');
  }

  private estimateSlippage(
    exchange: string,
    symbol: string,
    requestedAmount: number,
    side: 'buy' | 'sell'
  ): SlippageEstimate {
    const ob = this.orderbooks.get(`${exchange}:${symbol}`);
    if (!ob) return this.noDataEstimate(exchange, symbol, requestedAmount, side);

    const levels = side === 'buy' ? ob.asks : ob.bids;
    if (levels.length === 0) return this.noDataEstimate(exchange, symbol, requestedAmount, side);

    const bestPrice = levels[0].price;
    let remainingAmount = requestedAmount;
    let totalCost = 0;
    let filledAmount = 0;
    let levelsConsumed = 0;
    let worstPrice = bestPrice;
    let totalDepthUsd = 0;

    for (const level of levels) {
      totalDepthUsd += level.price * level.amount;
      if (remainingAmount <= 0) break;

      const fillAtLevel = Math.min(remainingAmount, level.amount);
      totalCost += fillAtLevel * level.price;
      filledAmount += fillAtLevel;
      remainingAmount -= fillAtLevel;
      levelsConsumed++;
      worstPrice = level.price;
    }

    const avgFillPrice = filledAmount > 0 ? totalCost / filledAmount : bestPrice;
    const slippageBps = bestPrice > 0 ? Math.abs(avgFillPrice - bestPrice) / bestPrice * 10000 : 0;
    const slippageCostUsd = Math.abs(avgFillPrice - bestPrice) * filledAmount;

    return {
      side, exchange, symbol, requestedAmount, avgFillPrice, worstPrice,
      slippageBps, slippageCostUsd, levelsConsumed,
      fillable: remainingAmount <= 0, filledAmount, depthUsd: totalDepthUsd,
    };
  }

  simulateArbitrageFill(
    buyExchange: string,
    sellExchange: string,
    symbol: string,
    amountBase: number,
    feeRatePerSide: number
  ): ArbitrageFillSimulation {
    const buyEstimate = this.estimateBuySlippage(buyExchange, symbol, amountBase);
    const sellEstimate = this.estimateSellSlippage(sellExchange, symbol, amountBase);

    const totalSlippageBps = buyEstimate.slippageBps + sellEstimate.slippageBps;
    const totalSlippageCostUsd = buyEstimate.slippageCostUsd + sellEstimate.slippageCostUsd;

    const effectiveBuyPrice = buyEstimate.avgFillPrice;
    const effectiveSellPrice = sellEstimate.avgFillPrice;
    const grossSpread = effectiveSellPrice - effectiveBuyPrice;
    const feesCost = (effectiveBuyPrice + effectiveSellPrice) * amountBase * feeRatePerSide;
    const netProfit = grossSpread * amountBase - feesCost - totalSlippageCostUsd;

    const effectiveSpreadPercent = effectiveBuyPrice > 0 ? (grossSpread / effectiveBuyPrice) * 100 : 0;

    return {
      buyEstimate, sellEstimate, totalSlippageBps, totalSlippageCostUsd,
      effectiveSpreadPercent,
      feasible: netProfit > 0 && buyEstimate.fillable && sellEstimate.fillable,
    };
  }

  getLiquidityScore(exchange: string, symbol: string): LiquidityScore {
    const ob = this.orderbooks.get(`${exchange}:${symbol}`);
    if (!ob || ob.bids.length === 0 || ob.asks.length === 0) {
      return {
        exchange, symbol, bidDepthUsd: 0, askDepthUsd: 0,
        midPrice: 0, bidAskSpreadBps: 0, score: 0, timestamp: Date.now(),
      };
    }

    const bidDepthUsd = ob.bids.reduce((sum, l) => sum + l.price * l.amount, 0);
    const askDepthUsd = ob.asks.reduce((sum, l) => sum + l.price * l.amount, 0);

    const bestBid = ob.bids[0].price;
    const bestAsk = ob.asks[0].price;
    const midPrice = (bestBid + bestAsk) / 2;
    const bidAskSpreadBps = midPrice > 0 ? ((bestAsk - bestBid) / midPrice) * 10000 : 0;

    const totalDepth = bidDepthUsd + askDepthUsd;
    const depthScore = Math.min(50, (totalDepth / 100000) * 50);
    const spreadScore = Math.max(0, 50 - bidAskSpreadBps * 10);
    const score = Math.round(depthScore + spreadScore);

    return {
      exchange, symbol, bidDepthUsd, askDepthUsd,
      midPrice, bidAskSpreadBps, score: Math.min(100, score), timestamp: Date.now(),
    };
  }

  getBestBuyExchange(symbol: string, amountBase: number): { exchange: string; avgPrice: number; slippageBps: number } | null {
    const candidates: { exchange: string; avgPrice: number; slippageBps: number }[] = [];
    for (const [key, ob] of this.orderbooks) {
      if (!key.endsWith(`:${symbol}`)) continue;
      const estimate = this.estimateBuySlippage(ob.exchange, symbol, amountBase);
      if (estimate.fillable && estimate.avgFillPrice > 0) {
        candidates.push({ exchange: ob.exchange, avgPrice: estimate.avgFillPrice, slippageBps: estimate.slippageBps });
      }
    }
    return candidates.length === 0 ? null : candidates.sort((a, b) => a.avgPrice - b.avgPrice)[0];
  }

  getBestSellExchange(symbol: string, amountBase: number): { exchange: string; avgPrice: number; slippageBps: number } | null {
    const candidates: { exchange: string; avgPrice: number; slippageBps: number }[] = [];
    for (const [key, ob] of this.orderbooks) {
      if (!key.endsWith(`:${symbol}`)) continue;
      const estimate = this.estimateSellSlippage(ob.exchange, symbol, amountBase);
      if (estimate.fillable && estimate.avgFillPrice > 0) {
        candidates.push({ exchange: ob.exchange, avgPrice: estimate.avgFillPrice, slippageBps: estimate.slippageBps });
      }
    }
    return candidates.length === 0 ? null : candidates.sort((a, b) => b.avgPrice - a.avgPrice)[0];
  }

  hasOrderBook(exchange: string, symbol: string): boolean {
    return this.orderbooks.has(`${exchange}:${symbol}`);
  }

  clear(): void { this.orderbooks.clear(); }

  private noDataEstimate(exchange: string, symbol: string, amount: number, side: 'buy' | 'sell'): SlippageEstimate {
    logger.warn(`[OrderBook] No orderbook data for ${exchange}:${symbol}`);
    return {
      side, exchange, symbol, requestedAmount: amount, avgFillPrice: 0, worstPrice: 0,
      slippageBps: 0, slippageCostUsd: 0, levelsConsumed: 0, fillable: false, filledAmount: 0, depthUsd: 0,
    };
  }
}
