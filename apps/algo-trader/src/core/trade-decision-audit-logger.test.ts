import { TradeDecisionAuditLogger } from './trade-decision-audit-logger';
import * as fs from 'fs';
import * as path from 'path';

const AUDIT_PATH = path.resolve(process.cwd(), 'data', 'audit-log.json');

describe('TradeDecisionAuditLogger', () => {
  beforeEach(() => {
    try { if (fs.existsSync(AUDIT_PATH)) fs.unlinkSync(AUDIT_PATH); } catch {}
  });

  it('should log a trade decision', () => {
    const logger = new TradeDecisionAuditLogger();
    logger.log({
      action: 'BUY', tokenId: 'tok-1', marketId: 'mkt-1', side: 'YES',
      price: 0.55, size: 100, notional: 55,
      reasoning: 'AI confidence 0.8, edge 15%', strategy: 'AIReasoning',
      riskCheck: { allowed: true }, confidence: 0.8, mode: 'LIVE',
    });

    const entries = logger.getRecent(10);
    expect(entries).toHaveLength(1);
    expect(entries[0].action).toBe('BUY');
    expect(entries[0].reasoning).toContain('AI confidence');
  });

  it('should log rejected trades', () => {
    const logger = new TradeDecisionAuditLogger();
    logger.log({
      action: 'REJECT', tokenId: 'tok-1', marketId: 'mkt-1', side: 'YES',
      price: 0.55, size: 100, notional: 55,
      reasoning: 'Daily loss limit hit', strategy: 'MakerBot',
      riskCheck: { allowed: false, reason: 'Daily loss 3% exceeded' },
      confidence: 0.6, mode: 'LIVE',
    });

    const stats = logger.getStats();
    expect(stats.rejects).toBe(1);
    expect(stats.buys).toBe(0);
  });

  it('should persist to file and reload', () => {
    const logger1 = new TradeDecisionAuditLogger();
    logger1.log({
      action: 'SELL', tokenId: 'tok-2', marketId: 'mkt-2', side: 'NO',
      price: 0.40, size: 50, notional: 20,
      reasoning: 'Stop-loss triggered', strategy: 'WeatherBot',
      riskCheck: { allowed: true }, confidence: 0.3, mode: 'PAPER',
    });

    // New instance should load from file
    const logger2 = new TradeDecisionAuditLogger();
    expect(logger2.getRecent(10)).toHaveLength(1);
    expect(logger2.getRecent(10)[0].tokenId).toBe('tok-2');
  });

  it('should return stats correctly', () => {
    const logger = new TradeDecisionAuditLogger();
    const base = { tokenId: 't', marketId: 'm', side: 'YES' as const, price: 0.5, size: 10, notional: 5, reasoning: '', strategy: 's', riskCheck: { allowed: true }, confidence: 0.5, mode: 'LIVE' as const };

    logger.log({ ...base, action: 'BUY' });
    logger.log({ ...base, action: 'BUY' });
    logger.log({ ...base, action: 'SELL' });
    logger.log({ ...base, action: 'REJECT', riskCheck: { allowed: false } });

    const stats = logger.getStats();
    expect(stats.total).toBe(4);
    expect(stats.buys).toBe(2);
    expect(stats.sells).toBe(1);
    expect(stats.rejects).toBe(1);
    expect(stats.liveCount).toBe(4);
  });

  it('should filter by token', () => {
    const logger = new TradeDecisionAuditLogger();
    const base = { marketId: 'm', side: 'YES' as const, price: 0.5, size: 10, notional: 5, reasoning: '', strategy: 's', riskCheck: { allowed: true }, confidence: 0.5, mode: 'DRY_RUN' as const, action: 'BUY' as const };

    logger.log({ ...base, tokenId: 'tok-A' });
    logger.log({ ...base, tokenId: 'tok-B' });
    logger.log({ ...base, tokenId: 'tok-A' });

    expect(logger.getByToken('tok-A')).toHaveLength(2);
    expect(logger.getByToken('tok-B')).toHaveLength(1);
  });
});
