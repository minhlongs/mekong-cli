// Admin Command Center Service — execute, log, schedule, and diagnose admin commands
import type { D1Database } from '@cloudflare/workers-types';

const AVAILABLE_COMMANDS = [
  { type: 'system_check', name: 'health_check', description: 'Check system health' },
  { type: 'system_check', name: 'db_stats', description: 'Database table row counts' },
  { type: 'cache_clear', name: 'clear_rate_limits', description: 'Reset rate limit counters' },
  { type: 'tenant_action', name: 'suspend_tenant', description: 'Suspend a tenant' },
  { type: 'tenant_action', name: 'activate_tenant', description: 'Activate a tenant' },
  { type: 'broadcast', name: 'platform_notice', description: 'Broadcast notice to all tenants' },
  { type: 'maintenance', name: 'vacuum_db', description: 'Run SQLite VACUUM' },
  { type: 'maintenance', name: 'purge_old_logs', description: 'Delete audit logs older than 90 days' },
];

/** Execute command and write audit record */
export async function executeCommand(
  db: D1Database,
  commandType: string,
  commandName: string,
  params: Record<string, unknown>,
  executedBy: string,
  targetTenantId?: string
): Promise<Record<string, unknown>> {
  const startedAt = new Date().toISOString();
  const t0 = Date.now();

  // Insert pending record first
  const insertResult = await db.prepare(
    `INSERT INTO admin_commands (command_type, command_name, parameters, executed_by, status, target_tenant_id, started_at)
     VALUES (?, ?, ?, ?, 'running', ?, ?)
     RETURNING id`
  ).bind(commandType, commandName, JSON.stringify(params), executedBy, targetTenantId ?? null, startedAt).first<{ id: string }>();

  const commandId = insertResult?.id ?? `cmd_${Date.now()}`;

  try {
    const result = await runCommand(db, commandType, commandName, params, targetTenantId);
    const durationMs = Date.now() - t0;

    await db.prepare(
      `UPDATE admin_commands SET status='completed', result=?, completed_at=datetime('now'), duration_ms=? WHERE id=?`
    ).bind(JSON.stringify(result), durationMs, commandId).run();

    return { commandId, status: 'completed', result, durationMs };
  } catch (err) {
    const durationMs = Date.now() - t0;
    const errMsg = err instanceof Error ? err.message : String(err);

    await db.prepare(
      `UPDATE admin_commands SET status='failed', error=?, completed_at=datetime('now'), duration_ms=? WHERE id=?`
    ).bind(errMsg, durationMs, commandId).run();

    return { commandId, status: 'failed', error: errMsg, durationMs };
  }
}

async function runCommand(
  db: D1Database,
  commandType: string,
  commandName: string,
  _params: Record<string, unknown>,
  targetTenantId?: string
): Promise<unknown> {
  if (commandType === 'system_check' && commandName === 'health_check') {
    const row = await db.prepare(`SELECT COUNT(*) as tenants FROM tenants`).first<{ tenants: number }>();
    return { ok: true, tenants: row?.tenants ?? 0, timestamp: new Date().toISOString() };
  }
  if (commandType === 'system_check' && commandName === 'db_stats') {
    const rows = await db.prepare(
      `SELECT name FROM sqlite_master WHERE type='table' ORDER BY name`
    ).all<{ name: string }>();
    return { tables: rows.results.map(r => r.name) };
  }
  if (commandType === 'maintenance' && commandName === 'purge_old_logs') {
    const r = await db.prepare(
      `DELETE FROM admin_commands WHERE created_at < datetime('now', '-90 days')`
    ).run();
    return { deleted: r.meta?.changes ?? 0 };
  }
  if (commandType === 'tenant_action' && targetTenantId) {
    const active = commandName === 'activate_tenant' ? 1 : 0;
    await db.prepare(`UPDATE tenants SET active=? WHERE id=?`).bind(active, targetTenantId).run();
    return { tenantId: targetTenantId, active: active === 1 };
  }
  // For commands requiring external side effects (cache_clear, broadcast, vacuum) — log intent
  return { executed: commandName, note: 'acknowledged' };
}

/** List executed commands with optional filters */
export async function listCommands(
  db: D1Database,
  filters?: { status?: string; commandType?: string; limit?: number }
): Promise<unknown[]> {
  const limit = Math.min(filters?.limit ?? 50, 200);
  const conditions: string[] = [];
  const binds: unknown[] = [];

  if (filters?.status) { conditions.push('status = ?'); binds.push(filters.status); }
  if (filters?.commandType) { conditions.push('command_type = ?'); binds.push(filters.commandType); }

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  const rows = await db.prepare(
    `SELECT * FROM admin_commands ${where} ORDER BY created_at DESC LIMIT ?`
  ).bind(...binds, limit).all();

  return rows.results;
}

/** Get single command by ID */
export async function getCommand(db: D1Database, commandId: string): Promise<unknown | null> {
  return db.prepare(`SELECT * FROM admin_commands WHERE id = ?`).bind(commandId).first();
}

/** Return available command types (static catalog) */
export function getAvailableCommands(): typeof AVAILABLE_COMMANDS {
  return AVAILABLE_COMMANDS;
}

/** Create a new scheduled command */
export async function createScheduledCommand(
  db: D1Database,
  config: { commandType: string; commandName: string; parameters?: Record<string, unknown>; cronExpression?: string; nextRunAt?: string }
): Promise<unknown> {
  const row = await db.prepare(
    `INSERT INTO scheduled_commands (command_type, command_name, parameters, cron_expression, next_run_at)
     VALUES (?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    config.commandType, config.commandName,
    JSON.stringify(config.parameters ?? {}),
    config.cronExpression ?? null,
    config.nextRunAt ?? null
  ).first();
  return row;
}

/** List all scheduled commands */
export async function listScheduledCommands(db: D1Database): Promise<unknown[]> {
  const rows = await db.prepare(`SELECT * FROM scheduled_commands ORDER BY created_at DESC`).all();
  return rows.results;
}

/** Update/toggle a scheduled command */
export async function updateScheduledCommand(
  db: D1Database, id: string, updates: Record<string, unknown>
): Promise<unknown | null> {
  const allowed = ['is_active', 'cron_expression', 'next_run_at', 'max_failures', 'parameters'];
  const sets: string[] = ["updated_at = datetime('now')"];
  const binds: unknown[] = [];

  for (const key of allowed) {
    if (key in updates) {
      sets.push(`${key} = ?`);
      binds.push(key === 'parameters' ? JSON.stringify(updates[key]) : updates[key]);
    }
  }

  await db.prepare(`UPDATE scheduled_commands SET ${sets.join(', ')} WHERE id = ?`).bind(...binds, id).run();
  return db.prepare(`SELECT * FROM scheduled_commands WHERE id = ?`).bind(id).first();
}

/** Delete a scheduled command */
export async function deleteScheduledCommand(db: D1Database, id: string): Promise<boolean> {
  const r = await db.prepare(`DELETE FROM scheduled_commands WHERE id = ?`).bind(id).run();
  return (r.meta?.changes ?? 0) > 0;
}

/** Execution stats by type/status for last N days */
export async function getCommandStats(db: D1Database, days = 7): Promise<unknown> {
  const [byType, byStatus] = await Promise.all([
    db.prepare(
      `SELECT command_type, COUNT(*) as count, AVG(duration_ms) as avg_ms
       FROM admin_commands WHERE created_at >= datetime('now', ?)
       GROUP BY command_type ORDER BY count DESC`
    ).bind(`-${days} days`).all(),
    db.prepare(
      `SELECT status, COUNT(*) as count FROM admin_commands
       WHERE created_at >= datetime('now', ?) GROUP BY status`
    ).bind(`-${days} days`).all(),
  ]);
  return { byType: byType.results, byStatus: byStatus.results, days };
}

/** Combined dashboard summary */
export async function getDashboardSummary(db: D1Database): Promise<unknown> {
  const [total, pending, failed, scheduled] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM admin_commands`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM admin_commands WHERE status='pending'`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM admin_commands WHERE status='failed' AND created_at >= datetime('now', '-24 hours')`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM scheduled_commands WHERE is_active=1`).first<{ count: number }>(),
  ]);

  return {
    totalCommands: total?.count ?? 0,
    pendingCommands: pending?.count ?? 0,
    failedLast24h: failed?.count ?? 0,
    activeScheduledCommands: scheduled?.count ?? 0,
    availableCommandTypes: AVAILABLE_COMMANDS.length,
  };
}
