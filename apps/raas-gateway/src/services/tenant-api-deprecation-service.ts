/**
 * Tenant API Deprecation Service — list/create notices, query acknowledgements, admin overview
 * DB calls use .all() + cast (D1 pattern, no generics on prepare). Caller passes db: any.
 */

interface DeprecationNotice {
  id: string; tenant_id: string | null; endpoint: string;
  deprecation_date: string | null; sunset_date: string | null;
  replacement_endpoint: string | null; message: string | null;
  status: string; created_at: string;
}

interface DeprecationAcknowledgement {
  id: string; tenant_id: string | null; notice_id: string | null; acknowledged_at: string;
}

interface AdminOverviewRow {
  tenant_id: string | null; total_notices: number; active_notices: number; total_acknowledgements: number;
}

const uuid = () => crypto.randomUUID();
const now = () => new Date().toISOString();

export const tenantApiDeprecationService = {

  /** List notices visible to a tenant (own + global where tenant_id IS NULL) */
  async listNotices(db: any, tenantId: string): Promise<DeprecationNotice[]> {
    try {
      const r = await db
        .prepare('SELECT * FROM api_deprecation_notices WHERE tenant_id = ? OR tenant_id IS NULL ORDER BY created_at DESC')
        .bind(tenantId).all();
      return (r.results ?? []) as DeprecationNotice[];
    } catch (err) { throw new Error(`listNotices: ${(err as Error).message}`); }
  },

  /** Create a deprecation notice scoped to a tenant */
  async createNotice(db: any, tenantId: string, data: {
    endpoint: string; deprecation_date?: string; sunset_date?: string;
    replacement_endpoint?: string; message?: string;
  }): Promise<DeprecationNotice> {
    const id = uuid(); const ts = now();
    try {
      await db
        .prepare(`INSERT INTO api_deprecation_notices
          (id, tenant_id, endpoint, deprecation_date, sunset_date, replacement_endpoint, message, status, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)`)
        .bind(id, tenantId, data.endpoint,
          data.deprecation_date ?? null, data.sunset_date ?? null,
          data.replacement_endpoint ?? null, data.message ?? null, ts)
        .run();
      return {
        id, tenant_id: tenantId, endpoint: data.endpoint,
        deprecation_date: data.deprecation_date ?? null, sunset_date: data.sunset_date ?? null,
        replacement_endpoint: data.replacement_endpoint ?? null, message: data.message ?? null,
        status: 'active', created_at: ts,
      };
    } catch (err) { throw new Error(`createNotice: ${(err as Error).message}`); }
  },

  /** List acknowledgements for a tenant, optionally filtered by notice_id */
  async getAcknowledgements(db: any, tenantId: string, noticeId?: string): Promise<DeprecationAcknowledgement[]> {
    try {
      const sql = noticeId
        ? 'SELECT * FROM api_deprecation_acknowledgements WHERE tenant_id = ? AND notice_id = ? ORDER BY acknowledged_at DESC'
        : 'SELECT * FROM api_deprecation_acknowledgements WHERE tenant_id = ? ORDER BY acknowledged_at DESC';
      const stmt = noticeId ? db.prepare(sql).bind(tenantId, noticeId) : db.prepare(sql).bind(tenantId);
      const r = await stmt.all();
      return (r.results ?? []) as DeprecationAcknowledgement[];
    } catch (err) { throw new Error(`getAcknowledgements: ${(err as Error).message}`); }
  },

  /** Admin overview — aggregate deprecation stats per tenant */
  async getAdminOverview(db: any): Promise<AdminOverviewRow[]> {
    try {
      const r = await db.prepare(
        `SELECT n.tenant_id,
           COUNT(DISTINCT n.id)                                        AS total_notices,
           COUNT(DISTINCT CASE WHEN n.status = 'active' THEN n.id END) AS active_notices,
           COUNT(DISTINCT a.id)                                        AS total_acknowledgements
         FROM api_deprecation_notices n
         LEFT JOIN api_deprecation_acknowledgements a ON a.notice_id = n.id
         GROUP BY n.tenant_id ORDER BY total_notices DESC`
      ).all();
      return (r.results ?? []) as AdminOverviewRow[];
    } catch (err) { throw new Error(`getAdminOverview: ${(err as Error).message}`); }
  },
};
