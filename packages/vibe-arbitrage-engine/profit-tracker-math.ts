/**
 * ProfitTracker mathematical and reporting utilities.
 */

import { getArbLogger } from './arb-logger';
import { EquityPoint, PerformanceSummary } from './profit-tracker-types';

const logger = getArbLogger();

export function computeEquityReturns(equityCurve: EquityPoint[], windowSize: number): number[] {
  const points = equityCurve.slice(-windowSize - 1);
  if (points.length < 2) return [];

  const returns: number[] = [];
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1].equity;
    if (prev > 0) {
      returns.push((points[i].equity - prev) / prev);
    }
  }
  return returns;
}

export function calculateSharpeRatio(returns: number[], riskFreeRate: number): number {
  if (returns.length < 2) return 0;

  const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
  const variance = returns.reduce((s, r) => s + (r - mean) ** 2, 0) / returns.length;
  const stddev = Math.sqrt(variance);

  if (stddev === 0) return 0;

  const tradesPerYear = 2500;
  const annualizedReturn = mean * tradesPerYear;
  const annualizedStddev = stddev * Math.sqrt(tradesPerYear);

  return (annualizedReturn - riskFreeRate) / annualizedStddev;
}

export function calculateSortinoRatio(returns: number[], riskFreeRate: number): number {
  if (returns.length < 2) return 0;

  const mean = returns.reduce((s, r) => s + r, 0) / returns.length;
  const downsideReturns = returns.filter(r => r < 0);

  if (downsideReturns.length === 0) return mean > 0 ? Infinity : 0;

  const downsideVariance = downsideReturns.reduce((s, r) => s + r ** 2, 0) / downsideReturns.length;
  const downsideStddev = Math.sqrt(downsideVariance);

  if (downsideStddev === 0) return 0;

  const tradesPerYear = 2500;
  const annualizedReturn = mean * tradesPerYear;
  const annualizedDownside = downsideStddev * Math.sqrt(tradesPerYear);

  return (annualizedReturn - riskFreeRate) / annualizedDownside;
}

export function printPerformanceReport(s: PerformanceSummary): void {
  logger.info('\n╔══════════════════════════════════════╗');
  logger.info('║      📊 PROFIT TRACKER REPORT        ║');
  logger.info('╠══════════════════════════════════════╣');
  logger.info(`║ Equity:     $${s.currentEquity.toFixed(2).padEnd(22)}║`);
  logger.info(`║ P&L:        $${s.cumulativePnl.toFixed(2).padEnd(22)}║`);
  logger.info(`║ P&L %:      ${s.cumulativePnlPercent.toFixed(2).padEnd(22)}%║`);
  logger.info(`║ Max DD:     ${s.maxDrawdownPercent.toFixed(2).padEnd(22)}%║`);
  logger.info(`║ Sharpe:     ${s.sharpeRatio.toFixed(2).padEnd(23)}║`);
  logger.info(`║ Sortino:    ${s.sortinoRatio.toFixed(2).padEnd(23)}║`);
  logger.info(`║ Win Rate:   ${s.winRate.toFixed(1).padEnd(22)}%║`);
  logger.info(`║ Trades:     ${String(s.totalTrades).padEnd(23)}║`);
  logger.info(`║ Profit F:   ${(s.profitFactor === Infinity ? '∞' : s.profitFactor.toFixed(2)).padEnd(23)}║`);
  logger.info('╚══════════════════════════════════════╝\n');
}
