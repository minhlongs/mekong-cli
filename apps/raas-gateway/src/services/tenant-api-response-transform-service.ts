/**
 * Tenant API Response Transform Service — CRUD for per-tenant response transform rules + logs
 */

interface TransformRow {
  id: string;
  tenant_id: string;
  rule_name: string;
  match_pattern: string;
  transform_type: string;
  transform_config_json: string;
  priority: number;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface LogRow {
  id: string;
  tenant_id: string;
  transform_id: string;
  request_path: string | null;
  applied: number;
  execution_time_ms: number;
  created_at: string;
}

interface CreateTransformInput {
  rule_name: string;
  match_pattern: string;
  transform_type?: string;
  transform_config?: Record<string, unknown>;
  priority?: number;
}

function rowToTransform(row: TransformRow) {
  return {
    ...row,
    is_active: row.is_active === 1,
    transform_config: (() => {
      try { return JSON.parse(row.transform_config_json); } catch { return {}; }
    })(),
  };
}

/** List active transform rules for a tenant, ordered by priority desc */
async function listTransforms(db: any, tenantId: string) {
  try {
    const result = await db
      .prepare('SELECT * FROM api_response_transforms WHERE tenant_id = ? ORDER BY priority DESC, created_at ASC')
      .bind(tenantId)
      .all();
    const rows = (result.results ?? []) as TransformRow[];
    return { transforms: rows.map(rowToTransform), total: rows.length };
  } catch (err) {
    throw new Error(`listTransforms failed: ${err instanceof Error ? err.message : err}`);
  }
}

/** Create a new transform rule for a tenant */
async function createTransform(db: any, tenantId: string, input: CreateTransformInput) {
  const id = crypto.randomUUID();
  const configJson = JSON.stringify(input.transform_config ?? {});
  const transformType = input.transform_type ?? 'map';
  const priority = input.priority ?? 0;

  try {
    await db
      .prepare(
        `INSERT INTO api_response_transforms
          (id, tenant_id, rule_name, match_pattern, transform_type, transform_config_json, priority)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, input.rule_name, input.match_pattern, transformType, configJson, priority)
      .run();

    const row = await db
      .prepare('SELECT * FROM api_response_transforms WHERE id = ?')
      .bind(id)
      .first() as TransformRow | null;

    if (!row) throw new Error('Transform created but not found');
    return rowToTransform(row);
  } catch (err) {
    throw new Error(`createTransform failed: ${err instanceof Error ? err.message : err}`);
  }
}

/** Get transform execution logs for a tenant */
async function getLogs(db: any, tenantId: string, limit = 100) {
  try {
    const result = await db
      .prepare('SELECT * FROM api_response_transform_logs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?')
      .bind(tenantId, limit)
      .all();
    const rows = (result.results ?? []) as LogRow[];
    return { logs: rows, total: rows.length };
  } catch (err) {
    throw new Error(`getLogs failed: ${err instanceof Error ? err.message : err}`);
  }
}

/** Admin overview — counts across all tenants */
async function getAdminOverview(db: any) {
  try {
    const transformsResult = await db
      .prepare('SELECT COUNT(*) as total, SUM(is_active) as active FROM api_response_transforms')
      .first() as { total: number; active: number } | null;

    const logsResult = await db
      .prepare('SELECT COUNT(*) as total FROM api_response_transform_logs')
      .first() as { total: number } | null;

    return {
      transforms: { total: transformsResult?.total ?? 0, active: transformsResult?.active ?? 0 },
      logs: { total: logsResult?.total ?? 0 },
    };
  } catch (err) {
    throw new Error(`getAdminOverview failed: ${err instanceof Error ? err.message : err}`);
  }
}

export const tenantApiResponseTransformService = { listTransforms, createTransform, getLogs, getAdminOverview };
