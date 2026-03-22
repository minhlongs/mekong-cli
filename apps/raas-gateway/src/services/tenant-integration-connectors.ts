/**
 * Tenant Integration Connectors Service
 * CRUD for per-tenant connector configs and event log retrieval
 */

// ── helpers ──────────────────────────────────────────────────────────────────

function ok(data: unknown): { success: true; data: unknown } {
  return { success: true, data };
}

function fail(error: unknown): { success: false; error: string } {
  return { success: false, error: error instanceof Error ? error.message : String(error) };
}

function newId(): string {
  return crypto.randomUUID();
}

// ── types ─────────────────────────────────────────────────────────────────────

interface Connector {
  id: string;
  tenant_id: string;
  connector_name: string;
  connector_type: string;
  config_json: string | null;
  status: string;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
}

interface ConnectorLog {
  id: string;
  tenant_id: string;
  connector_id: string;
  event_type: string;
  details: string | null;
  created_at: string;
}

interface CreateConnectorInput {
  connector_name: string;
  connector_type: string;
  config_json?: string;
  status?: string;
}

// ── service methods ───────────────────────────────────────────────────────────

async function listConnectors(db: any, tenantId: string) {
  try {
    const rows = await db
      .prepare('SELECT * FROM integration_connectors WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return ok(rows.results as Connector[]);
  } catch (err) {
    return fail(err);
  }
}

async function createConnector(db: any, tenantId: string, input: CreateConnectorInput) {
  try {
    const id = newId();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO integration_connectors
          (id, tenant_id, connector_name, connector_type, config_json, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        input.connector_name,
        input.connector_type,
        input.config_json ?? null,
        input.status ?? 'active',
        now,
        now
      )
      .run();
    const row = await db
      .prepare('SELECT * FROM integration_connectors WHERE id = ?')
      .bind(id)
      .first();
    return ok(row as Connector);
  } catch (err) {
    return fail(err);
  }
}

async function getLogs(db: any, tenantId: string, limit = 50) {
  try {
    const rows = await db
      .prepare(
        'SELECT * FROM integration_connector_logs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
      )
      .bind(tenantId, limit)
      .all();
    return ok(rows.results as ConnectorLog[]);
  } catch (err) {
    return fail(err);
  }
}

async function getAdminOverview(db: any) {
  try {
    const totalConnectors: { count: number } | null = await db
      .prepare('SELECT COUNT(*) as count FROM integration_connectors')
      .first();
    const activeConnectors: { count: number } | null = await db
      .prepare("SELECT COUNT(*) as count FROM integration_connectors WHERE status = 'active'")
      .first();
    const totalLogs: { count: number } | null = await db
      .prepare('SELECT COUNT(*) as count FROM integration_connector_logs')
      .first();
    const byType = await db
      .prepare(
        'SELECT connector_type, COUNT(*) as count FROM integration_connectors GROUP BY connector_type'
      )
      .all();
    return ok({
      totalConnectors: totalConnectors?.count ?? 0,
      activeConnectors: activeConnectors?.count ?? 0,
      totalLogs: totalLogs?.count ?? 0,
      byType: byType.results,
    });
  } catch (err) {
    return fail(err);
  }
}

// ── exports ───────────────────────────────────────────────────────────────────

export const tenantIntegrationConnectorsService = {
  listConnectors,
  createConnector,
  getLogs,
  getAdminOverview,
};
