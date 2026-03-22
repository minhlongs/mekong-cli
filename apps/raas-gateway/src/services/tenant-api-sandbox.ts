// Tenant API Sandbox Service — isolated sandbox environments for testing APIs

/** Generate a random ID */
function newId(): string {
  return crypto.randomUUID();
}

/** ISO timestamp */
function now(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// listSandboxes
// ---------------------------------------------------------------------------

/** List all sandbox environments for a tenant */
async function listSandboxes(
  db: any,
  tenantId: string,
): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM api_sandbox_environments WHERE tenant_id = ? ORDER BY created_at DESC',
      )
      .bind(tenantId)
      .all();
    return { success: true, data: result.results ?? [] };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

// ---------------------------------------------------------------------------
// createSandbox
// ---------------------------------------------------------------------------

/** Create a new sandbox environment for a tenant */
async function createSandbox(
  db: any,
  tenantId: string,
  data: {
    sandbox_name: string;
    base_url?: string;
    config_json?: string;
  },
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const id = newId();
    const ts = now();
    const row = await db
      .prepare(
        `INSERT INTO api_sandbox_environments
           (id, tenant_id, sandbox_name, base_url, config_json, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 'active', ?, ?) RETURNING *`,
      )
      .bind(id, tenantId, data.sandbox_name, data.base_url ?? null, data.config_json ?? null, ts, ts)
      .first();
    return { success: true, data: row };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

// ---------------------------------------------------------------------------
// getRequests
// ---------------------------------------------------------------------------

/** List sandbox requests logged for a tenant */
async function getRequests(
  db: any,
  tenantId: string,
): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM api_sandbox_requests WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100',
      )
      .bind(tenantId)
      .all();
    return { success: true, data: result.results ?? [] };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

// ---------------------------------------------------------------------------
// getAdminOverview
// ---------------------------------------------------------------------------

/** Admin overview: total sandbox count + 10 most recent environments */
async function getAdminOverview(
  db: any,
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const countRow = await db
      .prepare('SELECT COUNT(*) as total FROM api_sandbox_environments')
      .first();
    const recent = await db
      .prepare(
        'SELECT * FROM api_sandbox_environments ORDER BY created_at DESC LIMIT 10',
      )
      .all();
    return {
      success: true,
      data: {
        total: countRow?.total ?? 0,
        recent: recent.results ?? [],
      },
    };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export const tenantApiSandboxService = {
  listSandboxes,
  createSandbox,
  getRequests,
  getAdminOverview,
};
