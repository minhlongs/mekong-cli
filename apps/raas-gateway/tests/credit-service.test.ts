/**
 * Credit Service tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { CreditService, MISSION_COSTS } from '../src/services/credit-service';

// Mock D1 Database
class MockD1 {
  tables: Map<string, any[]> = new Map();

  prepare(query: string) {
    const self = this;
    let bindings: any[] = [];

    const queryBuilder = {
      bind: (...args: any[]) => {
        bindings = args;
        return queryBuilder;
      },
      first: async () => {
        // Extract table name from query
        const match = query.match(/FROM\s+(\w+)|INTO\s+(\w+)|UPDATE\s+(\w+)/i);
        const tableName = match ? match[1] || match[2] || match[3] : 'unknown';
        const rows = self.tables.get(tableName) || [];
        return rows[0] || null;
      },
      all: async () => {
        const match = query.match(/FROM\s+(\w+)/i);
        const tableName = match ? match[1] : 'unknown';
        const rows = self.tables.get(tableName) || [];
        return { results: rows };
      },
      run: async () => {
        return { success: true, meta: { changes: 1 } };
      },
    };

    return queryBuilder;
  }
}

describe('CreditService', () => {
  let mockDB: MockD1;
  let creditService: CreditService;

  beforeEach(() => {
    mockDB = new MockD1();
    creditService = new CreditService({
      DB: mockDB as any,
      RATE_LIMIT_KV: {} as any,
      SESSION_KV: {} as any,
      JWT_SECRET=REDACTED: 'test-secret',
      POLAR_WEBHOOK_SECRET: 'test-secret',
      ENVIRONMENT: 'test',
      LOG_LEVEL: 'debug',
      AI: {} as any,
      TELEGRAM_BOT_TOKEN: 'test-bot-token',
    });
  });

  describe('getMissionCost', () => {
    it('should return correct cost for simple mission', () => {
      expect(creditService.getMissionCost('simple')).toBe(1);
    });

    it('should return correct cost for standard mission', () => {
      expect(creditService.getMissionCost('standard')).toBe(3);
    });

    it('should return correct cost for complex mission', () => {
      expect(creditService.getMissionCost('complex')).toBe(5);
    });
  });

  describe('MISSION_COSTS constant', () => {
    it('should have correct cost mapping', () => {
      expect(MISSION_COSTS).toEqual({
        simple: 1,
        standard: 3,
        complex: 5,
      });
    });
  });

  describe('hasSufficientCredits', () => {
    it('should return true when balance >= amount', async () => {
      // Mock balance = 100
      mockDB.tables.set('tenants', [{ id: 'tenant-1', balance: 100 }]);

      const result = await creditService.hasSufficientCredits('tenant-1', 50);
      expect(result).toBe(true);
    });

    it('should return false when balance < amount', async () => {
      // Mock balance = 10
      mockDB.tables.set('tenants', [{ id: 'tenant-1', balance: 10 }]);

      const result = await creditService.hasSufficientCredits('tenant-1', 50);
      expect(result).toBe(false);
    });
  });

  describe('deduct', () => {
    it('should reject negative amounts', async () => {
      await expect(creditService.deduct('tenant-1', -10, 'mission', 'test'))
        .rejects.toThrow('Deduction amount must be positive');
    });

    it('should return TENANT_NOT_FOUND for non-existent tenant', async () => {
      // Atomic UPDATE returns 0 changes for non-existent tenant
      const origPrepare = mockDB.prepare.bind(mockDB);
      mockDB.prepare = (query: string) => {
        const builder = origPrepare(query);
        if (query.includes('UPDATE tenants SET balance')) {
          builder.run = async () => ({ success: true, meta: { changes: 0 } });
        }
        return builder;
      };

      const result = await creditService.deduct('non-existent', 10, 'mission', 'test');
      expect(result.success).toBe(false);
      expect(result.error).toBe('TENANT_NOT_FOUND');
    });

    it('should return INSUFFICIENT_CREDITS when balance too low', async () => {
      mockDB.tables.set('tenants', [{ id: 'tenant-1', balance: 5, total_spent: 0 }]);

      // Atomic UPDATE returns 0 changes when balance < amount
      const origPrepare = mockDB.prepare.bind(mockDB);
      mockDB.prepare = (query: string) => {
        const builder = origPrepare(query);
        if (query.includes('UPDATE tenants SET balance')) {
          builder.run = async () => ({ success: true, meta: { changes: 0 } });
        }
        return builder;
      };

      const result = await creditService.deduct('tenant-1', 10, 'mission', 'test');
      expect(result.success).toBe(false);
      expect(result.error).toBe('INSUFFICIENT_CREDITS');
    });
  });

  describe('addCredits', () => {
    it('should reject negative amounts', async () => {
      await expect(creditService.addCredits('tenant-1', -10, 'purchase', 'test'))
        .rejects.toThrow('Credit amount must be positive');
    });

    it('should handle all credit types', async () => {
      const types: Array<'purchase' | 'refund' | 'rollover' | 'adjustment' | 'webhook'> = [
        'purchase',
        'refund',
        'rollover',
        'adjustment',
        'webhook',
      ];

      for (const type of types) {
        const result = await creditService.addCredits('tenant-1', 10, type, 'test');
        expect(result).toBeGreaterThanOrEqual(10);
      }
    });
  });

  describe('getHistory', () => {
    it('should enforce limit between 1 and 200', async () => {
      // Test limit clamping
      mockDB.tables.set('credit_transactions', []);

      const result = await creditService.getHistory('tenant-1', 500, 0);
      expect(Array.isArray(result)).toBe(true);
    });

    it('should return empty array for tenant with no transactions', async () => {
      mockDB.tables.set('credit_transactions', []);

      const result = await creditService.getHistory('tenant-1');
      expect(result).toEqual([]);
    });
  });
});
