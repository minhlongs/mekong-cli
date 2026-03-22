/**
 * Admin Service Registry Service
 * CRUD + dependency graph + dashboard aggregation for registered platform services
 */

// List all service registry entries, optionally filtered by status
async function listServices(db: any, status?: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const query = status
      ? `SELECT * FROM service_registry_entries WHERE status = ? ORDER BY service_name ASC`
      : `SELECT * FROM service_registry_entries ORDER BY service_name ASC`;

    const result = status
      ? await db.prepare(query).bind(status).all()
      : await db.prepare(query).all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create a new service registry entry
async function createService(
  db: any,
  payload: {
    id: string;
    service_name: string;
    service_url: string;
    health_endpoint?: string;
    status?: string;
    version?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const { id, service_name, service_url, health_endpoint, status, version } = payload;
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO service_registry_entries
           (id, service_name, service_url, health_endpoint, status, version, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, service_name, service_url, health_endpoint ?? null, status ?? 'active', version ?? null, now, now)
      .run();

    const created = await db
      .prepare(`SELECT * FROM service_registry_entries WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Get dependency edges for a given service_id
async function getDependencies(
  db: any,
  serviceId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const deps = await db
      .prepare(
        `SELECT d.*, s.service_name as depends_on_name, s.service_url as depends_on_url, s.status as depends_on_status
         FROM service_registry_dependencies d
         JOIN service_registry_entries s ON s.id = d.depends_on_service_id
         WHERE d.service_id = ?
         ORDER BY d.dependency_type ASC`
      )
      .bind(serviceId)
      .all();

    return { success: true, data: deps.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Dashboard: counts by status + recent health checks
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totals, byStatus, recentChecks, depCount] = await Promise.all([
      db
        .prepare(`SELECT COUNT(*) as total FROM service_registry_entries`)
        .first(),
      db
        .prepare(`SELECT status, COUNT(*) as count FROM service_registry_entries GROUP BY status`)
        .all(),
      db
        .prepare(
          `SELECT id, service_name, status, last_health_check, version
           FROM service_registry_entries
           WHERE last_health_check IS NOT NULL
           ORDER BY last_health_check DESC
           LIMIT 10`
        )
        .all(),
      db
        .prepare(`SELECT COUNT(*) as total FROM service_registry_dependencies`)
        .first(),
    ]);

    return {
      success: true,
      data: {
        total_services: totals?.total ?? 0,
        total_dependencies: depCount?.total ?? 0,
        by_status: byStatus.results ?? [],
        recent_health_checks: recentChecks.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminServiceRegistryService = {
  listServices,
  createService,
  getDependencies,
  getDashboard,
};
