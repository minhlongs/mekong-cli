/**
 * Admin Platform Audit Trail Service
 * CRUD for platform_audit_entries and platform_audit_policies; dashboard aggregation
 */

// List audit entries; optional filters: actor, action, resource_type, limit
async function listEntries(
  db: any,
  filters?: { actor?: string; action?: string; resource_type?: string; limit?: number }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const limit = Math.min(filters?.limit ?? 50, 500);
    const conditions: string[] = [];
    const params: any[] = [];

    if (filters?.actor) {
      conditions.push('actor = ?');
      params.push(filters.actor);
    }
    if (filters?.action) {
      conditions.push('action = ?');
      params.push(filters.action);
    }
    if (filters?.resource_type) {
      conditions.push('resource_type = ?');
      params.push(filters.resource_type);
    }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const query = `SELECT * FROM platform_audit_entries ${where} ORDER BY created_at DESC LIMIT ?`;
    params.push(limit);

    const result = await db.prepare(query).bind(...params).all();
    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create a new audit entry
async function createEntry(
  db: any,
  body: {
    actor: string;
    action: string;
    resource_type: string;
    resource_id?: string;
    details?: string;
    ip_address?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const created_at = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO platform_audit_entries
           (id, actor, action, resource_type, resource_id, details, ip_address, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        body.actor,
        body.action,
        body.resource_type,
        body.resource_id ?? null,
        body.details ?? null,
        body.ip_address ?? null,
        created_at
      )
      .run();

    const created = await db
      .prepare('SELECT * FROM platform_audit_entries WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// List all audit policies
async function getPolicies(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM platform_audit_policies ORDER BY created_at DESC')
      .all();
    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Dashboard: entry counts by action, by resource_type, recent 7-day activity, policy summary
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [byAction, byResource, recent7d, totalEntries, policies] = await Promise.all([
      db
        .prepare(
          `SELECT action, COUNT(*) as count
           FROM platform_audit_entries
           GROUP BY action
           ORDER BY count DESC
           LIMIT 10`
        )
        .all(),
      db
        .prepare(
          `SELECT resource_type, COUNT(*) as count
           FROM platform_audit_entries
           GROUP BY resource_type
           ORDER BY count DESC
           LIMIT 10`
        )
        .all(),
      db
        .prepare(
          `SELECT COUNT(*) as count
           FROM platform_audit_entries
           WHERE created_at >= datetime('now', '-7 days')`
        )
        .first(),
      db
        .prepare('SELECT COUNT(*) as count FROM platform_audit_entries')
        .first(),
      db
        .prepare(
          `SELECT COUNT(*) as total,
                  SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as active
           FROM platform_audit_policies`
        )
        .first(),
    ]);

    return {
      success: true,
      data: {
        totalEntries: (totalEntries as any)?.count ?? 0,
        entriesLast7Days: (recent7d as any)?.count ?? 0,
        byAction: (byAction as any).results,
        byResourceType: (byResource as any).results,
        policies: {
          total: (policies as any)?.total ?? 0,
          active: (policies as any)?.active ?? 0,
        },
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminPlatformAuditTrailService = {
  listEntries,
  createEntry,
  getPolicies,
  getDashboard,
};
