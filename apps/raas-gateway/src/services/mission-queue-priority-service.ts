/**
 * Mission Queue Priority Service — manage queue configs and items with priority ordering
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

function uid(): string {
  return crypto.randomUUID();
}

/** List all queue configs for a tenant */
async function listQueues(db: DB, tenantId: string) {
  const { results } = await db.prepare(
    `SELECT * FROM mission_queue_configs WHERE tenant_id = ? ORDER BY priority_level DESC, created_at DESC`
  ).bind(tenantId).all();
  return results as Record<string, unknown>[];
}

/** Create a new queue config for a tenant */
async function createQueue(db: DB, tenantId: string, data: Record<string, unknown>) {
  const id = uid();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO mission_queue_configs
       (id, tenant_id, queue_name, priority_level, max_concurrency, timeout_ms, status, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id,
    tenantId,
    data.queue_name ?? 'default',
    data.priority_level ?? 5,
    data.max_concurrency ?? 10,
    data.timeout_ms ?? 60000,
    data.status ?? 'active',
    now,
    now
  ).run();
  return db.prepare('SELECT * FROM mission_queue_configs WHERE id = ?').bind(id).first() as Promise<Record<string, unknown>>;
}

/** Get items for a tenant queue, ordered by priority desc then enqueued_at asc */
async function getItems(db: DB, tenantId: string, queueId: string) {
  const { results } = await db.prepare(
    `SELECT * FROM mission_queue_items
     WHERE tenant_id = ? AND queue_id = ?
     ORDER BY priority DESC, enqueued_at ASC`
  ).bind(tenantId, queueId).all();
  return results as Record<string, unknown>[];
}

/** Admin overview: queue counts by status + items summary per queue */
async function getAdminOverview(db: DB) {
  const { results: configStats } = await db.prepare(
    `SELECT status, COUNT(*) as count FROM mission_queue_configs GROUP BY status`
  ).all();

  const { results: itemStats } = await db.prepare(
    `SELECT queue_id, status, COUNT(*) as count, AVG(priority) as avg_priority
     FROM mission_queue_items GROUP BY queue_id, status`
  ).all();

  const { results: pendingItems } = await db.prepare(
    `SELECT * FROM mission_queue_items WHERE status = 'pending'
     ORDER BY priority DESC, enqueued_at ASC LIMIT 20`
  ).all();

  return {
    queue_stats: configStats as Record<string, unknown>[],
    item_stats: itemStats as Record<string, unknown>[],
    top_pending: pendingItems as Record<string, unknown>[],
  };
}

export const missionQueuePriorityService = {
  listQueues,
  createQueue,
  getItems,
  getAdminOverview,
};
