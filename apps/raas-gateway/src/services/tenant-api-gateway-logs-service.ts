/**
 * Tenant API Gateway Logs Service — list, record, summarize gateway logs per tenant
 */

export interface GatewayLog {
  id: string;
  tenant_id: string;
  method: string;
  path: string;
  status_code: number;
  response_time_ms: number | null;
  request_size: number;
  response_size: number;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface GatewayLogSummary {
  id: string;
  tenant_id: string;
  period: string;
  total_requests: number;
  avg_response_time_ms: number;
  error_count: number;
  top_paths_json: string;
  created_at: string;
}

interface RecordLogInput {
  method: string;
  path: string;
  status_code: number;
  response_time_ms?: number;
  request_size?: number;
  response_size?: number;
  ip_address?: string;
  user_agent?: string;
}

interface ListLogsOptions {
  limit?: number;
  offset?: number;
  method?: string;
  status_code?: number;
}

// --- Log Operations ---

export const tenantApiGatewayLogsService = {
  /**
   * List gateway logs for a tenant with optional filters
   */
  async listLogs(
    db: any,
    tenantId: string,
    options: ListLogsOptions = {}
  ): Promise<GatewayLog[]> {
    try {
      let query = 'SELECT * FROM api_gateway_logs WHERE tenant_id = ?';
      const bindings: unknown[] = [tenantId];

      if (options.method) {
        query += ' AND method = ?';
        bindings.push(options.method.toUpperCase());
      }
      if (options.status_code !== undefined) {
        query += ' AND status_code = ?';
        bindings.push(options.status_code);
      }

      query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
      bindings.push(options.limit ?? 50, options.offset ?? 0);

      const result = await db.prepare(query).bind(...bindings).all();
      return (result.results ?? []) as GatewayLog[];
    } catch (err) {
      throw new Error(`Failed to list gateway logs: ${String(err)}`);
    }
  },

  /**
   * Record a single gateway log entry
   */
  async recordLog(
    db: any,
    tenantId: string,
    input: RecordLogInput
  ): Promise<GatewayLog> {
    try {
      const id = crypto.randomUUID();
      await db.prepare(
        `INSERT INTO api_gateway_logs
          (id, tenant_id, method, path, status_code, response_time_ms,
           request_size, response_size, ip_address, user_agent)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        id,
        tenantId,
        input.method.toUpperCase(),
        input.path,
        input.status_code,
        input.response_time_ms ?? null,
        input.request_size ?? 0,
        input.response_size ?? 0,
        input.ip_address ?? null,
        input.user_agent ?? null
      ).run();

      const row = await db.prepare(
        'SELECT * FROM api_gateway_logs WHERE id = ?'
      ).bind(id).first();

      return row as GatewayLog;
    } catch (err) {
      throw new Error(`Failed to record gateway log: ${String(err)}`);
    }
  },

  /**
   * Get log summaries for a tenant
   */
  async getSummaries(
    db: any,
    tenantId: string,
    limit = 10
  ): Promise<GatewayLogSummary[]> {
    try {
      const result = await db.prepare(
        `SELECT * FROM api_gateway_log_summaries
         WHERE tenant_id = ?
         ORDER BY created_at DESC LIMIT ?`
      ).bind(tenantId, limit).all();

      return (result.results ?? []) as GatewayLogSummary[];
    } catch (err) {
      throw new Error(`Failed to get log summaries: ${String(err)}`);
    }
  },

  /**
   * Admin overview — aggregate stats across all tenants
   */
  async getAdminOverview(db: any): Promise<Record<string, unknown>> {
    try {
      const [totals, byMethod, byStatus, recent] = await Promise.all([
        db.prepare(
          `SELECT COUNT(*) as total_requests,
                  AVG(response_time_ms) as avg_response_time_ms,
                  SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
           FROM api_gateway_logs`
        ).first(),
        db.prepare(
          `SELECT method, COUNT(*) as count
           FROM api_gateway_logs GROUP BY method ORDER BY count DESC`
        ).all(),
        db.prepare(
          `SELECT status_code, COUNT(*) as count
           FROM api_gateway_logs GROUP BY status_code ORDER BY count DESC LIMIT 10`
        ).all(),
        db.prepare(
          `SELECT tenant_id, COUNT(*) as request_count
           FROM api_gateway_logs
           GROUP BY tenant_id ORDER BY request_count DESC LIMIT 10`
        ).all(),
      ]);

      return {
        totals: totals ?? {},
        by_method: byMethod.results ?? [],
        by_status_code: byStatus.results ?? [],
        top_tenants: recent.results ?? [],
      };
    } catch (err) {
      throw new Error(`Failed to get admin overview: ${String(err)}`);
    }
  },
};
