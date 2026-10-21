/**
 * ArbitrageBacktester — Backtest cross-exchange arbitrage strategies.
 */

import { FeeCalculator } from './fee-calculator';
import { getArbLogger } from './arb-logger';
import {
  ExchangePricePoint, MultiExchangePriceSnapshot, BacktestTradeRecord,
  BacktestEquityPoint, BacktestResult, BacktestMetrics, BacktestConfig,
  DEFAULT_BACKTEST_CONFIG, createEmptyBacktestMetrics,
} from './arbitrage-backtester-types';

export * from './arbitrage-backtester-types';

export class ArbitrageBacktester {
  private config: BacktestConfig;
  private feeCalculator: FeeCalculator;

  constructor(config?: Partial<BacktestConfig>) {
    this.config = { ...DEFAULT_BACKTEST_CONFIG, ...config };
    this.feeCalculator = new FeeCalculator();
  }

  run(snapshots: MultiExchangePriceSnapshot[]): BacktestResult {
    if (snapshots.length === 0) return this.emptyResult();

    const sorted = [...snapshots].sort((a, b) => a.timestamp - b.timestamp);
    let equity = this.config.initialCapitalUsd;
    let peakEquity = equity;
    let maxDrawdownPercent = 0;
    let dailyPnL = 0;
    let lastTradeDay = -1;
    let lastTradeTime = 0;
    let tradeId = 0;

    const trades: BacktestTradeRecord[] = [];
    const equityCurve: BacktestEquityPoint[] = [{ timestamp: sorted[0].timestamp, equity, drawdownPercent: 0 }];

    for (const snapshot of sorted) {
      if (snapshot.prices.length < 2) continue;

      const day = Math.floor(snapshot.timestamp / 86400000);
      if (day !== lastTradeDay) { dailyPnL = 0; lastTradeDay = day; }
      if (dailyPnL <= -this.config.maxDailyLossUsd) continue;
      if (snapshot.timestamp - lastTradeTime < this.config.cooldownMs) continue;

      const opp = this.findBestOpportunity(snapshot);
      if (!opp || opp.spreadPercent < this.config.minSpreadPercent || equity < this.config.positionSizeUsd) continue;

      const positionSize = Math.min(this.config.positionSizeUsd, equity);
      const amount = positionSize / opp.buyPrice;

      const feesUsd = this.config.useFeeCalculator
        ? this.feeCalculator.calculateArbitrageFees(
            opp.buyExchange, opp.sellExchange, snapshot.symbol, opp.buyPrice, opp.sellPrice, amount
          ).totalFeesUsd
        : positionSize * this.config.flatFeeRate * 2;

      const slippageCostUsd = positionSize * (this.config.slippageBps / 10000) * 2;
      const grossProfitUsd = (opp.sellPrice - opp.buyPrice) * amount;
      const netProfitUsd = grossProfitUsd - feesUsd - slippageCostUsd;

      if (netProfitUsd <= 0) continue;

      equity += netProfitUsd;
      dailyPnL += netProfitUsd;
      lastTradeTime = snapshot.timestamp;

      if (equity > peakEquity) peakEquity = equity;
      const drawdownPercent = peakEquity > 0 ? ((peakEquity - equity) / peakEquity) * 100 : 0;
      if (drawdownPercent > maxDrawdownPercent) maxDrawdownPercent = drawdownPercent;

      trades.push({
        id: ++tradeId, timestamp: snapshot.timestamp, symbol: snapshot.symbol,
        buyExchange: opp.buyExchange, sellExchange: opp.sellExchange,
        buyPrice: opp.buyPrice, sellPrice: opp.sellPrice, amount,
        grossProfitUsd, feesUsd, slippageCostUsd, netProfitUsd, equityAfter: equity,
      });

      equityCurve.push({ timestamp: snapshot.timestamp, equity, drawdownPercent });
    }

    const metrics = this.calculateMetrics(trades, maxDrawdownPercent);
    getArbLogger().info(`[ArbBacktest] Complete: ${trades.length} trades, Net P&L: $${metrics.netProfitUsd.toFixed(2)}, Win Rate: ${metrics.winRate.toFixed(1)}%`);
    return { config: { ...this.config }, trades, equityCurve, metrics };
  }

  private findBestOpportunity(
    snapshot: MultiExchangePriceSnapshot
  ): { buyExchange: string; sellExchange: string; buyPrice: number; sellPrice: number; spreadPercent: number } | null {
    const { prices } = snapshot;
    let bestOpp = null;
    let bestSpread = 0;
    for (let i = 0; i < prices.length; i++) {
      for (let j = i + 1; j < prices.length; j++) {
        const a = prices[i], b = prices[j];
        if (a.price <= 0 || b.price <= 0) continue;
        const spread = Math.abs(a.price - b.price) / Math.min(a.price, b.price) * 100;
        if (spread > bestSpread) {
          bestSpread = spread;
          const buyIdx = a.price < b.price ? i : j;
          const sellIdx = a.price < b.price ? j : i;
          bestOpp = {
            buyExchange: prices[buyIdx].exchange, sellExchange: prices[sellIdx].exchange,
            buyPrice: prices[buyIdx].price, sellPrice: prices[sellIdx].price, spreadPercent: spread,
          };
        }
      }
    }
    return bestOpp;
  }

  private calculateMetrics(trades: BacktestTradeRecord[], maxDrawdownPercent: number): BacktestMetrics {
    if (trades.length === 0) return createEmptyBacktestMetrics();
    const wins = trades.filter(t => t.netProfitUsd > 0);
    const losses = trades.filter(t => t.netProfitUsd <= 0);
    const totalProfit = wins.reduce((s, t) => s + t.netProfitUsd, 0);
    const totalLoss = Math.abs(losses.reduce((s, t) => s + t.netProfitUsd, 0));
    const netProfitUsd = totalProfit - totalLoss;
    const totalFeesUsd = trades.reduce((s, t) => s + t.feesUsd, 0);
    const returns = trades.map(t => t.netProfitUsd / this.config.positionSizeUsd);
    const avgReturn = returns.reduce((s, r) => s + r, 0) / returns.length;
    const stdReturn = Math.sqrt(returns.reduce((s, r) => s + (r - avgReturn) ** 2, 0) / returns.length);
    const sharpeRatio = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(252) : 0;
    let maxConsWins = 0, maxConsLosses = 0, curWins = 0, curLosses = 0;
    for (const t of trades) {
      if (t.netProfitUsd > 0) { curWins++; curLosses = 0; maxConsWins = Math.max(maxConsWins, curWins); }
      else { curLosses++; curWins = 0; maxConsLosses = Math.max(maxConsLosses, curLosses); }
    }
    return {
      totalTrades: trades.length, winningTrades: wins.length, losingTrades: losses.length,
      winRate: (wins.length / trades.length) * 100, totalProfitUsd: totalProfit, totalFeesUsd, netProfitUsd,
      maxDrawdownPercent, sharpeRatio,
      profitFactor: totalLoss > 0 ? totalProfit / totalLoss : totalProfit > 0 ? Infinity : 0,
      avgTradeUsd: netProfitUsd / trades.length,
      avgWinUsd: wins.length > 0 ? totalProfit / wins.length : 0,
      avgLossUsd: losses.length > 0 ? totalLoss / losses.length : 0,
      maxConsecutiveWins: maxConsWins, maxConsecutiveLosses: maxConsLosses,
      returnOnCapital: (netProfitUsd / this.config.initialCapitalUsd) * 100,
    };
  }

  static generateTestData(params: {
    symbol: string; exchanges: string[]; basePrice: number; snapshots: number;
    intervalMs: number; volatilityPercent: number; spreadRangePercent: [number, number];
  }): MultiExchangePriceSnapshot[] {
    const data: MultiExchangePriceSnapshot[] = [];
    let currentPrice = params.basePrice;
    for (let i = 0; i < params.snapshots; i++) {
      const drift = (Math.random() - 0.5) * 2 * (params.volatilityPercent / 100) * currentPrice;
      currentPrice += drift;
      const prices: ExchangePricePoint[] = params.exchanges.map(exchange => {
        const spreadRange = params.spreadRangePercent[1] - params.spreadRangePercent[0];
        const randomSpread = (params.spreadRangePercent[0] + Math.random() * spreadRange) / 100;
        const direction = Math.random() > 0.5 ? 1 : -1;
        return { exchange, price: currentPrice * (1 + direction * randomSpread) };
      });
      data.push({ symbol: params.symbol, timestamp: Date.now() + i * params.intervalMs, prices });
    }
    return data;
  }

  getFeeCalculator(): FeeCalculator { return this.feeCalculator; }
  private emptyResult(): BacktestResult {
    return { config: { ...this.config }, trades: [], equityCurve: [], metrics: createEmptyBacktestMetrics() };
  }
}
