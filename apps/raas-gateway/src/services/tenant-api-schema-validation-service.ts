/**
 * Tenant API Schema Validation Service
 * Manages per-tenant endpoint schema rules and violation records
 */

// Plain DB row shapes used for casts after .all()
interface SchemaRuleRow {
  id: string;
  tenant_id: string;
  endpoint_pattern: string;
  schema_json: string;
  validation_mode: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

interface ViolationRow {
  id: string;
  tenant_id: string;
  rule_id: string;
  request_path: string;
  violation_details: string;
  severity: string;
  created_at: string;
}

export interface CreateRuleInput {
  id: string;
  tenant_id: string;
  endpoint_pattern: string;
  schema_json: string;
  validation_mode?: string;
}

export interface AdminOverviewRow {
  tenant_id: string;
  rule_count: number;
  violation_count: number;
}

// Named export object — no class, no generic type args on db
export const tenantApiSchemaValidationService = {
  /**
   * List all active schema rules for a tenant
   */
  async listRules(db: any, tenantId: string): Promise<SchemaRuleRow[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM api_schema_rules WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return (result.results ?? []) as SchemaRuleRow[];
    } catch (err) {
      console.error('[schemaValidationSvc] listRules error:', err);
      throw err;
    }
  },

  /**
   * Create a new schema rule for a tenant
   */
  async createRule(db: any, input: CreateRuleInput): Promise<SchemaRuleRow> {
    try {
      const now = new Date().toISOString();
      const mode = input.validation_mode ?? 'warn';
      await db
        .prepare(
          `INSERT INTO api_schema_rules
             (id, tenant_id, endpoint_pattern, schema_json, validation_mode, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 1, ?, ?)`
        )
        .bind(input.id, input.tenant_id, input.endpoint_pattern, input.schema_json, mode, now, now)
        .run();
      const row = await db
        .prepare('SELECT * FROM api_schema_rules WHERE id = ?')
        .bind(input.id)
        .first();
      return row as SchemaRuleRow;
    } catch (err) {
      console.error('[schemaValidationSvc] createRule error:', err);
      throw err;
    }
  },

  /**
   * Get violations for a tenant, newest first, capped at 200
   */
  async getViolations(db: any, tenantId: string, limit = 50): Promise<ViolationRow[]> {
    try {
      const safeLimit = Math.min(Math.max(1, limit), 200);
      const result = await db
        .prepare(
          'SELECT * FROM api_schema_violations WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?'
        )
        .bind(tenantId, safeLimit)
        .all();
      return (result.results ?? []) as ViolationRow[];
    } catch (err) {
      console.error('[schemaValidationSvc] getViolations error:', err);
      throw err;
    }
  },

  /**
   * Admin overview: rule + violation counts per tenant
   */
  async getAdminOverview(db: any): Promise<AdminOverviewRow[]> {
    try {
      const result = await db
        .prepare(
          `SELECT r.tenant_id,
                  COUNT(DISTINCT r.id)  AS rule_count,
                  COUNT(DISTINCT v.id)  AS violation_count
           FROM api_schema_rules r
           LEFT JOIN api_schema_violations v ON v.tenant_id = r.tenant_id
           GROUP BY r.tenant_id
           ORDER BY violation_count DESC`
        )
        .all();
      return (result.results ?? []) as AdminOverviewRow[];
    } catch (err) {
      console.error('[schemaValidationSvc] getAdminOverview error:', err);
      throw err;
    }
  },
};
