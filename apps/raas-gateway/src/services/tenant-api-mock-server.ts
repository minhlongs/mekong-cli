/**
 * Tenant API Mock Server Service
 * Manages configurable mock endpoints and request logs per tenant
 */

// Generate a simple unique ID (crypto.randomUUID not available in all CF workers builds)
function newId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
}

/** List all mock endpoints for a tenant */
async function listMocks(db: any, tenantId: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, mock_name, method, path_pattern, response_status,
                response_body, response_headers, delay_ms, enabled, created_at
         FROM api_mock_endpoints
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[MockService.listMocks] error:', err);
    return { success: false, error: 'Failed to list mock endpoints' };
  }
}

/** Create a new mock endpoint for a tenant */
async function createMock(
  db: any,
  tenantId: string,
  body: {
    mock_name: string;
    method?: string;
    path_pattern: string;
    response_status?: number;
    response_body?: string;
    response_headers?: string;
    delay_ms?: number;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const { mock_name, path_pattern } = body;

    if (!mock_name || !path_pattern) {
      return { success: false, error: 'mock_name and path_pattern are required' };
    }

    const id = newId();
    const method = (body.method ?? 'GET').toUpperCase();
    const response_status = body.response_status ?? 200;
    const response_body = body.response_body ?? null;
    const response_headers = body.response_headers ?? null;
    const delay_ms = body.delay_ms ?? 0;
    const created_at = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO api_mock_endpoints
           (id, tenant_id, mock_name, method, path_pattern,
            response_status, response_body, response_headers, delay_ms, enabled, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)`
      )
      .bind(id, tenantId, mock_name, method, path_pattern,
            response_status, response_body, response_headers, delay_ms, created_at)
      .run();

    return {
      success: true,
      data: {
        id, tenant_id: tenantId, mock_name, method, path_pattern,
        response_status, response_body, response_headers, delay_ms,
        enabled: 1, created_at,
      },
    };
  } catch (err) {
    console.error('[MockService.createMock] error:', err);
    return { success: false, error: 'Failed to create mock endpoint' };
  }
}

/** List recent mock requests logged for a tenant */
async function getRequests(
  db: any,
  tenantId: string,
  limit = 50
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 200);
    const rows = await db
      .prepare(
        `SELECT id, mock_id, request_method, request_path, matched, created_at
         FROM api_mock_requests
         WHERE tenant_id = ?
         ORDER BY created_at DESC
         LIMIT ?`
      )
      .bind(tenantId, safeLimit)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[MockService.getRequests] error:', err);
    return { success: false, error: 'Failed to fetch mock requests' };
  }
}

/** Admin overview: total mocks and requests across all tenants */
async function getAdminOverview(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [mockStats, requestStats, topTenants] = await Promise.all([
      db
        .prepare(
          `SELECT COUNT(*) as total_mocks,
                  SUM(enabled) as enabled_mocks,
                  COUNT(DISTINCT tenant_id) as tenants_with_mocks
           FROM api_mock_endpoints`
        )
        .first(),
      db
        .prepare(
          `SELECT COUNT(*) as total_requests,
                  SUM(matched) as matched_requests,
                  COUNT(DISTINCT tenant_id) as active_tenants
           FROM api_mock_requests`
        )
        .first(),
      db
        .prepare(
          `SELECT tenant_id, COUNT(*) as mock_count
           FROM api_mock_endpoints
           GROUP BY tenant_id
           ORDER BY mock_count DESC
           LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        mocks: mockStats,
        requests: requestStats,
        top_tenants: topTenants.results ?? [],
      },
    };
  } catch (err) {
    console.error('[MockService.getAdminOverview] error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

export const tenantApiMockServerService = {
  listMocks,
  createMock,
  getRequests,
  getAdminOverview,
};
