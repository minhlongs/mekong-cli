import { describe, it, expect, beforeEach } from 'vitest';
import {
  wireAdapterToOrchestrator,
  wireRdToAgi,
  wireMarketplaceToBilling,
  getWiringReport,
} from '../wiring.js';

// Reset module registry between tests via re-import is complex with ESM;
// instead verify idempotent behaviour and accumulation.

describe('wiring', () => {
  describe('wireAdapterToOrchestrator', () => {
    it('returns connected status', () => {
      const status = wireAdapterToOrchestrator();
      expect(status.connected).toBe(true);
      expect(status.source).toBe('@openclaw/cli-adapter');
      expect(status.target).toBe('@openclaw/cli-orchestrator');
      expect(status.lastSync).toBeInstanceOf(Date);
    });

    it('is idempotent — repeated calls stay connected', () => {
      wireAdapterToOrchestrator();
      const status = wireAdapterToOrchestrator();
      expect(status.connected).toBe(true);
    });
  });

  describe('wireRdToAgi', () => {
    it('returns connected status with correct source/target', () => {
      const status = wireRdToAgi();
      expect(status.connected).toBe(true);
      expect(status.source).toBe('@openclaw/rd-engine');
      expect(status.target).toBe('@openclaw/agi-evolution');
    });
  });

  describe('wireMarketplaceToBilling', () => {
    it('returns connected status', () => {
      const status = wireMarketplaceToBilling();
      expect(status.connected).toBe(true);
      expect(status.source).toBe('@openclaw/raas-marketplace');
      expect(status.target).toBe('@openclaw/billing');
    });
  });

  describe('getWiringReport', () => {
    beforeEach(() => {
      wireAdapterToOrchestrator();
      wireRdToAgi();
      wireMarketplaceToBilling();
    });

    it('includes all three integrations', () => {
      const report = getWiringReport();
      expect(report.totalCount).toBeGreaterThanOrEqual(3);
    });

    it('healthyCount matches connected integrations', () => {
      const report = getWiringReport();
      expect(report.healthyCount).toBe(report.totalCount);
    });

    it('returns a new array on each call', () => {
      const report1 = getWiringReport();
      const report2 = getWiringReport();
      expect(report1.integrations).not.toBe(report2.integrations);
    });
  });
});
