/**
 * Feature Flag Service — evaluation engine with percentage rollout,
 * tenant overrides, variant support, and evaluation logging
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface FeatureFlag {
  id: string;
  key: string;
  name: string;
  description?: string;
  flag_type: 'boolean' | 'percentage' | 'variant' | 'tenant_list';
  default_value: string;
  enabled: number;
  rollout_percentage: number;
  variants: string;
  tenant_overrides: string;
  metadata: string;
  created_at: string;
  updated_at: string;
}

export interface CreateFlagInput {
  key: string;
  name: string;
  description?: string;
  flagType?: FeatureFlag['flag_type'];
  defaultValue?: string;
  enabled?: boolean;
  rolloutPercentage?: number;
  variants?: unknown[];
}

export interface UpdateFlagInput {
  name?: string;
  description?: string;
  flagType?: FeatureFlag['flag_type'];
  defaultValue?: string;
  enabled?: boolean;
  rolloutPercentage?: number;
  variants?: unknown[];
}

/** Deterministic hash: sum of charCodes mod 100 — fast, no crypto needed */
function hashCode(str: string): number {
  let h = 0;
  for (let i = 0; i < str.length; i++) h += str.charCodeAt(i);
  return h % 100;
}

function newId(): string {
  return crypto.randomUUID();
}

export async function createFlag(db: D1Database, input: CreateFlagInput): Promise<FeatureFlag> {
  const id = newId();
  const { key, name, description, flagType = 'boolean', defaultValue = 'false',
    enabled = false, rolloutPercentage = 0, variants = [] } = input;

  await db.prepare(
    `INSERT INTO feature_flags
      (id, key, name, description, flag_type, default_value, enabled, rollout_percentage, variants)
     VALUES (?,?,?,?,?,?,?,?,?)`
  ).bind(id, key, name, description ?? null, flagType, defaultValue,
    enabled ? 1 : 0, rolloutPercentage, JSON.stringify(variants)).run();

  return getFlag(db, key) as Promise<FeatureFlag>;
}

export async function getFlags(db: D1Database): Promise<FeatureFlag[]> {
  const { results } = await db.prepare(
    'SELECT * FROM feature_flags ORDER BY created_at DESC'
  ).all<FeatureFlag>();
  return results;
}

export async function getFlag(db: D1Database, key: string): Promise<FeatureFlag | null> {
  return db.prepare('SELECT * FROM feature_flags WHERE key = ?').bind(key).first<FeatureFlag>();
}

export async function updateFlag(db: D1Database, key: string, updates: UpdateFlagInput): Promise<FeatureFlag | null> {
  const fields: string[] = ['updated_at = datetime(\'now\')'];
  const values: unknown[] = [];

  if (updates.name !== undefined)              { fields.push('name = ?');               values.push(updates.name); }
  if (updates.description !== undefined)       { fields.push('description = ?');        values.push(updates.description); }
  if (updates.flagType !== undefined)          { fields.push('flag_type = ?');          values.push(updates.flagType); }
  if (updates.defaultValue !== undefined)      { fields.push('default_value = ?');      values.push(updates.defaultValue); }
  if (updates.enabled !== undefined)           { fields.push('enabled = ?');            values.push(updates.enabled ? 1 : 0); }
  if (updates.rolloutPercentage !== undefined) { fields.push('rollout_percentage = ?'); values.push(updates.rolloutPercentage); }
  if (updates.variants !== undefined)          { fields.push('variants = ?');           values.push(JSON.stringify(updates.variants)); }

  if (fields.length === 1) return getFlag(db, key); // only updated_at — no-op

  values.push(key);
  await db.prepare(`UPDATE feature_flags SET ${fields.join(', ')} WHERE key = ?`).bind(...values).run();
  return getFlag(db, key);
}

export async function deleteFlag(db: D1Database, key: string): Promise<boolean> {
  const { success } = await db.prepare('DELETE FROM feature_flags WHERE key = ?').bind(key).run();
  return success;
}

/** Core evaluation logic — tenant_overrides → type logic → default */
export async function evaluateFlag(db: D1Database, flagKey: string, tenantId: string): Promise<string> {
  const flag = await getFlag(db, flagKey);
  if (!flag || !flag.enabled) return 'false';

  // 1. Check per-tenant override
  const overrides: Record<string, string> = JSON.parse(flag.tenant_overrides || '{}');
  if (overrides[tenantId] !== undefined) {
    const result = overrides[tenantId];
    await logEvaluation(db, flagKey, tenantId, result);
    return result;
  }

  let result = flag.default_value;

  // 2. Type-specific logic
  if (flag.flag_type === 'percentage') {
    const bucket = hashCode(tenantId + flagKey);
    result = bucket < flag.rollout_percentage ? 'true' : 'false';
  } else if (flag.flag_type === 'tenant_list') {
    const list: string[] = JSON.parse(flag.variants || '[]');
    result = list.includes(tenantId) ? 'true' : 'false';
  }

  await logEvaluation(db, flagKey, tenantId, result);
  return result;
}

async function logEvaluation(db: D1Database, flagKey: string, tenantId: string, result: string): Promise<void> {
  // Fire-and-forget — non-critical
  try {
    await db.prepare(
      'INSERT INTO flag_evaluations (id, flag_key, tenant_id, result) VALUES (?,?,?,?)'
    ).bind(newId(), flagKey, tenantId, result).run();
  } catch { /* non-critical */ }
}

export async function evaluateAllFlags(db: D1Database, tenantId: string): Promise<Record<string, string>> {
  const flags = await getFlags(db);
  const enabled = flags.filter(f => f.enabled === 1);
  const results: Record<string, string> = {};
  await Promise.all(enabled.map(async (f) => {
    results[f.key] = await evaluateFlag(db, f.key, tenantId);
  }));
  return results;
}

export async function setTenantOverride(db: D1Database, flagKey: string, tenantId: string, value: string): Promise<void> {
  const flag = await getFlag(db, flagKey);
  if (!flag) throw new Error('Flag not found');
  const overrides: Record<string, string> = JSON.parse(flag.tenant_overrides || '{}');
  overrides[tenantId] = value;
  await db.prepare("UPDATE feature_flags SET tenant_overrides = ?, updated_at = datetime('now') WHERE key = ?")
    .bind(JSON.stringify(overrides), flagKey).run();
}

export async function removeTenantOverride(db: D1Database, flagKey: string, tenantId: string): Promise<void> {
  const flag = await getFlag(db, flagKey);
  if (!flag) throw new Error('Flag not found');
  const overrides: Record<string, string> = JSON.parse(flag.tenant_overrides || '{}');
  delete overrides[tenantId];
  await db.prepare("UPDATE feature_flags SET tenant_overrides = ?, updated_at = datetime('now') WHERE key = ?")
    .bind(JSON.stringify(overrides), flagKey).run();
}

export async function getFlagStats(db: D1Database, flagKey: string): Promise<{
  total: number; unique_tenants: number; results: Record<string, number>;
}> {
  const rows = await db.prepare(
    'SELECT result, COUNT(*) as cnt, COUNT(DISTINCT tenant_id) as uniq FROM flag_evaluations WHERE flag_key = ? GROUP BY result'
  ).bind(flagKey).all<{ result: string; cnt: number; uniq: number }>();

  const resultDist: Record<string, number> = {};
  let total = 0;
  let uniqueTenants = 0;

  for (const row of rows.results) {
    resultDist[row.result] = row.cnt;
    total += row.cnt;
    uniqueTenants = Math.max(uniqueTenants, row.uniq);
  }

  return { total, unique_tenants: uniqueTenants, results: resultDist };
}
