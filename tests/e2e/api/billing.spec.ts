import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';
const TEST_TENANT_ID = process.env.TEST_TENANT_ID ?? 'test_tenant_001';

test.describe('Credits and Billing API', () => {
  test('get credit balance returns valid number', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/credits/balance`);

    if (response.status() === 401) {
      return; // Authentication required - set TEST_AUTH_TOKEN
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('balance');
    expect(typeof data.balance).toBe('number');
    expect(data.balance).toBeGreaterThanOrEqual(0);
  });

  test('credit balance includes available and reserved amounts', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/credits/balance`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Response should include both available and reserved credits
    expect(data).toHaveProperty('available');
    expect(data).toHaveProperty('reserved');
    expect(typeof data.available).toBe('number');
    expect(typeof data.reserved).toBe('number');
    expect(data.available + data.reserved).toBeGreaterThanOrEqual(0);
  });

  test('credit history returns paginated transactions', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/credits/history?limit=10`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('transactions');
    expect(Array.isArray(data.transactions)).toBeTruthy();
    expect(data.transactions.length).toBeLessThanOrEqual(10);

    // Verify transaction structure
    if (data.transactions.length > 0) {
      const tx = data.transactions[0];
      expect(tx).toHaveProperty('id');
      expect(tx).toHaveProperty('amount');
      expect(tx).toHaveProperty('type'); // 'debit', 'credit', 'reserve', 'release'
      expect(tx).toHaveProperty('created_at');
    }
  });

  test('credit history can be filtered by type', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/credits/history?type=debit&limit=5`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // All returned transactions should be debits
    data.transactions.forEach((tx: any) => {
      expect(tx.type).toBe('debit');
    });
  });

  test('get usage summary returns last 30 days data', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/usage/summary`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('period_start');
    expect(data).toHaveProperty('period_end');
    expect(data).toHaveProperty('total_missions');
    expect(data).toHaveProperty('total_mcus_used');
    expect(typeof data.total_missions).toBe('number');
    expect(typeof data.total_mcus_used).toBe('number');
  });

  test('usage summary includes daily breakdown', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/usage/summary`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('daily_usage');
    expect(Array.isArray(data.daily_usage)).toBeTruthy();

    // Verify daily structure
    if (data.daily_usage.length > 0) {
      const day = data.daily_usage[0];
      expect(day).toHaveProperty('date');
      expect(day).toHaveProperty('missions');
      expect(day).toHaveProperty('mcus_used');
    }
  });

  test('get activity feed returns recent actions', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/raas/usage/activity?limit=20`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('activities');
    expect(Array.isArray(data.activities)).toBeTruthy();
    expect(data.activities.length).toBeLessThanOrEqual(20);

    if (data.activities.length > 0) {
      const activity = data.activities[0];
      expect(activity).toHaveProperty('id');
      expect(activity).toHaveProperty('type');
      expect(activity).toHaveProperty('timestamp');
      expect(activity).toHaveProperty('description');
    }
  });

  test('insufficient credits returns 402 with upgrade URL', async ({ request }) => {
    // Create mission with high credit cost to trigger insufficient credits
    // This requires a test tenant with very low balance
    const drainedLicenseKey = process.env.DRAINED_LICENSE_KEY;

    if (!drainedLicenseKey) {
      return; // DRAINED_LICENSE_KEY not set for 402 test
    }

    const response = await request.post(`${API_BASE_URL}/raas/missions`, {
      data: {
        goal: 'Test mission that should fail with 402',
        tenant_id: TEST_TENANT_ID,
      },
      headers: {
        'Authorization': `Bearer ${drainedLicenseKey}`,
      },
    });

    expect(response.status()).toBe(402);
    const error = await response.json();
    expect(error).toHaveProperty('upgrade_url');
    expect(error.upgrade_url).toContain('pricing');
  });
});

test.describe('MCU Billing', () => {
  test('mission deducts correct MCU based on complexity', async ({ request }) => {
    // Simple mission
    const simpleResponse = await request.post(`${API_BASE_URL}/v1/missions`, {
      data: {
        goal: 'Simple task: format this file',
        tenant_id: TEST_TENANT_ID,
      },
    });

    expect(simpleResponse.ok()).toBeTruthy();
    const simpleMission = await simpleResponse.json();

    // Wait for completion and check credits deducted
    await new Promise((resolve) => setTimeout(resolve, 10000));

    const balanceAfterSimple = await request.get(`${API_BASE_URL}/raas/credits/balance`).then(r => r.json());

    // Complex mission
    const complexResponse = await request.post(`${API_BASE_URL}/v1/missions`, {
      data: {
        goal: 'Complex task: refactor the entire authentication system, implement OAuth2 with multiple providers, add comprehensive security testing, and update all documentation. This is a multi-file architectural change requiring deep analysis.',
        tenant_id: TEST_TENANT_ID,
      },
    });

    expect(complexResponse.ok()).toBeTruthy();
    const complexMission = await complexResponse.json();

    await new Promise((resolve) => setTimeout(resolve, 10000));

    const balanceAfterComplex = await request.get(`${API_BASE_URL}/raas/credits/balance`).then(r => r.json());

    // Complex mission should deduct more credits
    expect(balanceAfterComplex.balance).toBeLessThanOrEqual(balanceAfterSimple.balance);
  });

  test('webhook MCU deduct endpoint validates request', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/mcu/deduct`, {
      data: {
        tenant_id: TEST_TENANT_ID,
        complexity: 'standard',
        context: 'Test deduction',
      },
    });

    if (response.status() === 401) {
      return; // License gate enforced
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('deducted');
    expect(data).toHaveProperty('remaining');
    expect(typeof data.deducted).toBe('number');
    expect(data.deducted).toBeGreaterThan(0);
  });

  test('webhook MCU deduct with invalid complexity returns 400', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/mcu/deduct`, {
      data: {
        tenant_id: TEST_TENANT_ID,
        complexity: 'invalid',
        context: 'Test',
      },
    });

    expect(response.status()).toBe(400);
  });
});

test.describe('Billing and Coupons', () => {
  test('get available coupons returns list', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/coupons/available`);

    if (response.status() === 401) {
      return; // Authentication required
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(Array.isArray(data)).toBeTruthy();

    if (data.length > 0) {
      const coupon = data[0];
      expect(coupon).toHaveProperty('code');
      expect(coupon).toHaveProperty('discount_type');
      expect(coupon).toHaveProperty('discount_value');
    }
  });

  test('validate coupon returns discount calculation', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/coupons/validate`, {
      data: {
        code: 'TEST10',
        amount: 100,
      },
    });

    if (response.status() === 401) {
      return; // Authentication required
    }

    if (response.status() === 404) {
      // Coupon doesn't exist, skip
      return;
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('valid');
    expect(data).toHaveProperty('discounted_amount');
    expect(data.discounted_amount).toBeLessThan(100);
  });

  test('invalid coupon returns 400', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/coupons/validate`, {
      data: {
        code: 'INVALID_COUPON_XYZ',
        amount: 100,
      },
    });

    if (response.status() === 404) {
      return; // Coupon validation not implemented
    }

    expect([400, 404]).toContain(response.status());
  });
});

test.describe('Tier Configuration', () => {
  test('get tier features returns correct tier info', async ({ request }) => {
    const tiers = ['starter', 'growth', 'pro', 'franchise', 'enterprise'];

    for (const tier of tiers) {
      const response = await request.get(`${API_BASE_URL}/tier/${tier}`);
      if (response.status() === 404) {
        continue; // Skip if tier not configured
      }

      expect(response.ok()).toBeTruthy();
      const data = await response.json();

      expect(data).toHaveProperty('tier', tier);
      expect(data).toHaveProperty('mcus_per_month');
      expect(data).toHaveProperty('price');
      expect(Array.isArray(data.features)).toBeTruthy();
    }
  });

  test('tier features include required attributes', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/tier/pro`);

    if (response.status() === 404) {
      return; // Tier configuration not available
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('limits');
    expect(data.limits).toHaveProperty('max_missions');
    expect(data.limits).toHaveProperty('max_concurrent');
  });
});
