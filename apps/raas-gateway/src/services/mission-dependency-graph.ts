/**
 * Mission Dependency Graph Service
 * Tracks dependencies between missions and execution order.
 * Tables: mission_dependencies, mission_dependency_runs
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

/** List all dependencies for a tenant */
async function listDependencies(db: DB, tenantId: string) {
  try {
    const { results } = await db
      .prepare('SELECT * FROM mission_dependencies WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { success: true, data: { dependencies: results, total: results.length } };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

interface DependencyInput {
  mission_id: string;
  depends_on_mission_id: string;
  dependency_type?: string;
}

/** Create a dependency between two missions */
async function createDependency(db: DB, tenantId: string, data: DependencyInput) {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO mission_dependencies
         (id, tenant_id, mission_id, depends_on_mission_id, dependency_type, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)`
      )
      .bind(
        id,
        tenantId,
        data.mission_id,
        data.depends_on_mission_id,
        data.dependency_type ?? 'required',
        now,
        now
      )
      .run();
    const row = await db
      .prepare('SELECT * FROM mission_dependencies WHERE id = ?')
      .bind(id)
      .first();
    return { success: true, data: row };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Get dependency runs for a tenant */
async function getRuns(db: DB, tenantId: string) {
  try {
    const { results } = await db
      .prepare('SELECT * FROM mission_dependency_runs WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { success: true, data: { runs: results, total: results.length } };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Admin overview: dependency counts + recent entries across all tenants */
async function getAdminOverview(db: DB) {
  try {
    const [countRow, recent] = await Promise.all([
      db.prepare('SELECT COUNT(*) as count FROM mission_dependencies').first(),
      db
        .prepare('SELECT * FROM mission_dependencies ORDER BY created_at DESC LIMIT 20')
        .all(),
    ]);
    return {
      success: true,
      data: {
        total_dependencies: countRow?.count ?? 0,
        recent: recent.results,
      },
    };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

export const missionDependencyGraphService = {
  listDependencies,
  createDependency,
  getRuns,
  getAdminOverview,
};
