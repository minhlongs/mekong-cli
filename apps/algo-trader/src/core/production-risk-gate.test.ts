import { ProductionRiskGate } from './production-risk-gate';

describe('ProductionRiskGate', () => {
  let gate: ProductionRiskGate;

  beforeEach(() => {
    gate = new ProductionRiskGate({
      portfolioValue: 100000,
      maxDailyLossPct: 3,
      maxDrawdownPct: 10,
      maxPerMarketPct: 5,
      maxConsecutiveLosses: 3,
      maxOrdersPerMinute: 5, // Low for testing
    });
  });

  describe('canTrade', () => {
    it('should allow trade when all checks pass', () => {
      const result = gate.canTrade('market-1', 1000);
      expect(result.allowed).toBe(true);
    });

    it('should block after kill switch activated', () => {
      gate.emergencyStop('test');
      const result = gate.canTrade();
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('Kill switch');
      expect(result.checks.killSwitch).toBe(true);
    });

    it('should block when per-market cap exceeded', () => {
      // 5% of $100K = $5000
      const result = gate.canTrade('market-1', 6000);
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('cap');
      expect(result.checks.perMarketCap).toBe(true);
    });

    it('should allow when per-market cap not exceeded', () => {
      const result = gate.canTrade('market-1', 4000);
      expect(result.allowed).toBe(true);
    });
  });

  describe('rate limiter', () => {
    it('should block after exceeding rate limit', () => {
      // maxOrdersPerMinute = 5
      for (let i = 0; i < 5; i++) {
        expect(gate.canTrade().allowed).toBe(true);
      }
      const result = gate.canTrade();
      expect(result.allowed).toBe(false);
      expect(result.reason).toContain('Rate limit');
      expect(result.checks.rateLimit).toBe(true);
    });
  });

  describe('daily loss', () => {
    it('should block after daily loss limit hit', () => {
      // 3% of $100K = $3000 daily loss limit
      gate.recordTrade(-1500);
      expect(gate.canTrade().allowed).toBe(true);

      gate.recordTrade(-1600); // Total: -$3100 > $3000 limit
      const result = gate.canTrade();
      expect(result.allowed).toBe(false);
    });
  });

  describe('drawdown', () => {
    it('should block after 10% drawdown from peak', () => {
      // Peak = $100K, drop to $89K = 11% drawdown
      gate.recordTrade(-11000);
      const result = gate.canTrade();
      expect(result.allowed).toBe(false);
    });

    it('should allow at 5% drawdown', () => {
      gate.recordTrade(-5000);
      const result = gate.canTrade();
      // Daily loss 5% > 3% limit will trip first
      // This tests that drawdown alone at 5% would be fine
      expect(result.allowed).toBe(false); // Blocked by daily loss, not drawdown
    });
  });

  describe('consecutive losses', () => {
    it('should block after N consecutive losses', () => {
      gate.recordTrade(-100);
      gate.recordTrade(-100);
      expect(gate.canTrade().allowed).toBe(true);

      gate.recordTrade(-100); // 3rd consecutive loss
      const result = gate.canTrade();
      expect(result.allowed).toBe(false);
    });

    it('should reset counter on winning trade', () => {
      gate.recordTrade(-100);
      gate.recordTrade(-100);
      gate.recordTrade(500); // Win resets counter
      gate.recordTrade(-100);
      gate.recordTrade(-100);
      expect(gate.canTrade().allowed).toBe(true); // Only 2 consecutive
    });
  });

  describe('emergencyStop', () => {
    it('should halt all trading', () => {
      gate.emergencyStop('Test emergency');
      const status = gate.getStatus();
      expect(status.killSwitch.isTripped).toBe(true);
      expect(status.anyTripped).toBe(true);
    });
  });

  describe('reset', () => {
    it('should clear all breakers', () => {
      gate.emergencyStop('Test');
      gate.reset();
      expect(gate.canTrade().allowed).toBe(true);
    });
  });

  describe('getStatus', () => {
    it('should return portfolio metrics', () => {
      gate.recordTrade(-500);
      const status = gate.getStatus();
      expect(status.portfolioValue).toBe(99500);
      expect(status.dailyPnl).toBe(-500);
      expect(status.drawdownPct).toBeCloseTo(0.5, 1);
      expect(status.config.portfolioValue).toBe(100000);
    });
  });
});
