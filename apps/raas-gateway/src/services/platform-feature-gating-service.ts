/**
 * Platform Feature Gating Service — tier-based feature access + per-tenant overrides
 * Tables: feature_gates, feature_gate_overrides
 */

export interface FeatureGate {
  id: string; feature_key: string; display_name: string; description: string | null;
  allowed_tiers: string; is_enabled: number; created_at: string; updated_at: string;
}

export interface FeatureGateOverride {
  id: string; gate_id: string; tenant_id: string;
  is_enabled: number; reason: string | null; created_at: string;
}

/** List all feature gates */
async function listGates(db: any): Promise<FeatureGate[]> {
  try {
    const result = await db.prepare('SELECT * FROM feature_gates ORDER BY feature_key ASC').all();
    return (result.results ?? []) as FeatureGate[];
  } catch (err) {
    throw new Error(`listGates failed: ${err instanceof Error ? err.message : 'DB error'}`);
  }
}

/** Create a new feature gate */
async function createGate(
  db: any,
  data: { feature_key: string; display_name: string; description?: string; allowed_tiers?: string }
): Promise<FeatureGate> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const allowed_tiers = data.allowed_tiers ?? 'pro,enterprise';
  try {
    await db
      .prepare(
        `INSERT INTO feature_gates (id, feature_key, display_name, description, allowed_tiers, is_enabled, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 1, ?, ?)`
      )
      .bind(id, data.feature_key, data.display_name, data.description ?? null, allowed_tiers, now, now)
      .run();
    return { id, feature_key: data.feature_key, display_name: data.display_name,
      description: data.description ?? null, allowed_tiers, is_enabled: 1, created_at: now, updated_at: now };
  } catch (err) {
    throw new Error(`createGate failed: ${err instanceof Error ? err.message : 'DB error'}`);
  }
}

/** Get overrides filtered by gate_id and/or tenant_id */
async function getOverrides(
  db: any,
  filter: { gate_id?: string; tenant_id?: string }
): Promise<FeatureGateOverride[]> {
  try {
    let q = 'SELECT * FROM feature_gate_overrides WHERE 1=1';
    const b: string[] = [];
    if (filter.gate_id)   { q += ' AND gate_id = ?';   b.push(filter.gate_id); }
    if (filter.tenant_id) { q += ' AND tenant_id = ?'; b.push(filter.tenant_id); }
    q += ' ORDER BY created_at DESC';
    const result = await db.prepare(q).bind(...b).all();
    return (result.results ?? []) as FeatureGateOverride[];
  } catch (err) {
    throw new Error(`getOverrides failed: ${err instanceof Error ? err.message : 'DB error'}`);
  }
}

/** Dashboard: gate counts + override count */
async function getDashboard(db: any): Promise<{
  total_gates: number; enabled_gates: number; total_overrides: number; gates: FeatureGate[];
}> {
  try {
    const [gatesResult, overrideCount] = await Promise.all([
      db.prepare('SELECT * FROM feature_gates ORDER BY feature_key ASC').all(),
      db.prepare('SELECT COUNT(*) as cnt FROM feature_gate_overrides').first() as Promise<{ cnt: number }>,
    ]);
    const gates = (gatesResult.results ?? []) as FeatureGate[];
    return { total_gates: gates.length, enabled_gates: gates.filter((g) => g.is_enabled === 1).length,
      total_overrides: overrideCount?.cnt ?? 0, gates };
  } catch (err) {
    throw new Error(`getDashboard failed: ${err instanceof Error ? err.message : 'DB error'}`);
  }
}

export const platformFeatureGatingService = { listGates, createGate, getOverrides, getDashboard };
