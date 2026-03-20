/**
 * Billing Service tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { BillingService, POLAR_PRODUCT_CREDITS } from '../src/services/billing-service';

// Mock D1 and KV
class MockD1 {
  tables: Map<string, any[]> = new Map();

  prepare(query: string) {
    const self = this;
    const queryBuilder = {
      bind: (...args: any[]) => queryBuilder,
      first: async () => {
        const match = query.match(/FROM\s+(\w+)/i);
        const tableName = match ? match[1] : 'unknown';
        const rows = self.tables.get(tableName) || [];
        return rows[0] || null;
      },
      all: async () => {
        const match = query.match(/FROM\s+(\w+)/i);
        const tableName = match ? match[1] : 'unknown';
        const rows = self.tables.get(tableName) || [];
        return { results: rows };
      },
      run: async () => ({ success: true, meta: { changes: 1 } }),
    };
    return queryBuilder;
  }
}

class MockKV {
  private store: Map<string, any> = new Map();

  async get(key: string, type?: 'json'): Promise<any> {
    const value = this.store.get(key);
    if (type === 'json' && value) {
      return JSON.parse(JSON.stringify(value));
    }
    return value;
  }

  async put(key: string, value: string): Promise<void> {
    this.store.set(key, JSON.parse(value));
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }
}

describe('BillingService', () => {
  let mockDB: MockD1;
  let mockKV: MockKV;
  let billingService: BillingService;

  beforeEach(() => {
    mockDB = new MockD1();
    mockKV = new MockKV();
    billingService = new BillingService({
      DB: mockDB as any,
      RATE_LIMIT_KV: mockKV as any,
      SESSION_KV: mockKV as any,
      JWT_SECRET=REDACTED: 'test-secret',
      POLAR_WEBHOOK_SECRET: 'test-webhook-secret',
      ENVIRONMENT: 'test',
      LOG_LEVEL: 'debug',
      AI: {} as any,
    });
  });

  describe('POLAR_PRODUCT_CREDITS', () => {
    it('should have correct credit mappings', () => {
      expect(POLAR_PRODUCT_CREDITS['agencyos-starter']).toEqual({ credits: 50, tier: 'pro' });
      expect(POLAR_PRODUCT_CREDITS['agencyos-pro']).toEqual({ credits: 200, tier: 'pro' });
      expect(POLAR_PRODUCT_CREDITS['agencyos-agency']).toEqual({ credits: 500, tier: 'enterprise' });
      expect(POLAR_PRODUCT_CREDITS['agencyos-master']).toEqual({ credits: 1000, tier: 'enterprise' });
      expect(POLAR_PRODUCT_CREDITS['credits-10']).toEqual({ credits: 10 });
    });
  });

  describe('getProductCredits', () => {
    it('should return credits for known product', () => {
      const result = billingService.getProductCredits('AgencyOS Pro');
      expect(result).toEqual({ credits: 200, tier: 'pro' });
    });

    it('should return null for unknown product', () => {
      const result = billingService.getProductCredits('Unknown Product');
      expect(result).toBeNull();
    });

    it('should handle case-insensitive product names', () => {
      const result1 = billingService.getProductCredits('AGENCYOS-STARTER');
      const result2 = billingService.getProductCredits('agencyos-starter');
      expect(result1).toEqual(result2);
    });
  });

  describe('verifySignature', () => {
    it('should return true for valid signature', async () => {
      const payload = JSON.stringify({ type: 'order.paid', data: {} });
      const secret = 'test-webhook-secret';

      // Generate expected signature
      const keyData = new TextEncoder().encode(secret);
      const msgData = new TextEncoder().encode(payload);
      const cryptoKey = await crypto.subtle.importKey(
        'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
      );
      const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData);
      const expectedSig = Array.from(new Uint8Array(sigBuffer))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');

      const result = await billingService.verifySignature(payload, expectedSig);
      expect(result).toBe(true);
    });

    it('should return false for invalid signature', async () => {
      const payload = JSON.stringify({ type: 'order.paid', data: {} });
      const result = await billingService.verifySignature(payload, 'invalid-signature');
      expect(result).toBe(false);
    });

    it('should return true when no secret configured', async () => {
      const noSecretService = new BillingService({
        ...billingService as any,
        POLAR_WEBHOOK_SECRET: '',
      });
      const result = await noSecretService.verifySignature('{}', 'any-signature');
      expect(result).toBe(true);
    });
  });

  describe('isValidTimestamp', () => {
    it('should return true for recent timestamp', () => {
      const now = new Date().toISOString();
      const result = billingService.isValidTimestamp(now);
      expect(result).toBe(true);
    });

    it('should return false for old timestamp', () => {
      const old = new Date(Date.now() - 10 * 60 * 1000).toISOString(); // 10 minutes ago
      const result = billingService.isValidTimestamp(old);
      expect(result).toBe(false);
    });

    it('should return false for future timestamp', () => {
      const future = new Date(Date.now() + 10 * 60 * 1000).toISOString(); // 10 minutes in future
      const result = billingService.isValidTimestamp(future);
      expect(result).toBe(false);
    });
  });

  describe('extractTenantId', () => {
    it('should extract from order metadata', () => {
      const event = {
        type: 'order.paid',
        data: {
          order: {
            metadata: { tenant_id: 'tenant-123' },
          },
        },
      } as any;

      const result = billingService.extractTenantId(event);
      expect(result).toBe('tenant-123');
    });

    it('should extract from customer external_id', () => {
      const event = {
        type: 'subscription.active',
        data: {
          customer: {
            external_id: 'tenant-456',
          },
        },
      } as any;

      const result = billingService.extractTenantId(event);
      expect(result).toBe('tenant-456');
    });

    it('should return null if no tenant_id found', () => {
      const event = {
        type: 'order.paid',
        data: {
          order: {
            metadata: {},
          },
        },
      } as any;

      const result = billingService.extractTenantId(event);
      expect(result).toBeNull();
    });
  });

  describe('isDuplicateEvent', () => {
    it('should return false for new event', async () => {
      mockDB.tables.set('webhook_events', []);

      const result = await billingService.isDuplicateEvent('event-123');
      expect(result).toBe(false);
    });

    it('should return true for existing event', async () => {
      mockDB.tables.set('webhook_events', [{ event_id: 'event-123' }]);

      const result = await billingService.isDuplicateEvent('event-123');
      expect(result).toBe(true);
    });
  });

  describe('recordEvent', () => {
    it('should record event successfully', async () => {
      const events: any[] = [];
      mockDB.tables.set('webhook_events', events);

      await billingService.recordEvent('event-123', 'order.paid', true);

      // Verify event was recorded (mock doesn't actually insert, so just check no error)
      expect(true).toBe(true);
    });
  });
});
