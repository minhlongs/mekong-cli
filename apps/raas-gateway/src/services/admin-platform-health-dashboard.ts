/**
 * Admin Platform Health Dashboard Service
 * CRUD for platform_health_checks + platform_health_incidents tables
 * All functions: db: any, try/catch, return { success, data/error }
 */

// List all health checks, optionally filtered by service_name
async function listChecks(db: any, service_name?: string): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    let stmt: any;
    if (service_name) {
      stmt = db.prepare(
        `SELECT * FROM platform_health_checks WHERE service_name = ? ORDER BY last_checked_at DESC`
      ).bind(service_name);
    } else {
      stmt = db.prepare(
        `SELECT * FROM platform_health_checks ORDER BY last_checked_at DESC`
      );
    }
    const result = await stmt.all();
    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Insert a new health check record
async function createCheck(
  db: any,
  payload: {
    id: string;
    service_name: string;
    check_type?: string;
    status?: string;
    response_time_ms?: number;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const { id, service_name, check_type = 'http', status = 'healthy', response_time_ms } = payload;
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO platform_health_checks (id, service_name, check_type, status, response_time_ms, last_checked_at, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, service_name, check_type, status, response_time_ms ?? null, now, now)
      .run();
    return { success: true, data: { id, service_name, check_type, status, response_time_ms, last_checked_at: now, created_at: now } };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// List all incidents, optionally filtered by service_name or only unresolved
async function getIncidents(
  db: any,
  service_name?: string,
  unresolved_only?: boolean
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    let sql = `SELECT * FROM platform_health_incidents`;
    const bindings: any[] = [];
    const clauses: string[] = [];

    if (service_name) {
      clauses.push(`service_name = ?`);
      bindings.push(service_name);
    }
    if (unresolved_only) {
      clauses.push(`resolved_at IS NULL`);
    }
    if (clauses.length > 0) {
      sql += ` WHERE ` + clauses.join(' AND ');
    }
    sql += ` ORDER BY created_at DESC`;

    const result = await db.prepare(sql).bind(...bindings).all();
    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Aggregate dashboard: total checks, status breakdown, open incident count, recent activity
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [checksTotal, statusBreakdown, openIncidents, recentChecks] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as total FROM platform_health_checks`).first(),
      db.prepare(
        `SELECT status, COUNT(*) as count FROM platform_health_checks GROUP BY status`
      ).all(),
      db.prepare(
        `SELECT COUNT(*) as total FROM platform_health_incidents WHERE resolved_at IS NULL`
      ).first(),
      db.prepare(
        `SELECT * FROM platform_health_checks ORDER BY last_checked_at DESC LIMIT 10`
      ).all(),
    ]);

    const statusMap: Record<string, number> = {};
    for (const row of (statusBreakdown.results ?? []) as any[]) {
      statusMap[row.status] = row.count;
    }

    return {
      success: true,
      data: {
        checks: {
          total: checksTotal?.total ?? 0,
          by_status: statusMap,
        },
        incidents: {
          open: openIncidents?.total ?? 0,
        },
        recent_checks: recentChecks.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminPlatformHealthDashboardService = {
  listChecks,
  createCheck,
  getIncidents,
  getDashboard,
};
