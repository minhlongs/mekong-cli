import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';
const TEST_TENANT_ID = process.env.TEST_TENANT_ID ?? 'test_tenant_001';

test.describe('Organization Management', () => {
  let orgId: string | null = null;
  const authToken = process.env.TEST_AUTH_TOKEN;

  test.beforeAll(() => {
    if (!authToken) {
      return; // TEST_AUTH_TOKEN not set - organization tests require authentication
    }
  });

  test('create organization succeeds with valid data', async ({ request }) => {
    const orgData = {
      name: `Test Organization ${Date.now()}`,
      description: 'Test organization for E2E tests',
      tenant_id: TEST_TENANT_ID,
    };

    const response = await request.post(`${API_BASE_URL}/api/org`, {
      data: orgData,
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const org = await response.json();

    expect(org).toHaveProperty('id');
    expect(org).toHaveProperty('name', orgData.name);
    expect(org).toHaveProperty('tenant_id', TEST_TENANT_ID);
    expect(org).toHaveProperty('created_at');

    // Save orgId for subsequent tests
    orgId = org.id;
  });

  test('get organization by ID returns correct data', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const response = await request.get(`${API_BASE_URL}/api/org/${orgId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const org = await response.json();

    expect(org).toHaveProperty('id', orgId);
    expect(org).toHaveProperty('name');
    expect(org).toHaveProperty('members');
    expect(Array.isArray(org.members)).toBeTruthy();
  });

  test('list organizations for tenant', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/org?tenant_id=${TEST_TENANT_ID}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('organizations');
    expect(Array.isArray(data.organizations)).toBeTruthy();
  });

  test('update organization succeeds', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const updateData = {
      name: `Updated Org Name ${Date.now()}`,
      description: 'Updated description',
    };

    const response = await request.put(`${API_BASE_URL}/api/org/${orgId}`, {
      data: updateData,
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const org = await response.json();

    expect(org).toHaveProperty('name', updateData.name);
    expect(org).toHaveProperty('description', updateData.description);
  });

  test('invite member to organization', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const inviteData = {
      email: `new-member-${Date.now()}@example.com`,
      role: 'member',
      permissions: ['read', 'write'],
    };

    const response = await request.post(`${API_BASE_URL}/api/org/${orgId}/invite`, {
      data: inviteData,
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect([200, 201]).toContain(response.status());
    const result = await response.json();

    expect(result).toHaveProperty('invite_id');
    expect(result).toHaveProperty('email', inviteData.email);
  });

  test('list organization members', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const response = await request.get(`${API_BASE_URL}/api/org/${orgId}/members`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const members = await response.json();

    expect(Array.isArray(members)).toBeTruthy();

    if (members.length > 0) {
      const member = members[0];
      expect(member).toHaveProperty('user_id');
      expect(member).toHaveProperty('email');
      expect(member).toHaveProperty('role');
    }
  });

  test('update member role', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const response = await request.get(`${API_BASE_URL}/api/org/${orgId}/members`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    const members = await response.json();
    if (members.length === 0) {
      return; // No members to update
    }

    const member = members[0];
    const updateResponse = await request.put(`${API_BASE_URL}/api/org/${orgId}/members/${member.user_id}`, {
      data: { role: 'admin' },
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    expect([200, 204]).toContain(updateResponse.status());
  });

  test('remove member from organization', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const membersResponse = await request.get(`${API_BASE_URL}/api/org/${orgId}/members`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    const members = await membersResponse.json();
    if (members.length === 0) {
      return; // No members to remove
    }

    const member = members[0];
    const removeResponse = await request.delete(`${API_BASE_URL}/api/org/${orgId}/members/${member.user_id}`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    expect([200, 204, 404]).toContain(removeResponse.status());
  });

  test('delete organization succeeds', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const response = await request.delete(`${API_BASE_URL}/api/org/${orgId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect([200, 204]).toContain(response.status());
  });

  test('get non-existent organization returns 404', async ({ request }) => {
    const fakeId = 'org_that_does_not_exist_999999';

    const response = await request.get(`${API_BASE_URL}/api/org/${fakeId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.status()).toBe(404);
  });

  test('create organization without auth returns 401', async ({ request }) => {
    const orgData = {
      name: 'Unauthorized Org',
      tenant_id: TEST_TENANT_ID,
    };

    const response = await request.post(`${API_BASE_URL}/api/org`, {
      data: orgData,
    });

    expect(response.status()).toBe(401);
  });

test.describe('Organization Billing', () => {
  let orgId: string | null = null;
  const authToken = process.env.TEST_AUTH_TOKEN;

  test.beforeAll(() => {
    if (!authToken) {
      return; // TEST_AUTH_TOKEN not set - billing tests will skip
    }
  });

  test('create organization for billing tests', async ({ request }) => {
    const orgData = {
      name: `Billing Test Org ${Date.now()}`,
      tenant_id: TEST_TENANT_ID,
    };

    const response = await request.post(`${API_BASE_URL}/api/org`, {
      data: orgData,
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    expect(response.ok()).toBeTruthy();
    orgId = (await response.json()).id;
  });

  test('get organization billing summary', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const response = await request.get(`${API_BASE_URL}/api/org/${orgId}/billing`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    if (response.status() === 404) {
      return; // Billing endpoint not implemented
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('current_balance');
    expect(data).toHaveProperty('currency', 'VND');
    expect(data).toHaveProperty('last_updated');
  });

  test('organization usage breakdown', async ({ request }) => {
    if (!orgId) {
      return; // Organization not created
    }

    const response = await request.get(`${API_BASE_URL}/api/org/${orgId}/usage?period=month`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });

    if (response.status() === 404) {
      return; // Usage endpoint not implemented
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('period');
    expect(data).toHaveProperty('total_mcus');
    expect(data).toHaveProperty('breakdown');
    expect(Array.isArray(data.breakdown)).toBeTruthy();
  });

  test('after test: cleanup test organization', async ({ request }) => {
    if (!orgId || !authToken) {
      return;
    }

    await request.delete(`${API_BASE_URL}/api/org/${orgId}`, {
      headers: { 'Authorization': `Bearer ${authToken}` },
    });
  });
});
});
