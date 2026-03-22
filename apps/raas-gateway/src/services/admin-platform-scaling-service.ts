/**
 * Admin Platform Scaling Service — manage auto-scaling rules and event history
 * Used by admin-platform-scaling route (X-Admin-Key protected)
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

interface ScalingRule {
  id: string;
  rule_name: string;
  metric_trigger: string;
  scale_direction: string;
  threshold: number;
  cooldown_seconds: number;
  max_instances: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface ScalingEvent {
  id: string;
  rule_id: string;
  previous_count: number;
  new_count: number;
  trigger_value: number;
  status: string;
  created_at: string;
}

interface CreateRuleInput {
  rule_name: string;
  metric_trigger: string;
  scale_direction?: string;
  threshold: number;
  cooldown_seconds?: number;
  max_instances?: number;
}

/** List all scaling rules, optionally filtered by is_active */
async function listRules(db: DB, activeOnly?: boolean) {
  const where = activeOnly ? 'WHERE is_active = 1' : '';
  const { results } = await db
    .prepare(`SELECT * FROM scaling_rules ${where} ORDER BY created_at DESC`)
    .all();
  return { rules: results as ScalingRule[], total: results.length };
}

/** Create a new scaling rule */
async function createRule(db: DB, input: CreateRuleInput) {
  const now = new Date().toISOString();
  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO scaling_rules
        (id, rule_name, metric_trigger, scale_direction, threshold, cooldown_seconds, max_instances, is_active, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)`
    )
    .bind(
      id,
      input.rule_name,
      input.metric_trigger,
      input.scale_direction ?? 'up',
      input.threshold,
      input.cooldown_seconds ?? 300,
      input.max_instances ?? 10,
      now,
      now
    )
    .run();
  return db.prepare('SELECT * FROM scaling_rules WHERE id = ?').bind(id).first() as Promise<ScalingRule>;
}

/** List scaling events, optionally filtered by rule_id or status */
async function getEvents(db: DB, opts: { rule_id?: string; status?: string; limit?: number } = {}) {
  const conditions: string[] = [];
  const bindings: (string | number)[] = [];
  if (opts.rule_id) { conditions.push('rule_id = ?'); bindings.push(opts.rule_id); }
  if (opts.status) { conditions.push('status = ?'); bindings.push(opts.status); }
  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  const limit = opts.limit ?? 100;
  const { results } = await db
    .prepare(`SELECT * FROM scaling_events ${where} ORDER BY created_at DESC LIMIT ${limit}`)
    .bind(...bindings)
    .all();
  return { events: results as ScalingEvent[], total: results.length };
}

/** Dashboard: active rules count, recent events summary, direction breakdown */
async function getDashboard(db: DB) {
  const { results: rules } = await db
    .prepare('SELECT scale_direction, COUNT(*) as count FROM scaling_rules WHERE is_active = 1 GROUP BY scale_direction')
    .all();
  const { results: recentEvents } = await db
    .prepare("SELECT * FROM scaling_events ORDER BY created_at DESC LIMIT 10")
    .all();
  const totalActive = (rules as { scale_direction: string; count: number }[]).reduce((s, r) => s + r.count, 0);
  return { active_rules: totalActive, direction_breakdown: rules, recent_events: recentEvents };
}

export const adminPlatformScalingService = { listRules, createRule, getEvents, getDashboard };
