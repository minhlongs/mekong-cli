/**
 * Scheduled Mission Service — CRUD, run history, and due-mission queries for cron-based missions
 */

import type { D1Database } from '@cloudflare/workers-types';

export type ScheduledMissionStatus = 'active' | 'paused' | 'completed' | 'failed';
export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface MissionConfig {
  goal: string;
  complexity?: string;
  model?: string;
  project_id?: string;
}

export interface ScheduledMission {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  cron_expression: string;
  timezone: string;
  mission_config: MissionConfig;
  status: ScheduledMissionStatus;
  last_run_at?: string;
  next_run_at?: string;
  run_count: number;
  max_runs?: number;
  created_at: string;
  updated_at: string;
}

export interface ScheduledMissionRun {
  id: string;
  scheduled_mission_id: string;
  tenant_id: string;
  mission_id?: string;
  status: RunStatus;
  started_at: string;
  completed_at?: string;
  error?: string;
}

interface CreateInput {
  name: string;
  description?: string;
  cronExpression: string;
  timezone?: string;
  missionConfig: MissionConfig;
  maxRuns?: number;
}

interface UpdateInput {
  name?: string;
  description?: string;
  cronExpression?: string;
  timezone?: string;
  missionConfig?: MissionConfig;
  status?: ScheduledMissionStatus;
  maxRuns?: number;
}

interface ListOpts {
  status?: ScheduledMissionStatus;
  limit?: number;
  offset?: number;
}

interface RunResult {
  missionId?: string;
  status: RunStatus;
  error?: string;
}

/** Validate cron expression has exactly 5 space-separated parts */
export function validateCronExpression(expr: string): boolean {
  const parts = expr.trim().split(/\s+/);
  return parts.length === 5;
}

/**
 * Simple next-run calculator — covers common patterns only.
 * No full cron parser — KISS principle.
 */
export function calculateNextRun(cronExpression: string, _timezone: string): string {
  const now = new Date();
  const expr = cronExpression.trim();

  if (expr === '* * * * *') {
    // every minute
    now.setMinutes(now.getMinutes() + 1, 0, 0);
  } else if (/^0 \* \* \* \*$/.test(expr)) {
    // every hour at :00
    now.setHours(now.getHours() + 1, 0, 0, 0);
  } else if (/^0 0 \* \* \*$/.test(expr)) {
    // daily at midnight
    now.setDate(now.getDate() + 1);
    now.setHours(0, 0, 0, 0);
  } else {
    // default: 1 hour from now
    now.setHours(now.getHours() + 1, 0, 0, 0);
  }

  return now.toISOString();
}

/** Deserialize a DB row into a ScheduledMission object */
function rowToMission(row: Record<string, unknown>): ScheduledMission {
  return {
    ...row,
    mission_config: typeof row.mission_config === 'string'
      ? JSON.parse(row.mission_config)
      : row.mission_config,
  } as ScheduledMission;
}

// ── CRUD ────────────────────────────────────────────────────────────────────

export async function createScheduledMission(
  db: D1Database,
  tenantId: string,
  input: CreateInput
): Promise<ScheduledMission> {
  if (!validateCronExpression(input.cronExpression)) {
    throw new Error('Invalid cron expression — must have 5 space-separated parts');
  }

  const id = crypto.randomUUID();
  const nextRunAt = calculateNextRun(input.cronExpression, input.timezone ?? 'UTC');
  const configJson = JSON.stringify(input.missionConfig);

  await db.prepare(`
    INSERT INTO scheduled_missions
      (id, tenant_id, name, description, cron_expression, timezone, mission_config, next_run_at, max_runs)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id, tenantId, input.name, input.description ?? null,
    input.cronExpression, input.timezone ?? 'UTC',
    configJson, nextRunAt, input.maxRuns ?? null
  ).run();

  const row = await db.prepare('SELECT * FROM scheduled_missions WHERE id = ?').bind(id).first();
  return rowToMission(row as Record<string, unknown>);
}

export async function getScheduledMissions(
  db: D1Database,
  tenantId: string,
  opts: ListOpts = {}
): Promise<ScheduledMission[]> {
  const { status, limit = 50, offset = 0 } = opts;
  let query = 'SELECT * FROM scheduled_missions WHERE tenant_id = ?';
  const bindings: unknown[] = [tenantId];

  if (status) {
    query += ' AND status = ?';
    bindings.push(status);
  }
  query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
  bindings.push(limit, offset);

  const { results } = await db.prepare(query).bind(...bindings).all();
  return (results as Record<string, unknown>[]).map(rowToMission);
}

export async function getScheduledMission(
  db: D1Database,
  tenantId: string,
  id: string
): Promise<ScheduledMission | null> {
  const row = await db.prepare(
    'SELECT * FROM scheduled_missions WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).first();
  return row ? rowToMission(row as Record<string, unknown>) : null;
}

export async function updateScheduledMission(
  db: D1Database,
  tenantId: string,
  id: string,
  input: UpdateInput
): Promise<ScheduledMission | null> {
  if (input.cronExpression && !validateCronExpression(input.cronExpression)) {
    throw new Error('Invalid cron expression — must have 5 space-separated parts');
  }

  const sets: string[] = ['updated_at = datetime(\'now\')'];
  const bindings: unknown[] = [];

  if (input.name !== undefined) { sets.push('name = ?'); bindings.push(input.name); }
  if (input.description !== undefined) { sets.push('description = ?'); bindings.push(input.description); }
  if (input.cronExpression !== undefined) {
    sets.push('cron_expression = ?');
    bindings.push(input.cronExpression);
    const nextRun = calculateNextRun(input.cronExpression, input.timezone ?? 'UTC');
    sets.push('next_run_at = ?');
    bindings.push(nextRun);
  }
  if (input.timezone !== undefined) { sets.push('timezone = ?'); bindings.push(input.timezone); }
  if (input.missionConfig !== undefined) { sets.push('mission_config = ?'); bindings.push(JSON.stringify(input.missionConfig)); }
  if (input.status !== undefined) { sets.push('status = ?'); bindings.push(input.status); }
  if (input.maxRuns !== undefined) { sets.push('max_runs = ?'); bindings.push(input.maxRuns); }

  bindings.push(id, tenantId);
  await db.prepare(
    `UPDATE scheduled_missions SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ?`
  ).bind(...bindings).run();

  return getScheduledMission(db, tenantId, id);
}

export async function deleteScheduledMission(
  db: D1Database,
  tenantId: string,
  id: string
): Promise<boolean> {
  // Soft delete — set status=completed
  const result = await db.prepare(
    `UPDATE scheduled_missions SET status = 'completed', updated_at = datetime('now')
     WHERE id = ? AND tenant_id = ?`
  ).bind(id, tenantId).run();
  return (result.meta?.changes ?? 0) > 0;
}

export async function pauseScheduledMission(
  db: D1Database,
  tenantId: string,
  id: string
): Promise<ScheduledMission | null> {
  await db.prepare(
    `UPDATE scheduled_missions SET status = 'paused', updated_at = datetime('now')
     WHERE id = ? AND tenant_id = ? AND status = 'active'`
  ).bind(id, tenantId).run();
  return getScheduledMission(db, tenantId, id);
}

export async function resumeScheduledMission(
  db: D1Database,
  tenantId: string,
  id: string
): Promise<ScheduledMission | null> {
  await db.prepare(
    `UPDATE scheduled_missions SET status = 'active', updated_at = datetime('now')
     WHERE id = ? AND tenant_id = ? AND status = 'paused'`
  ).bind(id, tenantId).run();
  return getScheduledMission(db, tenantId, id);
}

// ── Run History ──────────────────────────────────────────────────────────────

export async function recordRun(
  db: D1Database,
  scheduledMissionId: string,
  tenantId: string,
  result: RunResult
): Promise<ScheduledMissionRun> {
  const id = crypto.randomUUID();
  const completedAt = result.status !== 'pending' && result.status !== 'running'
    ? new Date().toISOString() : null;

  await db.prepare(`
    INSERT INTO scheduled_mission_runs
      (id, scheduled_mission_id, tenant_id, mission_id, status, completed_at, error)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id, scheduledMissionId, tenantId,
    result.missionId ?? null, result.status, completedAt, result.error ?? null
  ).run();

  // Update parent: last_run_at, run_count, next_run_at
  const mission = await db.prepare(
    'SELECT cron_expression, timezone FROM scheduled_missions WHERE id = ?'
  ).bind(scheduledMissionId).first() as { cron_expression: string; timezone: string } | null;

  if (mission) {
    const nextRun = calculateNextRun(mission.cron_expression, mission.timezone);
    await db.prepare(`
      UPDATE scheduled_missions
      SET last_run_at = datetime('now'), run_count = run_count + 1, next_run_at = ?, updated_at = datetime('now')
      WHERE id = ?
    `).bind(nextRun, scheduledMissionId).run();
  }

  const row = await db.prepare('SELECT * FROM scheduled_mission_runs WHERE id = ?').bind(id).first();
  return row as unknown as ScheduledMissionRun;
}

export async function getRunHistory(
  db: D1Database,
  scheduledMissionId: string,
  opts: { limit?: number; offset?: number } = {}
): Promise<ScheduledMissionRun[]> {
  const { limit = 50, offset = 0 } = opts;
  const { results } = await db.prepare(
    'SELECT * FROM scheduled_mission_runs WHERE scheduled_mission_id = ? ORDER BY started_at DESC LIMIT ? OFFSET ?'
  ).bind(scheduledMissionId, limit, offset).all();
  return results as unknown as ScheduledMissionRun[];
}

export async function getDueScheduledMissions(db: D1Database): Promise<ScheduledMission[]> {
  const now = new Date().toISOString();
  const { results } = await db.prepare(
    `SELECT * FROM scheduled_missions
     WHERE status = 'active' AND next_run_at <= ?
     ORDER BY next_run_at ASC`
  ).bind(now).all();
  return (results as Record<string, unknown>[]).map(rowToMission);
}
