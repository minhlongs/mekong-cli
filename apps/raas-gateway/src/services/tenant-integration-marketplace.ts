/**
 * Tenant Integration Marketplace Service
 * CRUD for tenant integrations + logs, and admin overview
 */

export interface Integration {
  id: string;
  tenant_id: string;
  integration_type: string;
  provider_name: string;
  config_json: string;
  status: string;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationLog {
  id: string;
  tenant_id: string;
  integration_id: string;
  action: string;
  status: string;
  details: string | null;
  created_at: string;
}

export interface CreateIntegrationData {
  integration_type: string;
  provider_name: string;
  config_json?: string;
  status?: string;
}

/** List all integrations for a tenant */
export async function listIntegrations(db: any, tenantId: string): Promise<Integration[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM integrations WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return result.results as Integration[];
  } catch (err) {
    throw new Error(`listIntegrations failed: ${String(err)}`);
  }
}

/** Create a new integration for a tenant */
export async function createIntegration(
  db: any,
  tenantId: string,
  data: CreateIntegrationData
): Promise<Integration> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const configJson = data.config_json ?? '{}';
    const status = data.status ?? 'active';

    await db
      .prepare(
        `INSERT INTO integrations (id, tenant_id, integration_type, provider_name, config_json, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, data.integration_type, data.provider_name, configJson, status, now, now)
      .run();

    const created = (await db
      .prepare('SELECT * FROM integrations WHERE id = ?')
      .bind(id)
      .first()) as Integration | null;

    if (!created) throw new Error('Failed to retrieve created integration');
    return created;
  } catch (err) {
    throw new Error(`createIntegration failed: ${String(err)}`);
  }
}

/** List all integration logs for a tenant */
export async function getLogs(db: any, tenantId: string): Promise<IntegrationLog[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM integration_logs WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return result.results as IntegrationLog[];
  } catch (err) {
    throw new Error(`getLogs failed: ${String(err)}`);
  }
}

/** Admin: overview of all integrations grouped by status and provider */
export async function getAdminOverview(db: any): Promise<{
  total: number;
  by_status: Record<string, number>;
  by_provider: Record<string, number>;
  recent: Integration[];
}> {
  try {
    const [countRow, statusRows, providerRows, recentResult] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total FROM integrations').first(),
      db
        .prepare('SELECT status, COUNT(*) as count FROM integrations GROUP BY status')
        .all(),
      db
        .prepare('SELECT provider_name, COUNT(*) as count FROM integrations GROUP BY provider_name')
        .all(),
      db
        .prepare('SELECT * FROM integrations ORDER BY created_at DESC LIMIT 10')
        .all(),
    ]);

    const by_status: Record<string, number> = {};
    for (const row of statusRows.results as { status: string; count: number }[]) {
      by_status[row.status] = row.count;
    }

    const by_provider: Record<string, number> = {};
    for (const row of providerRows.results as { provider_name: string; count: number }[]) {
      by_provider[row.provider_name] = row.count;
    }

    return {
      total: (countRow as { total: number } | null)?.total ?? 0,
      by_status,
      by_provider,
      recent: recentResult.results as Integration[],
    };
  } catch (err) {
    throw new Error(`getAdminOverview failed: ${String(err)}`);
  }
}

export const tenantIntegrationMarketplaceService = {
  listIntegrations,
  createIntegration,
  getLogs,
  getAdminOverview,
};
