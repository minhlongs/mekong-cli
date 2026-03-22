/**
 * Mission Dependencies Service — DAG-based mission chain management
 * Handles chain lifecycle, dependency resolution, and mission state transitions
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface MissionChain {
  id: string; tenant_id: string; name: string; description: string | null;
  status: string; total_missions: number; completed_missions: number;
  failed_missions: number; started_at: string | null; completed_at: string | null;
  created_at: string; updated_at: string;
}
export interface MissionDependency {
  id: string; chain_id: string; mission_id: string;
  depends_on_mission_id: string | null; tenant_id: string;
  position: number; status: string; mission_config: string;
  result: string | null; started_at: string | null;
  completed_at: string | null; created_at: string;
}

// ── Chain CRUD ──────────────────────────────────────────────────────────────

/** Create a new mission chain in draft status */
export async function createChain(
  db: D1Database, tenantId: string, name: string, description?: string
): Promise<MissionChain> {
  const id = 'mc_' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
  await db.prepare(
    `INSERT INTO mission_chains (id, tenant_id, name, description) VALUES (?, ?, ?, ?)`
  ).bind(id, tenantId, name, description ?? null).run();
  return db.prepare('SELECT * FROM mission_chains WHERE id = ?')
    .bind(id).first<MissionChain>() as Promise<MissionChain>;
}

/** List chains for a tenant, optionally filtered by status */
export async function listChains(db: D1Database, tenantId: string, status?: string): Promise<MissionChain[]> {
  let sql = `SELECT * FROM mission_chains WHERE tenant_id = ?`;
  const binds: unknown[] = [tenantId];
  if (status) { sql += ` AND status = ?`; binds.push(status); }
  const r = await db.prepare(sql + ` ORDER BY created_at DESC`).bind(...binds).all<MissionChain>();
  return r.results ?? [];
}

/** Get chain with its dependency nodes */
export async function getChain(
  db: D1Database, chainId: string, tenantId: string
): Promise<{ chain: MissionChain; dependencies: MissionDependency[] } | null> {
  const chain = await db.prepare(
    `SELECT * FROM mission_chains WHERE id = ? AND tenant_id = ?`
  ).bind(chainId, tenantId).first<MissionChain>();
  if (!chain) return null;
  const deps = await db.prepare(
    `SELECT * FROM mission_dependencies WHERE chain_id = ? ORDER BY position ASC`
  ).bind(chainId).all<MissionDependency>();
  return { chain, dependencies: deps.results ?? [] };
}

// ── Dependency Node Management ──────────────────────────────────────────────

/** Add a mission node to a chain; dependsOn = null means root node */
export async function addDependency(
  db: D1Database, chainId: string, tenantId: string,
  missionId: string, dependsOn?: string, config?: Record<string, unknown>
): Promise<MissionDependency> {
  const id = 'md_' + crypto.randomUUID().replace(/-/g, '').slice(0, 16);
  const pos = await db.prepare(
    `SELECT COALESCE(MAX(position), -1) + 1 AS next FROM mission_dependencies WHERE chain_id = ?`
  ).bind(chainId).first<{ next: number }>();
  await db.prepare(
    `INSERT INTO mission_dependencies
      (id, chain_id, mission_id, depends_on_mission_id, tenant_id, position, mission_config)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, chainId, missionId, dependsOn ?? null, tenantId, pos?.next ?? 0, JSON.stringify(config ?? {})).run();
  await db.prepare(
    `UPDATE mission_chains SET total_missions = total_missions + 1, updated_at = datetime('now') WHERE id = ?`
  ).bind(chainId).run();
  return db.prepare('SELECT * FROM mission_dependencies WHERE id = ?')
    .bind(id).first<MissionDependency>() as Promise<MissionDependency>;
}

/** Remove a dependency node from chain */
export async function removeDependency(
  db: D1Database, depId: string, tenantId: string
): Promise<boolean> {
  const dep = await db.prepare(
    `SELECT chain_id FROM mission_dependencies WHERE id = ? AND tenant_id = ?`
  ).bind(depId, tenantId).first<{ chain_id: string }>();
  if (!dep) return false;
  await db.prepare(`DELETE FROM mission_dependencies WHERE id = ?`).bind(depId).run();
  await db.prepare(
    `UPDATE mission_chains SET total_missions = MAX(0, total_missions - 1), updated_at = datetime('now') WHERE id = ?`
  ).bind(dep.chain_id).run();
  return true;
}

// ── Chain Execution ─────────────────────────────────────────────────────────

/** Activate chain and mark root nodes (no deps) as ready */
export async function startChain(db: D1Database, chainId: string, tenantId: string): Promise<MissionChain | null> {
  const chain = await db.prepare(
    `SELECT * FROM mission_chains WHERE id = ? AND tenant_id = ?`
  ).bind(chainId, tenantId).first<MissionChain>();
  if (!chain || chain.status !== 'draft') return null;
  await db.prepare(
    `UPDATE mission_dependencies SET status = 'ready'
     WHERE chain_id = ? AND depends_on_mission_id IS NULL AND status = 'pending'`
  ).bind(chainId).run();
  await db.prepare(
    `UPDATE mission_chains SET status = 'active', started_at = datetime('now'), updated_at = datetime('now') WHERE id = ?`
  ).bind(chainId).run();
  return db.prepare('SELECT * FROM mission_chains WHERE id = ?')
    .bind(chainId).first<MissionChain>() as Promise<MissionChain>;
}

/** Mark a mission as completed; unlock dependents whose all deps are done */
export async function completeMission(
  db: D1Database, chainId: string, missionId: string,
  tenantId: string, result: Record<string, unknown>
): Promise<{ chain: MissionChain; unlocked: string[] }> {
  const resultStr = JSON.stringify(result);
  await db.prepare(
    `UPDATE mission_dependencies
     SET status = 'completed', result = ?, completed_at = datetime('now')
     WHERE chain_id = ? AND mission_id = ? AND tenant_id = ?`
  ).bind(resultStr, chainId, missionId, tenantId).run();
  await db.prepare(
    `UPDATE mission_chains SET completed_missions = completed_missions + 1, updated_at = datetime('now') WHERE id = ?`
  ).bind(chainId).run();
  // Unlock dependents: nodes that depend on this mission and whose dependency is now done
  const dependents = await db.prepare(
    `SELECT id, mission_id FROM mission_dependencies WHERE chain_id = ? AND depends_on_mission_id = ? AND status = 'pending'`
  ).bind(chainId, missionId).all<{ id: string; mission_id: string }>();
  const unlocked: string[] = [];
  for (const dep of (dependents.results ?? [])) {
    await db.prepare(
      `UPDATE mission_dependencies SET status = 'ready' WHERE id = ?`
    ).bind(dep.id).run();
    unlocked.push(dep.mission_id);
  }
  const chain = await db.prepare('SELECT * FROM mission_chains WHERE id = ?')
    .bind(chainId).first<MissionChain>() as MissionChain;
  if (chain.completed_missions >= chain.total_missions && chain.total_missions > 0) {
    await db.prepare(
      `UPDATE mission_chains SET status = 'completed', completed_at = datetime('now'), updated_at = datetime('now') WHERE id = ?`
    ).bind(chainId).run();
  }
  const updated = await db.prepare('SELECT * FROM mission_chains WHERE id = ?')
    .bind(chainId).first<MissionChain>() as MissionChain;
  return { chain: updated, unlocked };
}

/** Mark a mission as failed; set dependent nodes to skipped */
export async function failMission(db: D1Database, chainId: string, missionId: string, tenantId: string, error: string): Promise<MissionChain | null> {
  await db.prepare(
    `UPDATE mission_dependencies SET status = 'failed', result = ?, completed_at = datetime('now')
     WHERE chain_id = ? AND mission_id = ? AND tenant_id = ?`
  ).bind(JSON.stringify({ error }), chainId, missionId, tenantId).run();
  await db.prepare(
    `UPDATE mission_chains SET failed_missions = failed_missions + 1, updated_at = datetime('now') WHERE id = ?`
  ).bind(chainId).run();
  await db.prepare(
    `UPDATE mission_dependencies SET status = 'skipped'
     WHERE chain_id = ? AND depends_on_mission_id = ? AND status = 'pending'`
  ).bind(chainId, missionId).run();
  await db.prepare(
    `UPDATE mission_chains SET status = 'failed', updated_at = datetime('now') WHERE id = ?`
  ).bind(chainId).run();
  return db.prepare('SELECT * FROM mission_chains WHERE id = ?')
    .bind(chainId).first<MissionChain>();
}

/** Get missions whose dependencies are all satisfied (status = ready) */
export async function getReadyMissions(
  db: D1Database, chainId: string, tenantId: string
): Promise<MissionDependency[]> {
  const r = await db.prepare(
    `SELECT * FROM mission_dependencies WHERE chain_id = ? AND tenant_id = ? AND status = 'ready' ORDER BY position ASC`
  ).bind(chainId, tenantId).all<MissionDependency>();
  return r.results ?? [];
}

// ── Admin ───────────────────────────────────────────────────────────────────

/** Platform-wide chain statistics for admin monitoring */
export async function getAdminChainOverview(db: D1Database): Promise<{ total: number; by_status: Record<string, number>; total_missions: number }> {
  const rows = await db.prepare(
    `SELECT status, COUNT(*) AS cnt, SUM(total_missions) AS missions
     FROM mission_chains GROUP BY status`
  ).all<{ status: string; cnt: number; missions: number }>();
  const byStatus: Record<string, number> = {};
  let total = 0; let totalMissions = 0;
  for (const row of (rows.results ?? [])) {
    byStatus[row.status] = row.cnt;
    total += row.cnt;
    totalMissions += row.missions ?? 0;
  }
  return { total, by_status: byStatus, total_missions: totalMissions };
}
