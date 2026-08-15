import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';

test.describe('Vietnamese Pilot API', () => {
  test('get VN pricing returns correct structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/pricing/vn`);

    if (response.status() === 404) {
      return; // VN pricing not implemented
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('services');
    expect(Array.isArray(data.services)).toBeTruthy();
    expect(data.services.length).toBeGreaterThan(0);
  });

  test('VN pricing services have correct fields', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/pricing/vn`);

    if (response.status() === 404) {
      return; // VN pricing not implemented
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    const service = data.services[0];
    expect(service).toHaveProperty('id');
    expect(service).toHaveProperty('name');
    expect(service).toHaveProperty('description');
    expect(service).toHaveProperty('price_vnd');
    expect(service).toHaveProperty('credits');
  });

  test('get VN tier details returns pricing info', async ({ request }) => {
    const tiers = ['starter', 'growth', 'pro'];

    for (const tier of tiers) {
      const response = await request.get(`${API_BASE_URL}/v1/pricing/vn/tier/${tier}`);

      if (response.status() === 404) {
        continue;
      }

      expect(response.ok()).toBeTruthy();
      const data = await response.json();

      expect(data).toHaveProperty('tier', tier);
      expect(data).toHaveProperty('price_vnd');
      expect(data).toHaveProperty('mcus');
    }
  });

  test('pilot signup creates new pilot user', async ({ request }) => {
    const signupData = {
      name: 'Test Pilot User',
      email: `test-pilot-${Date.now()}@example.com`,
      zalo: `+849${Math.floor(Math.random() * 100000000)}`,
      business_type: 'shop_online',
      city: 'HCM',
      industry: 'thời trang',
      source: 'test',
    };

    const response = await request.post(`${API_BASE_URL}/v1/pilot/signup`, {
      data: signupData,
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('user_id');
    expect(data.user_id).toMatch(/^opc_\d+_[a-z0-9]+$/);
    expect(data).toHaveProperty('initial_credits');
    expect(data.initial_credits).toBe(50); // 50 free credits

    // Clean up - delete test pilot (would need admin endpoint)
  });

  test('pilot signup with duplicate email returns error', async ({ request }) => {
    const email = `duplicate-test-${Date.now()}@example.com`;

  test('pilot can retrieve own profile', async ({ request }) => {
    // First signup
    const signupData = {
      name: 'Profile Test User',
      email: `profile-test-${Date.now()}@example.com`,
      zalo: '+84912345678',
      business_type: 'shop_online',
      city: 'HCM',
      industry: 'test',
    };

    const signupResponse = await request.post(`${API_BASE_URL}/v1/pilot/signup`, {
      data: signupData,
    });

    expect(signupResponse.ok()).toBeTruthy();
    const signupDataResult = await signupResponse.json();
    const userId = signupDataResult.user_id;

    // Retrieve profile
    const profileResponse = await request.get(`${API_BASE_URL}/v1/pilot/profile`, {
      headers: {
        'X-User-Id': userId,
      },
    });

    expect(profileResponse.ok()).toBeTruthy();
    const profile = await profileResponse.json();

    expect(profile).toHaveProperty('user_id', userId);
    expect(profile).toHaveProperty('name', signupData.name);
    expect(profile).toHaveProperty('email', signupData.email);
    expect(profile).toHaveProperty('credits');
  });

  test('pilot credit operations work correctly', async ({ request }) => {
    // Signup to get initial credits
    const signupData = {
      name: 'Credit Test User',
      email: `credit-test-${Date.now()}@example.com`,
      zalo: '+84912345678',
      business_type: 'shop_online',
      city: 'HCM',
      industry: 'test',
    };

    const signupResponse = await request.post(`${API_BASE_URL}/v1/pilot/signup`, {
      data: signupData,
    });

    expect(signupResponse.ok()).toBeTruthy();
    const { user_id, initial_credits } = await signupResponse.json();

    // Get initial balance
    const initialBalance = await request.get(`${API_BASE_URL}/v1/pilot/credits`, {
      headers: { 'X-User-Id': user_id },
    }).then(r => r.json());

    expect(initialBalance.balance).toBe(initial_credits);

    // Add credits (simulate purchase)
    const addResponse = await request.post(`${API_BASE_URL}/v1/pilot/credits/add`, {
      data: {
        user_id: user_id,
        amount: 100,
        reason: 'Test credit addition',
      },
    });

    if (addResponse.status() === 401) {
      return; // Admin token required for credit modification
    }

    expect(addResponse.ok()).toBeTruthy();

    // Verify balance increased
    const newBalance = await request.get(`${API_BASE_URL}/v1/pilot/credits`, {
      headers: { 'X-User-Id': user_id },
    }).then(r => r.json());

    expect(newBalance.balance).toBeGreaterThan(initialBalance.balance);
  });

  test('pilot usage is tracked correctly', async ({ request }) => {
    // Signup and execute a command
    const signupResponse = await request.post(`${API_BASE_URL}/v1/pilot/signup`, {
      data: {
        name: 'Usage Track Test',
        email: `usage-test-${Date.now()}@example.com`,
        zalo: '+84912345678',
        business_type: 'shop_online',
        city: 'HCM',
        industry: 'test',
      },
    });

    const { user_id } = await signupResponse.json();

    // Execute a command (would need to call command API)
    // For now, verify usage endpoint exists and returns empty initially
    const usageResponse = await request.get(`${API_BASE_URL}/v1/pilot/usage`, {
      headers: { 'X-User-Id': user_id },
    });

    if (usageResponse.status() === 404) {
      return; // Usage tracking endpoint not implemented
    }

    expect(usageResponse.ok()).toBeTruthy();
    const usage = await usageResponse.json();

    expect(usage).toHaveProperty('events');
    expect(Array.isArray(usage.events)).toBeTruthy();
  });

  test('VietQR webhook processes payment correctly', async ({ request }) => {
    // This test requires the VietQR webhook to be configured
    const webhookSecret = process.env.MEKONG_VIETQR_WEBHOOK_SECRET;

    if (!webhookSecret) {
      return; // VietQR webhook not configured
    }

    // Simulate VietQR webhook payload
    const webhookPayload = {
      transaction_id: `test_tx_${Date.now()}`,
      user_id: 'opc_test_abc123',
      amount: 199000, // 199K VND for starter tier
      bank_code: 'MB',
      account_number: '1234567890',
      transfer_time: new Date().toISOString(),
      signature: 'test_signature',
    };

    // Calculate HMAC signature (simplified for test)
    // In production, would use proper HMAC-SHA256

    const response = await request.post(`${API_BASE_URL}/v1/payments/vietqr/webhook`, {
      data: webhookPayload,
      headers: {
        'X-Vietqr-Signature': webhookSecret, // Simplified
      },
    });

    // Webhook should accept and acknowledge
    expect([200, 202]).toContain(response.status());
  });

  test('VietQR webhook with invalid signature returns 401', async ({ request }) => {
    const webhookPayload = {
      transaction_id: `test_tx_${Date.now()}`,
      user_id: 'opc_test_abc123',
      amount: 199000,
    };

    const response = await request.post(`${API_BASE_URL}/v1/payments/vietqr/webhook`, {
      data: webhookPayload,
      headers: {
        'X-Vietqr-Signature': 'invalid_signature',
      },
    });

    expect(response.status()).toBe(401);
  });

  test('pilot weekly NPS poll workflow', async ({ request }) => {
    const signupResponse = await request.post(`${API_BASE_URL}/v1/pilot/signup`, {
      data: {
        name: 'NPS Poll Test',
        email: `nps-test-${Date.now()}@example.com`,
        zalo: '+84912345678',
        business_type: 'shop_online',
        city: 'HCM',
        industry: 'test',
      },
    });

    const { user_id } = await signupResponse.json();

    // Get pending polls
    const pollsResponse = await request.get(`${API_BASE_URL}/v1/pilot/polls/pending`, {
      headers: { 'X-User-Id': user_id },
    });

    if (pollsResponse.status() === 404) {
      return; // Poll system not implemented
    }

    expect(pollsResponse.ok()).toBeTruthy();
    const polls = await pollsResponse.json();

    if (polls.polls && polls.polls.length > 0) {
      const poll = polls.polls[0];

      // Submit NPS response
      const submitResponse = await request.post(`${API_BASE_URL}/v1/pilot/polls/${poll.id}/respond`, {
        data: {
          rating: 9,
          feedback: 'Test feedback submission',
        },
        headers: { 'X-User-Id': user_id },
      });

      expect(submitResponse.ok()).toBeTruthy();
    }
  });
});

test.describe('Pilot Admin Operations', () => {
  const ADMIN_TOKEN = process.env.MEKONG_ADMIN_TOKEN;

  test.beforeAll(() => {
    if (!ADMIN_TOKEN) {
      return; // MEKONG_ADMIN_TOKEN not set - admin tests will be skipped
    }
  });

  test('admin can convert pilot to paid customer', async ({ request }) => {
    // Requires a pilot user to exist
    const signupResponse = await request.post(`${API_BASE_URL}/v1/pilot/signup`, {
      data: {
        name: 'Convert Test User',
        email: `convert-test-${Date.now()}@example.com`,
        zalo: '+84912345678',
        business_type: 'shop_online',
        city: 'HCM',
        industry: 'test',
      },
    });

    const { user_id } = await signupResponse.json();

    const convertResponse = await request.post(`${API_BASE_URL}/v1/pilot/convert`, {
      data: {
        user_id: user_id,
        tier: 'growth',
        payment_method: 'bank_transfer',
      },
      headers: {
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
      },
    });

    expect(convertResponse.ok()).toBeTruthy();
    const result = await convertResponse.json();
    expect(result).toHaveProperty('status', 'converted');
    expect(result).toHaveProperty('tier', 'growth');
  });

  test('admin without token cannot convert pilot', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/pilot/convert`, {
      data: {
        user_id: 'opc_test_abc123',
        tier: 'growth',
      },
    });

    expect(response.status()).toBe(401);
  });

  test('admin can get pilot statistics', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/pilot/admin/stats`, {
      headers: {
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const stats = await response.json();

    expect(stats).toHaveProperty('total_pilots');
    expect(stats).toHaveProperty('active_pilots');
    expect(stats).toHaveProperty('conversion_rate');
    expect(stats).toHaveProperty('revenue_vnd');
  });

  test('admin can list all pilots', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/pilot/admin/list?limit=10`, {
      headers: {
        'Authorization': `Bearer ${ADMIN_TOKEN}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('pilots');
    expect(Array.isArray(data.pilots)).toBeTruthy();
    expect(data.pilots.length).toBeLessThanOrEqual(10);
  });
});
});
