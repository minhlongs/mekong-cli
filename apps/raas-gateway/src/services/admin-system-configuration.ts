/**
 * Admin System Configuration Service
 * Platform-level key/value config store with history tracking
 * All functions: db: any, try/catch, { success, data/error }
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

interface ConfigRow {
  id: string;
  config_key: string;
  config_value: string;
  config_type: string;
  description: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

interface HistoryRow {
  id: string;
  config_id: string;
  old_value: string | null;
  new_value: string;
  changed_by: string | null;
  created_at: string;
}

interface CreateConfigInput {
  config_key: string;
  config_value: string;
  config_type?: string;
  description?: string;
  updated_by?: string;
}

/** List all system configurations ordered by key */
async function listConfigs(db: DB): Promise<{ success: boolean; data?: ConfigRow[]; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM system_configurations ORDER BY config_key ASC')
      .all();
    return { success: true, data: result.results ?? [] };
  } catch (err) {
    console.error('[adminSystemConfig] listConfigs error:', err);
    return { success: false, error: 'Failed to list configurations' };
  }
}

/** Create a new system configuration and record initial history entry */
async function createConfig(
  db: DB,
  input: CreateConfigInput
): Promise<{ success: boolean; data?: ConfigRow; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const configType = input.config_type ?? 'string';

    await db
      .prepare(
        `INSERT INTO system_configurations
           (id, config_key, config_value, config_type, description, updated_by, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        input.config_key,
        input.config_value,
        configType,
        input.description ?? null,
        input.updated_by ?? null,
        now,
        now
      )
      .run();

    // Record initial creation in history
    await db
      .prepare(
        `INSERT INTO system_configuration_history
           (id, config_id, old_value, new_value, changed_by, created_at)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .bind(crypto.randomUUID(), id, null, input.config_value, input.updated_by ?? null, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM system_configurations WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: row ?? undefined };
  } catch (err) {
    console.error('[adminSystemConfig] createConfig error:', err);
    return { success: false, error: 'Failed to create configuration' };
  }
}

/** Get change history for all configs or a specific config_id */
async function getHistory(
  db: DB,
  configId?: string,
  limit = 50
): Promise<{ success: boolean; data?: HistoryRow[]; error?: string }> {
  try {
    const safeLimit = Math.min(Math.max(1, limit), 200);
    let result;

    if (configId) {
      result = await db
        .prepare(
          `SELECT * FROM system_configuration_history
           WHERE config_id = ?
           ORDER BY created_at DESC
           LIMIT ?`
        )
        .bind(configId, safeLimit)
        .all();
    } else {
      result = await db
        .prepare(
          `SELECT * FROM system_configuration_history
           ORDER BY created_at DESC
           LIMIT ?`
        )
        .bind(safeLimit)
        .all();
    }

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    console.error('[adminSystemConfig] getHistory error:', err);
    return { success: false, error: 'Failed to fetch configuration history' };
  }
}

/** Dashboard: aggregate stats — total configs by type + recent 10 changes */
async function getDashboard(
  db: DB
): Promise<{ success: boolean; data?: Record<string, unknown>; error?: string }> {
  try {
    const [typeCounts, totalResult, recentHistory] = await Promise.all([
      db
        .prepare(
          `SELECT config_type, COUNT(*) as count
           FROM system_configurations
           GROUP BY config_type`
        )
        .all(),
      db
        .prepare('SELECT COUNT(*) as total FROM system_configurations')
        .first(),
      db
        .prepare(
          `SELECT h.*, c.config_key
           FROM system_configuration_history h
           LEFT JOIN system_configurations c ON c.id = h.config_id
           ORDER BY h.created_at DESC
           LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        total_configs: totalResult?.total ?? 0,
        by_type: typeCounts.results ?? [],
        recent_changes: recentHistory.results ?? [],
      },
    };
  } catch (err) {
    console.error('[adminSystemConfig] getDashboard error:', err);
    return { success: false, error: 'Failed to fetch dashboard' };
  }
}

export const adminSystemConfigurationService = {
  listConfigs,
  createConfig,
  getHistory,
  getDashboard,
};
