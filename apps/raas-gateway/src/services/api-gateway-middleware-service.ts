// API Gateway Middleware Service — CRUD + ordering + logs + chain preview for per-tenant middleware configs

/** List all middleware configs for a tenant, ordered by priority */
export async function listConfigs(db: any, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM middleware_configs WHERE tenant_id = ? ORDER BY priority ASC, created_at ASC`
  ).bind(tenantId).all();
  return rows.results;
}

/** Create a new middleware config for a tenant */
export async function createConfig(
  db: any,
  tenantId: string,
  data: {
    name: string;
    middleware_type: string;
    config_json?: Record<string, unknown>;
    description?: string;
    priority?: number;
    is_active?: boolean;
    endpoint_pattern?: string;
  }
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO middleware_configs
       (tenant_id, name, description, middleware_type, config_json, priority, is_active, endpoint_pattern)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    tenantId,
    data.name,
    data.description ?? null,
    data.middleware_type,
    JSON.stringify(data.config_json ?? {}),
    data.priority ?? 100,
    data.is_active !== false ? 1 : 0,
    data.endpoint_pattern ?? '*'
  ).first();
}

/** Update an existing middleware config (tenant-scoped) */
export async function updateConfig(
  db: any,
  tenantId: string,
  configId: string,
  data: {
    name?: string;
    description?: string;
    middleware_type?: string;
    config_json?: Record<string, unknown>;
    priority?: number;
    is_active?: boolean;
    endpoint_pattern?: string;
  }
): Promise<unknown | null> {
  const sets: string[] = ["updated_at = datetime('now')"];
  const binds: unknown[] = [];

  if (data.name !== undefined) { sets.push('name = ?'); binds.push(data.name); }
  if (data.description !== undefined) { sets.push('description = ?'); binds.push(data.description); }
  if (data.middleware_type !== undefined) { sets.push('middleware_type = ?'); binds.push(data.middleware_type); }
  if (data.config_json !== undefined) { sets.push('config_json = ?'); binds.push(JSON.stringify(data.config_json)); }
  if (data.priority !== undefined) { sets.push('priority = ?'); binds.push(data.priority); }
  if (data.is_active !== undefined) { sets.push('is_active = ?'); binds.push(data.is_active ? 1 : 0); }
  if (data.endpoint_pattern !== undefined) { sets.push('endpoint_pattern = ?'); binds.push(data.endpoint_pattern); }

  binds.push(configId, tenantId);
  return db.prepare(
    `UPDATE middleware_configs SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ? RETURNING *`
  ).bind(...binds).first();
}

/** Delete a middleware config (tenant-scoped) */
export async function deleteConfig(db: any, tenantId: string, configId: string): Promise<boolean> {
  const result = await db.prepare(
    `DELETE FROM middleware_configs WHERE id = ? AND tenant_id = ?`
  ).bind(configId, tenantId).run();
  return result.meta?.changes > 0;
}

/** Reorder configs by reassigning sequential priority values */
export async function reorderConfigs(
  db: any,
  tenantId: string,
  orderedIds: string[]
): Promise<void> {
  const stmts = orderedIds.map((id, idx) =>
    db.prepare(
      `UPDATE middleware_configs SET priority = ?, updated_at = datetime('now') WHERE id = ? AND tenant_id = ?`
    ).bind((idx + 1) * 10, id, tenantId)
  );
  if (stmts.length > 0) await db.batch(stmts);
}

/** List all public middleware templates */
export async function listTemplates(db: any): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM middleware_templates ORDER BY middleware_type, name`
  ).all();
  return rows.results;
}

/** Get execution logs for a tenant (newest first, limit 100) */
export async function getExecutionLogs(db: any, tenantId: string, limit = 100): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT l.*, c.name as middleware_name, c.middleware_type
     FROM middleware_execution_logs l
     LEFT JOIN middleware_configs c ON c.id = l.middleware_id
     WHERE l.tenant_id = ?
     ORDER BY l.executed_at DESC LIMIT ?`
  ).bind(tenantId, Math.min(limit, 500)).all();
  return rows.results;
}

/** Preview the ordered middleware chain that would apply for a given endpoint pattern */
export async function getChainPreview(
  db: any,
  tenantId: string,
  endpointPattern: string
): Promise<unknown[]> {
  // Match configs whose endpoint_pattern is '*' or exactly matches the provided pattern
  const rows = await db.prepare(
    `SELECT * FROM middleware_configs
     WHERE tenant_id = ? AND is_active = 1
       AND (endpoint_pattern = '*' OR endpoint_pattern = ?)
     ORDER BY priority ASC`
  ).bind(tenantId, endpointPattern).all();
  return rows.results;
}

/** Admin overview: aggregate stats across all tenants */
export async function getAdminOverview(db: any): Promise<unknown> {
  const [totalConfigs, activeConfigs, totalLogs, errorLogs, topTypes] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM middleware_configs`).first() as Promise<{ count: number } | null>,
    db.prepare(`SELECT COUNT(*) as count FROM middleware_configs WHERE is_active = 1`).first() as Promise<{ count: number } | null>,
    db.prepare(`SELECT COUNT(*) as count FROM middleware_execution_logs`).first() as Promise<{ count: number } | null>,
    db.prepare(`SELECT COUNT(*) as count FROM middleware_execution_logs WHERE status = 'error'`).first() as Promise<{ count: number } | null>,
    db.prepare(
      `SELECT middleware_type, COUNT(*) as count FROM middleware_configs GROUP BY middleware_type ORDER BY count DESC`
    ).all(),
  ]);
  return {
    configs: { total: totalConfigs?.count ?? 0, active: activeConfigs?.count ?? 0 },
    logs: { total: totalLogs?.count ?? 0, errors: errorLogs?.count ?? 0 },
    byType: topTypes.results,
  };
}
