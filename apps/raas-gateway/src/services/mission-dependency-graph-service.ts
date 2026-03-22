/**
 * Mission Dependency Graph Service — DAG dependencies, execution groups,
 * critical path analysis. Used by mission-dependency-graph route.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;
interface DependencyData { parent_mission_id: string; child_mission_id: string; dependency_type?: string }
interface GroupData { name: string; missions_json?: string; execution_order?: string }

/** Add a dependency between two missions */
async function addDependency(db: DB, tenantId: string, data: DependencyData) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO mission_dependencies_v2
     (id, tenant_id, parent_mission_id, child_mission_id, dependency_type, status, created_at)
     VALUES (?, ?, ?, ?, ?, 'pending', ?)`
  ).bind(id, tenantId, data.parent_mission_id, data.child_mission_id,
    data.dependency_type ?? 'finish_to_start', now).run();
  return db.prepare('SELECT * FROM mission_dependencies_v2 WHERE id = ?').bind(id).first();
}

/** Remove a dependency by id (tenant-scoped) */
async function removeDependency(db: DB, tenantId: string, id: string) {
  const dep = await db.prepare(
    'SELECT * FROM mission_dependencies_v2 WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).first();
  if (!dep) return null;
  await db.prepare('DELETE FROM mission_dependencies_v2 WHERE id = ?').bind(id).run();
  return { deleted: true, id };
}

/** Get all dependencies for a given mission (as parent or child) */
async function getDependencies(db: DB, tenantId: string, missionId: string) {
  const { results } = await db.prepare(
    `SELECT * FROM mission_dependencies_v2
     WHERE tenant_id = ? AND (parent_mission_id = ? OR child_mission_id = ?)
     ORDER BY created_at DESC`
  ).bind(tenantId, missionId, missionId).all();
  return { dependencies: results, total: results.length };
}

/** Get full DAG rooted at a mission via BFS */
async function getGraph(db: DB, tenantId: string, rootMissionId: string) {
  const visited = new Set<string>([rootMissionId]);
  const edges: unknown[] = [];
  const queue = [rootMissionId];
  while (queue.length > 0) {
    const current = queue.shift()!;
    const { results } = await db.prepare(
      'SELECT * FROM mission_dependencies_v2 WHERE tenant_id = ? AND parent_mission_id = ?'
    ).bind(tenantId, current).all();
    for (const edge of results) {
      edges.push(edge);
      if (!visited.has(edge.child_mission_id)) {
        visited.add(edge.child_mission_id);
        queue.push(edge.child_mission_id);
      }
    }
  }
  return { root: rootMissionId, nodes: Array.from(visited), edges, node_count: visited.size };
}

/** List execution groups for a tenant */
async function listGroups(db: DB, tenantId: string) {
  const { results } = await db.prepare(
    'SELECT * FROM execution_groups WHERE tenant_id = ? ORDER BY created_at DESC'
  ).bind(tenantId).all();
  return { groups: results, total: results.length };
}

/** Create an execution group */
async function createGroup(db: DB, tenantId: string, data: GroupData) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO execution_groups
     (id, tenant_id, name, missions_json, execution_order, status, created_at)
     VALUES (?, ?, ?, ?, ?, 'pending', ?)`
  ).bind(id, tenantId, data.name, data.missions_json ?? '[]',
    data.execution_order ?? 'parallel', now).run();
  return db.prepare('SELECT * FROM execution_groups WHERE id = ?').bind(id).first();
}

/** Update execution group status; sets started_at / completed_at timestamps */
async function updateGroupStatus(db: DB, tenantId: string, id: string, status: string) {
  const group = await db.prepare(
    'SELECT * FROM execution_groups WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).first();
  if (!group) return null;
  const now = new Date().toISOString();
  const started_at = status === 'running' ? now : group.started_at;
  const completed_at = (status === 'completed' || status === 'failed') ? now : group.completed_at;
  await db.prepare(
    'UPDATE execution_groups SET status = ?, started_at = ?, completed_at = ? WHERE id = ?'
  ).bind(status, started_at, completed_at, id).run();
  return db.prepare('SELECT * FROM execution_groups WHERE id = ?').bind(id).first();
}

/** Analyze critical path from root mission — DFS longest path, 1000ms/hop estimate */
async function analyzeCriticalPath(db: DB, tenantId: string, rootMissionId: string) {
  const graph = await getGraph(db, tenantId, rootMissionId);
  const edges = graph.edges as Array<{ parent_mission_id: string; child_mission_id: string }>;
  const children: Record<string, string[]> = {};
  for (const e of edges) { (children[e.parent_mission_id] ??= []).push(e.child_mission_id); }
  const memo: Record<string, string[]> = {};
  const longest = (n: string): string[] => {
    if (memo[n]) return memo[n];
    const kids = children[n] ?? [];
    memo[n] = kids.length === 0 ? [n]
      : [n, ...kids.reduce((b, k) => { const p = longest(k); return p.length > b.length ? p : b; }, [] as string[])];
    return memo[n];
  };
  const criticalPath = longest(rootMissionId);
  const totalDurationMs = (criticalPath.length - 1) * 1000;
  const bottleneck = criticalPath.length > 1 ? criticalPath[Math.floor(criticalPath.length / 2)] : null;
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO critical_path_analysis
     (id, tenant_id, root_mission_id, path_json, total_duration_ms, bottleneck_mission_id, analyzed_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, rootMissionId, JSON.stringify(criticalPath), totalDurationMs, bottleneck, now).run();
  return db.prepare('SELECT * FROM critical_path_analysis WHERE id = ?').bind(id).first();
}

/** Get past critical path analyses for a tenant */
async function getAnalyses(db: DB, tenantId: string) {
  const { results } = await db.prepare(
    'SELECT * FROM critical_path_analysis WHERE tenant_id = ? ORDER BY analyzed_at DESC'
  ).bind(tenantId).all();
  return { analyses: results, total: results.length };
}

/** Admin overview across all tenants */
async function getAdminOverview(db: DB) {
  const [deps, groups, analyses] = await Promise.all([
    db.prepare('SELECT tenant_id, COUNT(*) as count FROM mission_dependencies_v2 GROUP BY tenant_id').all(),
    db.prepare('SELECT status, COUNT(*) as count FROM execution_groups GROUP BY status').all(),
    db.prepare('SELECT COUNT(*) as count FROM critical_path_analysis').first(),
  ]);
  return {
    dependencies_by_tenant: deps.results,
    groups_by_status: groups.results,
    total_analyses: analyses?.count ?? 0,
  };
}

export const missionDependencyGraphService = {
  addDependency, removeDependency, getDependencies, getGraph,
  listGroups, createGroup, updateGroupStatus,
  analyzeCriticalPath, getAnalyses, getAdminOverview,
};
