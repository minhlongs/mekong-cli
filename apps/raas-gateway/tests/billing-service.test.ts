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
    // Secret must be valid base64 for Standard Webhooks
    const testSecretBase64 = btoa('test-webhook-secret-key-32bytes!!');
    billingService = new BillingService({
      DB: mockDB as any,
      RATE_LIMIT_KV: mockKV as any,
      SESSION_KV: mockKV as any,
      JWT_SECRET=REDACTED: 'test-secret',
      POLAR_WEBHOOK_SECRET: testSecretBase64,
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
    it('should return true for valid Standard Webhooks signature', async () => {
      const secretRaw = 'test-webhook-secret-key-32bytes!!';
      const secretBase64 = btoa(secretRaw);
      const payload = JSON.stringify({ type: 'order.paid', data: {} });
      const webhookId = 'msg_test123';
      const webhookTimestamp = Math.floor(Date.now() / 1000).toString();

      // Generate Standard Webhooks signature using same decoding as service
      const keyBytes = Uint8Array.from(atob(secretBase64), c => c.charCodeAt(0));
      const signedContent = `${webhookId}.${webhookTimestamp}.${payload}`;
      const msgData = new TextEncoder().encode(signedContent);
      const cryptoKey = await crypto.subtle.importKey(
        'raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
      );
      const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData);
      const sigBase64 = btoa(String.fromCharCode(...new Uint8Array(sigBuffer)));

      const result = await billingService.verifySignature(
        payload, `v1,${sigBase64}`, webhookId, webhookTimestamp
      );
      expect(result).toBe(true);
    });

    it('should return false for invalid signature', async () => {
      const payload = JSON.stringify({ type: 'order.paid', data: {} });
      const result = await billingService.verifySignature(payload, 'v1,invalid', 'msg_1', '123');
      expect(result).toBe(false);
    });

    it('should return false when no secret configured (fail closed)', async () => {
      const noSecretService = new BillingService({
        DB: mockDB as any,
        RATE_LIMIT_KV: mockKV as any,
        SESSION_KV: mockKV as any,
        JWT_SECRET=REDACTED: 'test-secret',
        POLAR_WEBHOOK_SECRET: '',
        ENVIRONMENT: 'test',
        LOG_LEVEL: 'debug',
        AI: {} as any,
      });
      const result = await noSecretService.verifySignature('{}', 'any-signature');
      expect(result).toBe(false);
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
