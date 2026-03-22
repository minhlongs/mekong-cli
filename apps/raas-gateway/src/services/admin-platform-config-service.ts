/**
 * Admin Platform Config Service — CRUD, overrides, history, rollback
 * Used by admin-platform-config route (X-Admin-Key protected)
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

interface ConfigMeta { changedBy?: string; changeReason?: string; valueType?: string; description?: string; category?: string; isSensitive?: number }

/** List all configs, optionally filtered by category */
async function listConfigs(db: DB, category?: string) {
  const where = category ? `WHERE category = '${category}'` : '';
  const { results } = await db
    .prepare(`SELECT * FROM platform_configs ${where} ORDER BY category, config_key`)
    .all();
  return { configs: results, total: results.length };
}

/** Get single config by key */
async function getConfig(db: DB, key: string) {
  return db.prepare('SELECT * FROM platform_configs WHERE config_key = ?').bind(key).first();
}

/** Upsert config value and record history */
async function setConfig(db: DB, key: string, value: string, meta: ConfigMeta = {}) {
  const now = new Date().toISOString();
  const existing = await getConfig(db, key);
  if (existing) {
    await db.prepare(
      'UPDATE platform_configs SET config_value = ?, updated_at = ? WHERE config_key = ?'
    ).bind(value, now, key).run();
    await db.prepare(
      'INSERT INTO config_history (id, config_key, old_value, new_value, changed_by, change_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(crypto.randomUUID(), key, existing.config_value, value, meta.changedBy ?? null, meta.changeReason ?? null, now).run();
  } else {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO platform_configs (id, config_key, config_value, value_type, description, category, is_sensitive, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id, key, value,
      meta.valueType ?? 'string',
      meta.description ?? null,
      meta.category ?? 'general',
      meta.isSensitive ?? 0,
      now, now
    ).run();
    await db.prepare(
      'INSERT INTO config_history (id, config_key, old_value, new_value, changed_by, change_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(crypto.randomUUID(), key, null, value, meta.changedBy ?? null, meta.changeReason ?? null, now).run();
  }
  return getConfig(db, key);
}

/** Delete config and record tombstone in history */
async function deleteConfig(db: DB, key: string) {
  const existing = await getConfig(db, key);
  if (!existing) return null;
  const now = new Date().toISOString();
  await db.prepare('DELETE FROM platform_configs WHERE config_key = ?').bind(key).run();
  await db.prepare(
    'INSERT INTO config_history (id, config_key, old_value, new_value, changed_by, change_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(crypto.randomUUID(), key, existing.config_value, '__deleted__', null, 'config deleted', now).run();
  return { deleted: true };
}

/** Get effective config: environment override first, then base config */
async function getEffectiveConfig(db: DB, key: string, environment: string) {
  const override = await db
    .prepare('SELECT * FROM config_overrides WHERE config_key = ? AND environment = ?')
    .bind(key, environment).first();
  if (override) return { key, value: override.override_value, source: 'override', environment };
  const base = await getConfig(db, key);
  if (!base) return { key, value: null, source: 'not_found', environment };
  return { key, value: base.config_value, source: 'base', environment };
}

/** List all environment overrides for a config key */
async function listOverrides(db: DB, key: string) {
  const { results } = await db
    .prepare('SELECT * FROM config_overrides WHERE config_key = ? ORDER BY environment')
    .bind(key).all();
  return { overrides: results };
}

/** Upsert environment override for a config key */
async function setOverride(db: DB, key: string, environment: string, value: string, createdBy?: string) {
  const now = new Date().toISOString();
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO config_overrides (id, config_key, environment, override_value, created_by, created_at)
     VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT (config_key, environment) DO UPDATE SET override_value = excluded.override_value, created_by = excluded.created_by`
  ).bind(id, key, environment, value, createdBy ?? null, now).run();
  return db.prepare('SELECT * FROM config_overrides WHERE config_key = ? AND environment = ?').bind(key, environment).first();
}

/** Remove environment override for a config key */
async function removeOverride(db: DB, key: string, environment: string) {
  await db.prepare('DELETE FROM config_overrides WHERE config_key = ? AND environment = ?').bind(key, environment).run();
  return { deleted: true };
}

/** Paginated history for a config key (default 20 per page) */
async function getHistory(db: DB, key: string, page = 1, limit = 20) {
  const offset = (page - 1) * limit;
  const { results } = await db
    .prepare('SELECT * FROM config_history WHERE config_key = ? ORDER BY created_at DESC LIMIT ? OFFSET ?')
    .bind(key, limit, offset).all();
  const total = await db.prepare('SELECT COUNT(*) as count FROM config_history WHERE config_key = ?').bind(key).first();
  return { history: results, total: total?.count ?? 0, page, limit };
}

/** Restore config value from a specific history record */
async function rollbackConfig(db: DB, key: string, historyId: string, rolledBackBy?: string) {
  const entry = await db.prepare('SELECT * FROM config_history WHERE id = ? AND config_key = ?').bind(historyId, key).first();
  if (!entry || entry.old_value == null) return null;
  return setConfig(db, key, entry.old_value, { changedBy: rolledBackBy, changeReason: `rollback to history ${historyId}` });
}

/** Admin overview: config counts grouped by category */
async function getAdminOverview(db: DB) {
  const [byCat, total, overrideCount] = await Promise.all([
    db.prepare('SELECT category, COUNT(*) as count FROM platform_configs GROUP BY category').all(),
    db.prepare('SELECT COUNT(*) as count FROM platform_configs').first(),
    db.prepare('SELECT COUNT(*) as count FROM config_overrides').first(),
  ]);
  return { byCategory: byCat.results, total: total?.count ?? 0, totalOverrides: overrideCount?.count ?? 0 };
}

export const adminPlatformConfigService = {
  listConfigs, getConfig, setConfig, deleteConfig,
  getEffectiveConfig, listOverrides, setOverride, removeOverride,
  getHistory, rollbackConfig, getAdminOverview,
};
