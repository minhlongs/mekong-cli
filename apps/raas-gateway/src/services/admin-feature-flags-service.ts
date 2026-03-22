/**
 * Admin Feature Flags Service — CRUD, evaluation, overrides, history
 * Used by admin-feature-flags route (X-Admin-Key protected)
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

interface FlagFilters { status?: string; page?: number; limit?: number }
interface FlagData {
  flag_key: string; name: string; description?: string; flag_type?: string;
  default_value?: string; rollout_percentage?: number; targeting_rules_json?: string; status?: string;
}

/** Paginated list of flags with optional status filter */
async function listFlags(db: DB, filters: FlagFilters = {}) {
  const { status, page = 1, limit = 20 } = filters;
  const offset = (page - 1) * limit;
  const where = status ? `WHERE status = '${status}'` : '';
  const { results } = await db
    .prepare(`SELECT * FROM feature_flags ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`)
    .bind(limit, offset).all();
  const total = await db.prepare(`SELECT COUNT(*) as count FROM feature_flags ${where}`).first();
  return { flags: results, total: total?.count ?? 0, page, limit };
}

/** Get single flag by id */
async function getFlag(db: DB, id: string) {
  return db.prepare('SELECT * FROM feature_flags WHERE id = ?').bind(id).first();
}

/** Create new flag, returns created record */
async function createFlag(db: DB, data: FlagData) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO feature_flags (id, flag_key, name, description, flag_type, default_value, rollout_percentage, targeting_rules_json, status, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id, data.flag_key, data.name, data.description ?? null,
    data.flag_type ?? 'boolean', data.default_value ?? 'false',
    data.rollout_percentage ?? 0, data.targeting_rules_json ?? '[]',
    data.status ?? 'inactive', now, now
  ).run();
  return getFlag(db, id);
}

/** Update flag fields and record history entry */
async function updateFlag(db: DB, id: string, data: Partial<FlagData>, changedBy?: string) {
  const old = await getFlag(db, id);
  if (!old) return null;
  const now = new Date().toISOString();
  const keys = Object.keys(data).filter((k) => k in old);
  if (keys.length) {
    const fields = keys.map((k) => `${k} = ?`).join(', ');
    const values = keys.map((k) => (data as Record<string, unknown>)[k]);
    await db.prepare(`UPDATE feature_flags SET ${fields}, updated_at = ? WHERE id = ?`).bind(...values, now, id).run();
    await db.prepare(
      'INSERT INTO feature_flag_history (id, flag_id, change_type, old_value, new_value, changed_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(crypto.randomUUID(), id, 'update', JSON.stringify(old), JSON.stringify(data), changedBy ?? null, now).run();
  }
  return getFlag(db, id);
}

/** Toggle flag active/inactive and record history */
async function toggleFlag(db: DB, id: string, status: string, changedBy?: string) {
  const old = await getFlag(db, id);
  if (!old) return null;
  const now = new Date().toISOString();
  await db.prepare('UPDATE feature_flags SET status = ?, updated_at = ? WHERE id = ?').bind(status, now, id).run();
  await db.prepare(
    'INSERT INTO feature_flag_history (id, flag_id, change_type, old_value, new_value, changed_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(crypto.randomUUID(), id, 'toggle', old.status, status, changedBy ?? null, now).run();
  return getFlag(db, id);
}

/** Delete flag by id */
async function deleteFlag(db: DB, id: string) {
  await db.prepare('DELETE FROM feature_flags WHERE id = ?').bind(id).run();
  return { deleted: true };
}

/**
 * Evaluate flag for a tenant:
 * 1. Tenant override → return override value
 * 2. Rollout percentage → deterministic bucket (sum char codes % 100)
 * 3. Fall back to default_value
 */
async function evaluateFlag(db: DB, flagKey: string, tenantId?: string) {
  const flag = await db.prepare('SELECT * FROM feature_flags WHERE flag_key = ?').bind(flagKey).first();
  if (!flag) return { flagKey, value: false, reason: 'not_found' };
  if (tenantId) {
    const ov = await db
      .prepare('SELECT override_value FROM feature_flag_overrides WHERE flag_id = ? AND tenant_id = ?')
      .bind(flag.id, tenantId).first();
    if (ov) return { flagKey, value: ov.override_value, reason: 'override' };
  }
  const pct = flag.rollout_percentage ?? 0;
  if (pct > 0 && tenantId) {
    const bucket = [...tenantId].reduce((acc: number, c: string) => acc + c.charCodeAt(0), 0) % 100;
    if (bucket < pct) return { flagKey, value: flag.default_value, reason: 'rollout' };
  }
  return { flagKey, value: flag.default_value, reason: 'default' };
}

/** List overrides for a flag */
async function listOverrides(db: DB, flagId: string) {
  const { results } = await db
    .prepare('SELECT * FROM feature_flag_overrides WHERE flag_id = ? ORDER BY created_at DESC')
    .bind(flagId).all();
  return results;
}

/** Upsert tenant override for a flag */
async function setOverride(db: DB, flagId: string, tenantId: string, value: string, reason?: string, createdBy?: string) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db.prepare(
    `INSERT INTO feature_flag_overrides (id, flag_id, tenant_id, override_value, reason, created_by, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT (flag_id, tenant_id) DO UPDATE SET override_value = excluded.override_value, reason = excluded.reason`
  ).bind(id, flagId, tenantId, value, reason ?? null, createdBy ?? null, now).run();
  return db.prepare('SELECT * FROM feature_flag_overrides WHERE flag_id = ? AND tenant_id = ?').bind(flagId, tenantId).first();
}

/** Remove tenant override */
async function removeOverride(db: DB, flagId: string, tenantId: string) {
  await db.prepare('DELETE FROM feature_flag_overrides WHERE flag_id = ? AND tenant_id = ?').bind(flagId, tenantId).run();
  return { deleted: true };
}

/** Admin overview: flag counts by status + 10 most recent history entries */
async function getAdminOverview(db: DB) {
  const [counts, recent] = await Promise.all([
    db.prepare('SELECT status, COUNT(*) as count FROM feature_flags GROUP BY status').all(),
    db.prepare('SELECT * FROM feature_flag_history ORDER BY created_at DESC LIMIT 10').all(),
  ]);
  return { counts: counts.results, recentChanges: recent.results };
}

export const adminFeatureFlagsService = {
  listFlags, getFlag, createFlag, updateFlag, toggleFlag, deleteFlag,
  evaluateFlag, listOverrides, setOverride, removeOverride, getAdminOverview,
};
