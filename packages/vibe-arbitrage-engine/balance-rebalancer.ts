/**
 * BalanceRebalancer — Cross-exchange balance management for arbitrage.
 */

import { getArbLogger } from './arb-logger';
import {
  ExchangeBalance, BalanceSnapshot, TransferSuggestion,
  TransferRecord, ImbalanceReport, RebalancerConfig, DEFAULT_REBALANCER_CONFIG,
} from './balance-rebalancer-types';

export * from './balance-rebalancer-types';

const logger = getArbLogger();

export class BalanceRebalancer {
  private config: RebalancerConfig;
  private currentBalances: Map<string, ExchangeBalance[]> = new Map();
  private snapshots: BalanceSnapshot[] = [];
  private transfers: TransferRecord[] = [];
  private transferCounter = 0;

  constructor(config?: Partial<RebalancerConfig>) {
    this.config = { ...DEFAULT_REBALANCER_CONFIG, ...config };
  }

  updateBalances(exchange: string, balances: ExchangeBalance[]): void {
    this.currentBalances.set(exchange, balances);
  }

  takeSnapshot(): BalanceSnapshot {
    const allBalances: ExchangeBalance[] = [];
    let totalValueUsd = 0;

    for (const balances of this.currentBalances.values()) {
      for (const b of balances) {
        allBalances.push(b);
        totalValueUsd += b.valueUsd;
      }
    }

    const snapshot: BalanceSnapshot = { timestamp: Date.now(), balances: allBalances, totalValueUsd };
    this.snapshots.push(snapshot);
    if (this.snapshots.length > this.config.maxHistorySize) {
      this.snapshots.splice(0, this.snapshots.length - this.config.maxHistorySize);
    }
    return snapshot;
  }

  detectImbalance(currency: string): ImbalanceReport {
    const exchanges: { exchange: string; available: number; valueUsd: number; sharePercent: number }[] = [];
    let totalValue = 0;

    for (const [exchange, balances] of this.currentBalances) {
      const bal = balances.find(b => b.currency === currency);
      const available = bal?.available || 0;
      const valueUsd = bal?.valueUsd || 0;
      totalValue += valueUsd;
      exchanges.push({ exchange, available, valueUsd, sharePercent: 0 });
    }

    for (const e of exchanges) {
      e.sharePercent = totalValue > 0 ? (e.valueUsd / totalValue) * 100 : 0;
    }

    const shares = exchanges.map(e => e.sharePercent);
    const maxShare = shares.length > 0 ? Math.max(...shares) : 0;
    const minShare = shares.length > 0 ? Math.min(...shares) : 0;
    const imbalancePercent = maxShare - minShare;

    return {
      currency, exchanges, maxSharePercent: maxShare, minSharePercent: minShare,
      imbalancePercent, isImbalanced: imbalancePercent > this.config.imbalanceThresholdPercent,
    };
  }

  suggestTransfers(currency: string): TransferSuggestion[] {
    const report = this.detectImbalance(currency);
    if (!report.isImbalanced || report.exchanges.length < 2) return [];

    const suggestions: TransferSuggestion[] = [];
    const targetShare = this.config.targetSharePercent > 0
      ? this.config.targetSharePercent : 100 / report.exchanges.length;

    const totalValue = report.exchanges.reduce((s, e) => s + e.valueUsd, 0);
    const targetValue = totalValue * (targetShare / 100);

    const overAllocated = report.exchanges.filter(e => e.valueUsd > targetValue).sort((a, b) => b.valueUsd - a.valueUsd);
    const underAllocated = report.exchanges.filter(e => e.valueUsd < targetValue).sort((a, b) => a.valueUsd - b.valueUsd);

    for (const over of overAllocated) {
      const excessUsd = over.valueUsd - targetValue;
      if (excessUsd < this.config.minTransferUsd) continue;

      for (const under of underAllocated) {
        const deficitUsd = targetValue - under.valueUsd;
        if (deficitUsd < this.config.minTransferUsd) continue;

        const transferUsd = Math.min(excessUsd, deficitUsd);
        const transferAmount = over.available > 0 ? (transferUsd / over.valueUsd) * over.available : 0;
        if (transferAmount <= 0) continue;

        const priority = report.imbalancePercent > 60 ? 'high' : report.imbalancePercent > 40 ? 'medium' : 'low';
        suggestions.push({
          fromExchange: over.exchange, toExchange: under.exchange, currency,
          amount: transferAmount, valueUsd: transferUsd,
          reason: `Rebalance ${currency}: ${over.exchange} has ${over.sharePercent.toFixed(1)}%, ${under.exchange} has ${under.sharePercent.toFixed(1)}%`,
          priority,
        });
      }
    }
    return suggestions;
  }

  recordTransfer(from: string, to: string, currency: string, amount: number, valueUsd: number): TransferRecord {
    const record: TransferRecord = {
      id: ++this.transferCounter, timestamp: Date.now(),
      fromExchange: from, toExchange: to, currency, amount, valueUsd, status: 'pending',
    };
    this.transfers.push(record);
    logger.info(`[Rebalancer] Transfer #${record.id}: ${amount} ${currency} ${from}→${to} ($${valueUsd.toFixed(2)})`);
    return record;
  }

  updateTransferStatus(id: number, status: TransferRecord['status']): void {
    const transfer = this.transfers.find(t => t.id === id);
    if (transfer) transfer.status = status;
  }

  getTrackedCurrencies(): string[] {
    const currencies = new Set<string>();
    for (const balances of this.currentBalances.values()) {
      for (const b of balances) currencies.add(b.currency);
    }
    return Array.from(currencies);
  }

  getAllImbalances(): ImbalanceReport[] {
    return this.getTrackedCurrencies().map(c => this.detectImbalance(c));
  }

  getTransferHistory(): TransferRecord[] { return [...this.transfers]; }
  getSnapshots(): BalanceSnapshot[] { return [...this.snapshots]; }
  getExchangeCount(): number { return this.currentBalances.size; }

  clear(): void {
    this.currentBalances.clear();
    this.snapshots = [];
    this.transfers = [];
  }
}
