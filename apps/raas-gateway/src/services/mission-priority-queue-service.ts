/**
 * Mission Priority Queue Service — enqueue, dequeue, peek, rules, metrics
 * Dequeue is priority-descending then SLA-deadline-ascending (earliest deadline wins ties)
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

function uid(): string {
  return crypto.randomUUID();
}

/** Add a mission to the priority queue */
async function enqueue(db: DB, tenantId: string, missionId: string, priority = 5, slaDeadline?: string) {
  const id = uid();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO priority_queue (id, tenant_id, mission_id, priority, status, sla_deadline, queued_at)
     VALUES (?, ?, ?, ?, 'queued', ?, ?)`
  ).bind(id, tenantId, missionId, priority, slaDeadline ?? null, now).run();
  return db.prepare('SELECT * FROM priority_queue WHERE id = ?').bind(id).first();
}

/** Claim the highest-priority queued item (by priority DESC, sla_deadline ASC) */
async function dequeue(db: DB, workerId: string) {
  const item = await db.prepare(
    `SELECT * FROM priority_queue
     WHERE status = 'queued'
     ORDER BY priority DESC, sla_deadline ASC NULLS LAST, queued_at ASC
     LIMIT 1`
  ).first();
  if (!item) return null;
  const now = new Date().toISOString();
  await db.prepare(
    `UPDATE priority_queue SET status = 'running', worker_id = ?, started_at = ? WHERE id = ?`
  ).bind(workerId, now, item.id).run();
  return { ...item, status: 'running', worker_id: workerId, started_at: now };
}

/** Peek at the top N queued items without claiming them */
async function peek(db: DB, limit = 10) {
  const { results } = await db.prepare(
    `SELECT * FROM priority_queue
     WHERE status = 'queued'
     ORDER BY priority DESC, sla_deadline ASC NULLS LAST, queued_at ASC
     LIMIT ?`
  ).bind(limit).all();
  return results;
}

/** Get a single queue item by id */
async function getQueueItem(db: DB, id: string) {
  return db.prepare('SELECT * FROM priority_queue WHERE id = ?').bind(id).first();
}

/** Cancel a queued item (tenant-scoped) */
async function cancelItem(db: DB, tenantId: string, id: string) {
  const item = await db.prepare('SELECT * FROM priority_queue WHERE id = ? AND tenant_id = ?').bind(id, tenantId).first();
  if (!item) return null;
  if (item.status !== 'queued') throw new Error('Only queued items can be cancelled');
  await db.prepare(`UPDATE priority_queue SET status = 'cancelled' WHERE id = ?`).bind(id).run();
  return { ...item, status: 'cancelled' };
}

/** Change priority of a queued item (tenant-scoped) */
async function reprioritize(db: DB, tenantId: string, id: string, newPriority: number) {
  const item = await db.prepare('SELECT * FROM priority_queue WHERE id = ? AND tenant_id = ?').bind(id, tenantId).first();
  if (!item) return null;
  await db.prepare(`UPDATE priority_queue SET priority = ? WHERE id = ?`).bind(newPriority, id).run();
  return { ...item, priority: newPriority };
}

/** List priority rules for tenant (includes global rules) */
async function listRules(db: DB, tenantId: string) {
  const { results } = await db.prepare(
    `SELECT * FROM priority_rules WHERE tenant_id = ? OR is_global = 1 ORDER BY created_at DESC`
  ).bind(tenantId).all();
  return results;
}

/** Create a priority rule (tenant or global) */
async function createRule(db: DB, tenantId: string | undefined, data: Record<string, unknown>) {
  const id = uid();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO priority_rules (id, name, condition_json, priority_boost, sla_minutes, tenant_id, is_global, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id,
    data.name ?? 'Unnamed Rule',
    JSON.stringify(data.condition ?? {}),
    data.priority_boost ?? 0,
    data.sla_minutes ?? 60,
    tenantId ?? null,
    tenantId ? 0 : 1,
    now
  ).run();
  return db.prepare('SELECT * FROM priority_rules WHERE id = ?').bind(id).first();
}

/** Aggregate queue stats by status */
async function getQueueStats(db: DB) {
  const { results } = await db.prepare(
    `SELECT status, COUNT(*) as count, AVG(priority) as avg_priority
     FROM priority_queue GROUP BY status`
  ).all();
  return { by_status: results };
}

/** Record a snapshot of queue metrics */
async function recordMetrics(db: DB, data: Record<string, unknown>) {
  const id = uid();
  await db.prepare(
    `INSERT INTO queue_metrics (id, timestamp, queue_depth, avg_wait_ms, p95_wait_ms, throughput_per_min, priority_distribution_json)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id,
    new Date().toISOString(),
    data.queue_depth ?? 0,
    data.avg_wait_ms ?? 0,
    data.p95_wait_ms ?? 0,
    data.throughput_per_min ?? 0,
    JSON.stringify(data.priority_distribution ?? {})
  ).run();
  return db.prepare('SELECT * FROM queue_metrics WHERE id = ?').bind(id).first();
}

/** Admin overview: stats + recent metrics */
async function getAdminOverview(db: DB) {
  const stats = await getQueueStats(db);
  const { results: recentMetrics } = await db.prepare(
    `SELECT * FROM queue_metrics ORDER BY timestamp DESC LIMIT 10`
  ).all();
  const { results: stalledItems } = await db.prepare(
    `SELECT * FROM priority_queue WHERE status = 'running'
     AND started_at < datetime('now', '-30 minutes') LIMIT 20`
  ).all();
  return { stats, recent_metrics: recentMetrics, stalled_items: stalledItems };
}

export const missionPriorityQueueService = {
  enqueue,
  dequeue,
  peek,
  getQueueItem,
  cancelItem,
  reprioritize,
  listRules,
  createRule,
  getQueueStats,
  recordMetrics,
  getAdminOverview,
};
