import { sopDailyHealthCheck, sopStrategyLifecycle, sopCapitalScaling, sopEmergencyProtocol, SOPRunner } from './business-sop-engine';
import { ProductionRiskGate } from './production-risk-gate';
import { TradeDecisionAuditLogger } from './trade-decision-audit-logger';
import * as fs from 'fs';
import * as path from 'path';

const AUDIT_PATH = path.resolve(process.cwd(), 'data', 'audit-log.json');

describe('Business SOP Engine', () => {
  beforeEach(() => {
    try { if (fs.existsSync(AUDIT_PATH)) fs.unlinkSync(AUDIT_PATH); } catch {}
  });

  describe('sopDailyHealthCheck', () => {
    it('should return GREEN when all healthy', () => {
      const gate = new ProductionRiskGate({ portfolioValue: 100000 });
      const result = sopDailyHealthCheck(gate);
      expect(result.decision).toBe('GREEN');
      expect(result.actions[0]).toContain('Continue');
    });

    it('should return RED when circuit breaker tripped', () => {
      const gate = new ProductionRiskGate({ portfolioValue: 100000 });
      gate.emergencyStop('test');
      const result = sopDailyHealthCheck(gate);
      expect(result.decision).toBe('RED');
      expect(result.actions[0]).toContain('HALT');
    });

    it('should return ORANGE on >5% drawdown', () => {
      const gate = new ProductionRiskGate({ portfolioValue: 100000, maxDrawdownPct: 20, maxDailyLossPct: 10 });
      gate.recordTrade(-6000); // 6% drawdown
      const result = sopDailyHealthCheck(gate);
      expect(result.decision).toBe('ORANGE');
    });
  });

  describe('sopStrategyLifecycle', () => {
    it('should PROMOTE high-performing strategy', () => {
      const result = sopStrategyLifecycle([
        { name: 'MakerBot', sharpe: 2.5, winRate: 0.65, totalPnl: 5000, drawdownPct: 3, tradeCount: 100 },
      ]);
      expect(result.decision).toContain('PROMOTE');
    });

    it('should KILL underperforming strategy', () => {
      const result = sopStrategyLifecycle([
        { name: 'WeatherBot', sharpe: 0.3, winRate: 0.4, totalPnl: -2000, drawdownPct: 18, tradeCount: 50 },
      ]);
      expect(result.decision).toContain('KILL');
    });

    it('should KEEP strategy with insufficient data', () => {
      const result = sopStrategyLifecycle([
        { name: 'NewBot', sharpe: 0.1, winRate: 0.3, totalPnl: -100, drawdownPct: 5, tradeCount: 10 },
      ]);
      expect(result.decision).toContain('KEEP');
    });
  });

  describe('sopCapitalScaling', () => {
    it('should SCALE_UP on strong performance', () => {
      const result = sopCapitalScaling(50000, 6000, 3, 22);
      expect(result.decision).toBe('SCALE_UP');
    });

    it('should HALT on >10% drawdown', () => {
      const result = sopCapitalScaling(100000, -5000, 12, 0);
      expect(result.decision).toBe('HALT');
    });

    it('should SCALE_DOWN on negative return', () => {
      const result = sopCapitalScaling(100000, -3000, 8, 5);
      expect(result.decision).toBe('SCALE_DOWN');
    });

    it('should HOLD in normal conditions', () => {
      const result = sopCapitalScaling(100000, 3000, 4, 15);
      expect(result.decision).toBe('HOLD');
    });
  });

  describe('sopEmergencyProtocol', () => {
    it('should trigger RED on >10% drawdown', () => {
      const gate = new ProductionRiskGate({ portfolioValue: 100000 });
      const result = sopEmergencyProtocol(gate, 12, 2);
      expect(result.decision).toBe('RED');
      expect(result.actions[0]).toContain('KILL SWITCH');
    });

    it('should trigger GREEN in normal conditions', () => {
      const gate = new ProductionRiskGate({ portfolioValue: 100000 });
      const result = sopEmergencyProtocol(gate, 2, 1);
      expect(result.decision).toBe('GREEN');
    });
  });

  describe('SOPRunner', () => {
    it('should record decisions in history', () => {
      const gate = new ProductionRiskGate({ portfolioValue: 100000 });
      const audit = new TradeDecisionAuditLogger();
      const runner = new SOPRunner(gate, audit);

      runner.runDailyHealth();
      runner.runStrategyLifecycle([{ name: 'Test', sharpe: 1.5, winRate: 0.55, totalPnl: 1000, drawdownPct: 2, tradeCount: 30 }]);

      expect(runner.getHistory()).toHaveLength(2);
      expect(runner.getHistory()[0].sop).toBe('DAILY_HEALTH_CHECK');
      expect(runner.getHistory()[1].sop).toBe('STRATEGY_LIFECYCLE');
    });
  });
});
