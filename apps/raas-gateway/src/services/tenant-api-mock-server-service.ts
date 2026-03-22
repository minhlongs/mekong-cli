/**
 * Tenant API Mock Server Service
 * Manages mock endpoints and request logs per tenant
 */

function newId(): string {
  return crypto.randomUUID();
}

export const tenantApiMockServerService = {
  /**
   * List active mock endpoints for a tenant
   */
  async listMocks(db: any, tenantId: string): Promise<any[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM api_mock_endpoints WHERE tenant_id = ? AND is_active = 1 ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return (result.results ?? []) as any[];
    } catch (err) {
      console.error('[MockService.listMocks] error:', err);
      throw err;
    }
  },

  /**
   * Create a new mock endpoint for a tenant
   */
  async createMock(db: any, tenantId: string, data: {
    mock_path: string;
    method?: string;
    response_status?: number;
    response_body_json?: string;
    response_headers_json?: string;
    delay_ms?: number;
  }): Promise<any> {
    try {
      const id = newId();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO api_mock_endpoints
            (id, tenant_id, mock_path, method, response_status, response_body_json, response_headers_json, delay_ms, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.mock_path,
          data.method ?? 'GET',
          data.response_status ?? 200,
          data.response_body_json ?? '{}',
          data.response_headers_json ?? '{}',
          data.delay_ms ?? 0,
          now,
          now
        )
        .run();
      return { id, tenant_id: tenantId, ...data, is_active: 1, created_at: now, updated_at: now };
    } catch (err) {
      console.error('[MockService.createMock] error:', err);
      throw err;
    }
  },

  /**
   * Get request log for a specific mock endpoint
   */
  async getRequests(db: any, tenantId: string, mockId: string, limit = 50): Promise<any[]> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM api_mock_requests WHERE tenant_id = ? AND mock_id = ? ORDER BY created_at DESC LIMIT ?'
        )
        .bind(tenantId, mockId, Math.min(limit, 200))
        .all();
      return (result.results ?? []) as any[];
    } catch (err) {
      console.error('[MockService.getRequests] error:', err);
      throw err;
    }
  },

  /**
   * Admin overview: total mocks and requests across all tenants
   */
  async getAdminOverview(db: any): Promise<{ total_mocks: number; total_requests: number; active_tenants: number }> {
    try {
      const mocks = await db
        .prepare('SELECT COUNT(*) as total_mocks, COUNT(DISTINCT tenant_id) as active_tenants FROM api_mock_endpoints WHERE is_active = 1')
        .first() as any;
      const reqs = await db
        .prepare('SELECT COUNT(*) as total_requests FROM api_mock_requests')
        .first() as any;
      return {
        total_mocks: mocks?.total_mocks ?? 0,
        total_requests: reqs?.total_requests ?? 0,
        active_tenants: mocks?.active_tenants ?? 0,
      };
    } catch (err) {
      console.error('[MockService.getAdminOverview] error:', err);
      throw err;
    }
  },
};
