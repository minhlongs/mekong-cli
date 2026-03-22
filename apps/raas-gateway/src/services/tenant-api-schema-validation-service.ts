/**
 * Tenant API Schema Validation Service
 * Manages per-tenant JSON schema definitions for request/response validation
 * and records schema violations for observability.
 */

/** A schema definition record stored in D1 */
export interface ApiSchemaDefinition {
  id: string;
  tenant_id: string;
  schema_name: string;
  endpoint_pattern: string;
  request_schema: string | null;
  response_schema: string | null;
  enabled: number;
  created_at: string;
  updated_at: string;
}

/** A schema violation record stored in D1 */
export interface ApiSchemaViolation {
  id: string;
  tenant_id: string;
  schema_id: string;
  violation_type: string;
  endpoint: string | null;
  details: string | null;
  created_at: string;
}

/** Input for creating a new schema definition */
export interface CreateSchemaInput {
  schema_name: string;
  endpoint_pattern: string;
  request_schema?: string;
  response_schema?: string;
  enabled?: boolean;
}

/** List all schema definitions for a tenant */
async function listSchemas(
  db: any,
  tenantId: string,
): Promise<{ success: boolean; data?: ApiSchemaDefinition[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, schema_name, endpoint_pattern,
                request_schema, response_schema, enabled, created_at, updated_at
         FROM api_schema_definitions
         WHERE tenant_id = ?
         ORDER BY created_at DESC`,
      )
      .bind(tenantId)
      .all();

    return { success: true, data: (result.results ?? []) as ApiSchemaDefinition[] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
  }
}

/** Create a new schema definition for a tenant */
async function createSchema(
  db: any,
  tenantId: string,
  input: CreateSchemaInput,
): Promise<{ success: boolean; data?: ApiSchemaDefinition; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const enabled = input.enabled === false ? 0 : 1;
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO api_schema_definitions
           (id, tenant_id, schema_name, endpoint_pattern, request_schema, response_schema, enabled, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      )
      .bind(
        id,
        tenantId,
        input.schema_name,
        input.endpoint_pattern,
        input.request_schema ?? null,
        input.response_schema ?? null,
        enabled,
        now,
        now,
      )
      .run();

    const row = await db
      .prepare(
        `SELECT id, tenant_id, schema_name, endpoint_pattern,
                request_schema, response_schema, enabled, created_at, updated_at
         FROM api_schema_definitions WHERE id = ?`,
      )
      .bind(id)
      .first();

    if (!row) throw new Error('Insert succeeded but row not found');

    return { success: true, data: row as ApiSchemaDefinition };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
  }
}

/** Get violations for a tenant, optionally filtered by schema_id */
async function getViolations(
  db: any,
  tenantId: string,
  schemaId?: string,
): Promise<{ success: boolean; data?: ApiSchemaViolation[]; error?: string }> {
  try {
    const query = schemaId
      ? `SELECT id, tenant_id, schema_id, violation_type, endpoint, details, created_at
         FROM api_schema_violations
         WHERE tenant_id = ? AND schema_id = ?
         ORDER BY created_at DESC LIMIT 200`
      : `SELECT id, tenant_id, schema_id, violation_type, endpoint, details, created_at
         FROM api_schema_violations
         WHERE tenant_id = ?
         ORDER BY created_at DESC LIMIT 200`;

    const stmt = schemaId
      ? db.prepare(query).bind(tenantId, schemaId)
      : db.prepare(query).bind(tenantId);

    const result = await stmt.all();
    return { success: true, data: (result.results ?? []) as ApiSchemaViolation[] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
  }
}

/** Admin overview — aggregate counts across all tenants */
async function getAdminOverview(db: any): Promise<{
  success: boolean;
  data?: {
    total_schemas: number;
    enabled_schemas: number;
    total_violations: number;
    tenants_with_schemas: number;
  };
  error?: string;
}> {
  try {
    const [schemas, violations, tenants] = await Promise.all([
      db
        .prepare(
          `SELECT COUNT(*) as total, SUM(enabled) as enabled_count FROM api_schema_definitions`,
        )
        .first(),
      db
        .prepare(`SELECT COUNT(*) as total FROM api_schema_violations`)
        .first(),
      db
        .prepare(
          `SELECT COUNT(DISTINCT tenant_id) as count FROM api_schema_definitions`,
        )
        .first(),
    ]);

    return {
      success: true,
      data: {
        total_schemas: schemas?.total ?? 0,
        enabled_schemas: schemas?.enabled_count ?? 0,
        total_violations: violations?.total ?? 0,
        tenants_with_schemas: tenants?.count ?? 0,
      },
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
  }
}

export const tenantApiSchemaValidationService = {
  listSchemas,
  createSchema,
  getViolations,
  getAdminOverview,
};
