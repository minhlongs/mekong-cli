/**
 * Platform Audit Trail Service — Wave 50
 * Centralized audit logging with retention policies and export management
 */

export const platformAuditTrailService = {
  /** Insert a new audit log entry */
  async logEvent(db: D1Database, data: {
    tenantId?: string; actorId?: string; actorType?: string;
    action: string; resourceType: string; resourceId?: string;
    detailsJson?: Record<string, unknown>; ipAddress?: string;
    userAgent?: string; severity?: string;
  }): Promise<{ id: string }> {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO audit_logs
        (id, tenant_id, actor_id, actor_type, action, resource_type, resource_id, details_json, ip_address, user_agent, severity)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id, data.tenantId ?? null, data.actorId ?? null,
      data.actorType ?? 'user', data.action, data.resourceType,
      data.resourceId ?? null, JSON.stringify(data.detailsJson ?? {}),
      data.ipAddress ?? null, data.userAgent ?? null, data.severity ?? 'info',
    ).run();
    return { id };
  },

  /** Paginated search with optional filters */
  async searchLogs(db: D1Database, tenantId: string, filters?: {
    action?: string; resourceType?: string; severity?: string;
    dateFrom?: string; dateTo?: string; limit?: number; offset?: number;
  }) {
    const conditions = ['tenant_id = ?'];
    const params: unknown[] = [tenantId];
    if (filters?.action) { conditions.push('action = ?'); params.push(filters.action); }
    if (filters?.resourceType) { conditions.push('resource_type = ?'); params.push(filters.resourceType); }
    if (filters?.severity) { conditions.push('severity = ?'); params.push(filters.severity); }
    if (filters?.dateFrom) { conditions.push('created_at >= ?'); params.push(filters.dateFrom); }
    if (filters?.dateTo) { conditions.push('created_at <= ?'); params.push(filters.dateTo); }
    const limit = filters?.limit ?? 50;
    const offset = filters?.offset ?? 0;
    params.push(limit, offset);
    const { results } = await db.prepare(
      `SELECT * FROM audit_logs WHERE ${conditions.join(' AND ')} ORDER BY created_at DESC LIMIT ? OFFSET ?`
    ).bind(...params).all();
    return { logs: results, limit, offset };
  },

  /** Get single log entry by id scoped to tenant */
  async getLogDetail(db: D1Database, tenantId: string, id: string) {
    const row = await db.prepare(
      'SELECT * FROM audit_logs WHERE id = ? AND tenant_id = ?'
    ).bind(id, tenantId).first();
    return row ?? null;
  },

  /** List all retention policies */
  async listRetentionPolicies(db: D1Database) {
    const { results } = await db.prepare(
      'SELECT * FROM audit_retention_policies ORDER BY resource_type'
    ).all();
    return results;
  },

  /** Upsert a retention policy for a resource type */
  async updateRetentionPolicy(db: D1Database, resourceType: string, data: {
    retentionDays?: number; autoArchive?: boolean;
  }) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db.prepare(
      `INSERT INTO audit_retention_policies (id, resource_type, retention_days, auto_archive, updated_at)
       VALUES (?, ?, ?, ?, ?)
       ON CONFLICT(resource_type) DO UPDATE SET
         retention_days = excluded.retention_days,
         auto_archive = excluded.auto_archive,
         updated_at = excluded.updated_at`
    ).bind(
      id, resourceType, data.retentionDays ?? 90,
      data.autoArchive ? 1 : 0, now,
    ).run();
    return { resourceType, ...data };
  },

  /** Create an export request */
  async requestExport(db: D1Database, tenantId: string, filters: Record<string, unknown>) {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO audit_exports (id, tenant_id, filters_json, status)
       VALUES (?, ?, ?, 'pending')`
    ).bind(id, tenantId, JSON.stringify(filters)).run();
    return { id, status: 'pending' };
  },

  /** List exports for a tenant */
  async listExports(db: D1Database, tenantId: string) {
    const { results } = await db.prepare(
      'SELECT * FROM audit_exports WHERE tenant_id = ? ORDER BY requested_at DESC LIMIT 50'
    ).bind(tenantId).all();
    return results;
  },

  /** Per-tenant stats: action counts + severity distribution */
  async getStats(db: D1Database, tenantId: string) {
    const [actionCounts, severityDist] = await Promise.all([
      db.prepare(
        `SELECT action, COUNT(*) as count FROM audit_logs WHERE tenant_id = ?
         GROUP BY action ORDER BY count DESC LIMIT 20`
      ).bind(tenantId).all(),
      db.prepare(
        `SELECT severity, COUNT(*) as count FROM audit_logs WHERE tenant_id = ?
         GROUP BY severity ORDER BY count DESC`
      ).bind(tenantId).all(),
    ]);
    return { tenantId, actionCounts: actionCounts.results, severityDist: severityDist.results };
  },

  /** Admin overview: global stats + storage usage estimate */
  async getAdminOverview(db: D1Database) {
    const [total, bySeverity, byTenant, recentExports] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total FROM audit_logs').first<{ total: number }>(),
      db.prepare(
        'SELECT severity, COUNT(*) as count FROM audit_logs GROUP BY severity'
      ).all(),
      db.prepare(
        'SELECT tenant_id, COUNT(*) as count FROM audit_logs GROUP BY tenant_id ORDER BY count DESC LIMIT 10'
      ).all(),
      db.prepare(
        'SELECT status, COUNT(*) as count FROM audit_exports GROUP BY status'
      ).all(),
    ]);
    return {
      totalLogs: total?.total ?? 0,
      bySeverity: bySeverity.results,
      topTenants: byTenant.results,
      exportsByStatus: recentExports.results,
    };
  },
};
