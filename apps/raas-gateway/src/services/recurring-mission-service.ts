/**
 * Recurring Mission Service — CRUD + cron scheduling for scheduled missions
 * Supports simple cron patterns: hourly, daily, weekly, every-N-hours
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface RecurringMission {
  id: number;
  tenant_id: string;
  name: string;
  type: string;
  input: string;
  cron_expression: string;
  timezone: string;
  is_active: number;
  last_run_at: string | null;
  next_run_at: string | null;
  run_count: number;
  max_runs: number | null;
  created_at: string;
  updated_at: string;
}

export interface CreateRecurringInput {
  name: string;
  type: string;
  input?: Record<string, unknown>;
  cron_expression: string;
  timezone?: string;
  max_runs?: number;
}

export interface UpdateRecurringInput {
  name?: string;
  cron_expression?: string;
  is_active?: boolean;
  input?: Record<string, unknown>;
  max_runs?: number;
}

// Supported cron patterns — keep simple, no full cron lib needed
const SUPPORTED_CRON_PATTERNS: Record<string, string> = {
  '0 * * * *': 'hourly',
  '0 0 * * *': 'daily',
  '0 0 * * 1': 'weekly (monday)',
  '0 */6 * * *': 'every 6 hours',
  '0 */2 * * *': 'every 2 hours',
  '0 */4 * * *': 'every 4 hours',
  '0 */12 * * *': 'every 12 hours',
};

/**
 * Validate cron expression — only allow known safe patterns
 */
function validateCron(expr: string): boolean {
  return expr in SUPPORTED_CRON_PATTERNS;
}

/**
 * Calculate next run time from cron expression
 * Returns ISO string of next execution time (UTC)
 */
export function getNextRun(cronExpr: string, _timezone: string = 'UTC'): string {
  const now = new Date();
  const next = new Date(now);

  // Parse cron: minute hour * * *
  const parts = cronExpr.trim().split(/\s+/);
  if (parts.length !== 5) throw new Error(`Invalid cron: ${cronExpr}`);

  const [minutePart, hourPart] = parts;

  if (cronExpr === '0 * * * *') {
    // Every hour: next whole hour
    next.setMinutes(0, 0, 0);
    next.setHours(next.getHours() + 1);
  } else if (cronExpr === '0 0 * * *') {
    // Daily at midnight UTC
    next.setHours(0, 0, 0, 0);
    next.setDate(next.getDate() + 1);
  } else if (cronExpr === '0 0 * * 1') {
    // Weekly on Monday at midnight UTC
    const daysUntilMonday = (1 - now.getDay() + 7) % 7 || 7;
    next.setHours(0, 0, 0, 0);
    next.setDate(next.getDate() + daysUntilMonday);
  } else if (hourPart.startsWith('*/')) {
    // Every N hours: 0 */6 * * * etc.
    const interval = parseInt(hourPart.slice(2), 10);
    if (isNaN(interval) || interval < 1) throw new Error(`Invalid interval: ${hourPart}`);
    next.setMinutes(parseInt(minutePart, 10), 0, 0);
    // Advance by interval until we're past now
    while (next <= now) {
      next.setHours(next.getHours() + interval);
    }
  } else {
    throw new Error(`Unsupported cron pattern: ${cronExpr}`);
  }

  return next.toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');
}

export class RecurringMissionService {
  /**
   * Create a new recurring mission
   */
  async create(
    db: D1Database,
    tenantId: string,
    data: CreateRecurringInput
  ): Promise<RecurringMission> {
    if (!validateCron(data.cron_expression)) {
      const supported = Object.keys(SUPPORTED_CRON_PATTERNS).join(', ');
      throw new Error(`Unsupported cron expression. Supported: ${supported}`);
    }

    const nextRunAt = getNextRun(data.cron_expression, data.timezone ?? 'UTC');
    const inputJson = JSON.stringify(data.input ?? {});

    const result = await db
      .prepare(
        `INSERT INTO recurring_missions
         (tenant_id, name, type, input, cron_expression, timezone, next_run_at, max_runs)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
         RETURNING *`
      )
      .bind(
        tenantId,
        data.name,
        data.type,
        inputJson,
        data.cron_expression,
        data.timezone ?? 'UTC',
        nextRunAt,
        data.max_runs ?? null
      )
      .first<RecurringMission>();

    if (!result) throw new Error('Failed to create recurring mission');
    return result;
  }

  /**
   * List recurring missions for a tenant
   */
  async list(
    db: D1Database,
    tenantId: string,
    opts: { active?: boolean } = {}
  ): Promise<RecurringMission[]> {
    let query = 'SELECT * FROM recurring_missions WHERE tenant_id = ?';
    const bindings: (string | number)[] = [tenantId];

    if (opts.active !== undefined) {
      query += ' AND is_active = ?';
      bindings.push(opts.active ? 1 : 0);
    }

    query += ' ORDER BY created_at DESC';

    const result = await db.prepare(query).bind(...bindings).all<RecurringMission>();
    return result.results;
  }

  /**
   * Get single recurring mission (tenant-scoped)
   */
  async getById(
    db: D1Database,
    id: number,
    tenantId: string
  ): Promise<RecurringMission | null> {
    return db
      .prepare('SELECT * FROM recurring_missions WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .first<RecurringMission>();
  }

  /**
   * Update recurring mission fields
   */
  async update(
    db: D1Database,
    id: number,
    tenantId: string,
    data: UpdateRecurringInput
  ): Promise<RecurringMission> {
    const existing = await this.getById(db, id, tenantId);
    if (!existing) throw new Error('Recurring mission not found');

    if (data.cron_expression && !validateCron(data.cron_expression)) {
      const supported = Object.keys(SUPPORTED_CRON_PATTERNS).join(', ');
      throw new Error(`Unsupported cron expression. Supported: ${supported}`);
    }

    const cronExpr = data.cron_expression ?? existing.cron_expression;
    const nextRunAt = getNextRun(cronExpr, existing.timezone);

    const result = await db
      .prepare(
        `UPDATE recurring_missions SET
           name = ?,
           cron_expression = ?,
           is_active = ?,
           input = ?,
           max_runs = ?,
           next_run_at = ?,
           updated_at = datetime('now')
         WHERE id = ? AND tenant_id = ?
         RETURNING *`
      )
      .bind(
        data.name ?? existing.name,
        cronExpr,
        data.is_active !== undefined ? (data.is_active ? 1 : 0) : existing.is_active,
        data.input !== undefined ? JSON.stringify(data.input) : existing.input,
        data.max_runs !== undefined ? data.max_runs : existing.max_runs,
        nextRunAt,
        id,
        tenantId
      )
      .first<RecurringMission>();

    if (!result) throw new Error('Update failed');
    return result;
  }

  /**
   * Soft delete — sets is_active = 0
   */
  async delete(db: D1Database, id: number, tenantId: string): Promise<void> {
    const existing = await this.getById(db, id, tenantId);
    if (!existing) throw new Error('Recurring mission not found');

    await db
      .prepare(
        `UPDATE recurring_missions SET is_active = 0, updated_at = datetime('now')
         WHERE id = ? AND tenant_id = ?`
      )
      .bind(id, tenantId)
      .run();
  }

  /**
   * Process all due recurring missions — called by scheduled handler
   * Finds active missions with next_run_at <= now, creates mission rows, updates schedule
   */
  async processDue(db: D1Database): Promise<{ triggered: number }> {
    const now = new Date().toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');

    const due = await db
      .prepare(
        `SELECT * FROM recurring_missions
         WHERE is_active = 1 AND next_run_at <= ?
         ORDER BY next_run_at ASC
         LIMIT 50`
      )
      .bind(now)
      .all<RecurringMission>();

    let triggered = 0;

    for (const rm of due.results) {
      try {
        // Check max_runs limit
        if (rm.max_runs !== null && rm.run_count >= rm.max_runs) {
          await db
            .prepare(
              `UPDATE recurring_missions SET is_active = 0, updated_at = datetime('now')
               WHERE id = ?`
            )
            .bind(rm.id)
            .run();
          continue;
        }

        const missionId = crypto.randomUUID();
        const inputData = (() => {
          try { return JSON.parse(rm.input); } catch { return {}; }
        })();

        // Insert mission into missions table
        await db
          .prepare(
            `INSERT INTO missions (id, tenant_id, goal, complexity, status, created_at)
             VALUES (?, ?, ?, 'standard', 'queued', datetime('now'))`
          )
          .bind(
            missionId,
            rm.tenant_id,
            inputData.goal ?? `[Recurring] ${rm.name} (${rm.type})`
          )
          .run();

        // Calculate next run
        const nextRun = getNextRun(rm.cron_expression, rm.timezone);

        await db
          .prepare(
            `UPDATE recurring_missions SET
               last_run_at = datetime('now'),
               next_run_at = ?,
               run_count = run_count + 1,
               updated_at = datetime('now')
             WHERE id = ?`
          )
          .bind(nextRun, rm.id)
          .run();

        triggered++;
      } catch (err) {
        console.error(`[RecurringMission] Failed to trigger id=${rm.id}:`, err);
      }
    }

    return { triggered };
  }
}
