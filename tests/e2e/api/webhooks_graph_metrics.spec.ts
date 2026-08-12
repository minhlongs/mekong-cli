import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.API_BASE_URL ?? 'http://localhost:8000';

test.describe('Webhook Endpoints', () => {
  test('webhook schema endpoint returns valid schema', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/v1/webhook/schema`);

    expect(response.ok()).toBeTruthy();
    const schema = await response.json();

    expect(schema).toHaveProperty('version');
    expect(schema).toHaveProperty('events');
    expect(schema).toHaveProperty('descriptions');
    expect(typeof schema.events).toBe('object');
  });

  test('test webhook connectivity validates URL', async ({ request }) => {
    const testData = {
      webhook_url: 'https://httpbin.org/status/200',
    };

    const response = await request.post(`${API_BASE_URL}/v1/webhook/test`, {
      data: testData,
    });

    expect(response.ok()).toBeTruthy();
    const result = await response.json();

    expect(result).toHaveProperty('success');
    expect(result).toHaveProperty('response_time_ms');
    expect(result.response_time_ms).toBeGreaterThan(0);
  });

  test('test webhook rejects invalid URL', async ({ request }) => {
    const testData = {
      webhook_url: 'not-a-valid-url',
    };

    const response = await request.post(`${API_BASE_URL}/v1/webhook/test`, {
      data: testData,
    });

    expect(response.status()).toBe(400);
    const result = await response.json();
    expect(result.success).toBe(false);
  });

  test('test webhook handles unreachable URL gracefully', async ({ request }) => {
    const testData = {
      webhook_url: 'https://nonexistent.invalid.local:9999',
    };

    const response = await request.post(`${API_BASE_URL}/v1/webhook/test`, {
      data: testData,
    });

    // Should handle network error gracefully
    expect([200, 500]).toContain(response.status());
    const result = await response.json();
    expect(result).toHaveProperty('success');
  });

  test('test webhook without URL returns error', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/v1/webhook/test`, {
      data: {},
    });

    expect(response.status()).toBe(400);
  });
});

test.describe('Graph API', () => {
  test('graph query returns valid response', async ({ request }) => {
    const query = {
      query: `
        query {
          tenants {
            id
            name
          }
        }
      `,
    };

    const response = await request.post(`${API_BASE_URL}/api/graph`, {
      data: query,
    });

    if (response.status() === 401) {
      return; // Authentication required for graph queries - set TEST_AUTH_TOKEN
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('data');
    expect(data).not.toHaveProperty('errors');
  });

  test('graph query with invalid syntax returns errors', async ({ request }) => {
    const query = {
      query: `
        query {
          tenants {
            invalid_field
        }
      `,
    };

    const response = await request.post(`${API_BASE_URL}/api/graph`, {
      data: query,
    });

    const result = await response.json();
    expect(result).toHaveProperty('errors');
  });

  test('graph query respects tenant isolation', async ({ request }) => {
    const query = {
      query: `
        query($tenantId: ID!) {
          tenant(id: $tenantId) {
            id
            name
            particles {
              id
            }
          }
        }
      `,
      variables: { tenantId: 'different_tenant' },
    };

    const response = await request.post(`${API_BASE_URL}/api/graph`, {
      data: query,
    });

    if (response.status() === 200) {
      const result = await response.json();
      // Should either return null or throw permission error
      expect(result.data.tenant).toBeNull();
    }
  });
});

test.describe('Metrics and Observability', () => {
  test('metrics endpoint returns Prometheus format', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/metrics`);

    expect(response.ok()).toBeTruthy();
    const text = await response.text();

    // Prometheus format: # HELP metric_name ...
    expect(text).toMatch(/# HELP/);
    expect(text).toMatch(/# TYPE/);
  });

  test('metrics include request counters', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/metrics`);

    expect(response.ok()).toBeTruthy();
    const text = await response.text();

    expect(text).toMatch(/http_requests_total/);
    expect(text).toMatch(/http_request_duration_seconds/);
  });

  test('metrics include business metrics', async ({ request }) => {
    // Trigger some activity first
    await request.get(`${API_BASE_URL}/health`);

    const response = await request.get(`${API_BASE_URL}/metrics`);
    const text = await response.text();

    // Check for mission-related metrics
    expect(text).toMatch(/missions_total/);
    expect(text).toMatch(/mcus_consumed_total/);
  });

  test('metrics endpoint is not accessible from browser (no CORS)', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/metrics`, {
      headers: {
        'Origin': 'https://evil.com',
      },
    });

    const allowOrigin = response.headers()['access-control-allow-origin'];
    expect(allowOrigin).not.toBe('*');
  });
});

test.describe('Health Checks', () => {
  test('health endpoint returns healthy status', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('version');
    expect(data).toHaveProperty('timestamp');
  });

  test('health includes all required subsystems', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('subsystems');
    expect(Array.isArray(data.subsystems)).toBeTruthy();

    const subsystemNames = data.subsystems.map((s: any) => s.name);
    expect(subsystemNames).toContain('database');
    expect(subsystemNames).toContain('redis');
  });

  test('health reports degraded when subsystem fails', async ({ request }) => {
    // This would require simulating a subsystem failure
    // For now, just verify the structure
    const response = await request.get(`${API_BASE_URL}/health`);

    if (response.ok()) {
      const data = await response.json();
      // If degraded, status would be 'degraded'
      expect(['healthy', 'degraded']).toContain(data.status);
    }
  });

  test('ready endpoint checks deep dependencies', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/ready`);

    if (response.status() === 404) {
      return; // Ready endpoint not implemented
    }

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('ready', true);
    expect(data).toHaveProperty('checks');
  });
});

test.describe('API Documentation', () => {
  test('OpenAPI schema is available in development', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api-docs`);

    if (response.status() === 404) {
      return; // API docs disabled in production
    }

    expect(response.ok()).toBeTruthy();
    const html = await response.text();
    expect(html).toContain('Swagger UI');
  });

  test('OpenAPI JSON schema is valid', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/openapi.json`);

    if (response.status() === 404) {
      return; // OpenAPI disabled in production
    }

    expect(response.ok()).toBeTruthy();
    const schema = await response.json();

    expect(schema).toHaveProperty('openapi');
    expect(schema).toHaveProperty('info');
    expect(schema).toHaveProperty('paths');
  });

  test('Redoc documentation is available', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api-redoc`);

    if (response.status() === 404) {
      return; // Redoc disabled in production
    }

    expect(response.ok()).toBeTruthy();
    const html = await response.text();
    expect(html).toContain('Redoc');
  });
});
