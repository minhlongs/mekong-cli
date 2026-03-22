/**
 * Tenant Event Replay Service — list/create replay configs, query runs, admin overview
 *
 * All DB calls use .all() + cast or .first() + cast (D1 pattern, no generics on prepare).
 * Every export is a plain async function; caller passes db: any.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ReplayConfig {
  id: string;
  tenant_id: string;
  source_event_type: string;
  target_endpoint: string;
  filter_json: string;
  replay_speed: number;
  status: string;
  created_at: string;
  updated_at: string;
}

interface ReplayRun {
  id: string;
  tenant_id: string;
  config_id: string;
  events_replayed: number;
  events_failed: number;
  status: string;
  started_at: string;
  completed_at: string | null;
}

interface AdminOverviewRow {
  tenant_id: string;
  total_configs: number;
  total_runs: number;
  events_replayed: number;
  events_failed: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function nowIso(): string {
  return new Date().toISOString();
}

function uuid(): string {
  // crypto.randomUUID() is available in Cloudflare Workers runtime
  return crypto.randomUUID();
}

// ---------------------------------------------------------------------------
// Exported service object
// ---------------------------------------------------------------------------

export const tenantEventReplayService = {

  /** List all replay configs for a tenant */
  async listConfigs(db: any, tenantId: string): Promise<ReplayConfig[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM event_replay_configs WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return (result.results ?? []) as ReplayConfig[];
    } catch (err) {
      throw new Error(`listConfigs failed: ${(err as Error).message}`);
    }
  },

  /** Create a new replay config for a tenant */
  async createConfig(
    db: any,
    tenantId: string,
    data: {
      source_event_type: string;
      target_endpoint: string;
      filter_json?: string;
      replay_speed?: number;
    }
  ): Promise<ReplayConfig> {
    const id = uuid();
    const now = nowIso();
    const filterJson = data.filter_json ?? '{}';
    const replaySpeed = data.replay_speed ?? 1.0;
    try {
      await db
        .prepare(
          `INSERT INTO event_replay_configs
           (id, tenant_id, source_event_type, target_endpoint, filter_json, replay_speed, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)`
        )
        .bind(id, tenantId, data.source_event_type, data.target_endpoint, filterJson, replaySpeed, now, now)
        .run();
      return { id, tenant_id: tenantId, source_event_type: data.source_event_type, target_endpoint: data.target_endpoint, filter_json: filterJson, replay_speed: replaySpeed, status: 'active', created_at: now, updated_at: now };
    } catch (err) {
      throw new Error(`createConfig failed: ${(err as Error).message}`);
    }
  },

  /** List replay runs for a tenant, optionally filtered by config_id */
  async getRuns(db: any, tenantId: string, configId?: string): Promise<ReplayRun[]> {
    try {
      const sql = configId
        ? 'SELECT * FROM event_replay_runs WHERE tenant_id = ? AND config_id = ? ORDER BY started_at DESC'
        : 'SELECT * FROM event_replay_runs WHERE tenant_id = ? ORDER BY started_at DESC';
      const stmt = configId
        ? db.prepare(sql).bind(tenantId, configId)
        : db.prepare(sql).bind(tenantId);
      const result = await stmt.all();
      return (result.results ?? []) as ReplayRun[];
    } catch (err) {
      throw new Error(`getRuns failed: ${(err as Error).message}`);
    }
  },

  /** Admin overview — aggregate replay stats per tenant */
  async getAdminOverview(db: any): Promise<AdminOverviewRow[]> {
    try {
      const result = await db
        .prepare(
          `SELECT
             c.tenant_id,
             COUNT(DISTINCT c.id)       AS total_configs,
             COUNT(DISTINCT r.id)       AS total_runs,
             COALESCE(SUM(r.events_replayed), 0) AS events_replayed,
             COALESCE(SUM(r.events_failed), 0)   AS events_failed
           FROM event_replay_configs c
           LEFT JOIN event_replay_runs r ON r.config_id = c.id
           GROUP BY c.tenant_id
           ORDER BY total_runs DESC`
        )
        .all();
      return (result.results ?? []) as AdminOverviewRow[];
    } catch (err) {
      throw new Error(`getAdminOverview failed: ${(err as Error).message}`);
    }
  },
};
