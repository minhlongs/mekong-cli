/**
 * Tenant Webhook Templates Service
 * CRUD for reusable webhook templates + usage tracking, and admin overview
 */

export interface WebhookTemplate {
  id: string; tenant_id: string; template_name: string; event_type: string;
  url_pattern: string; headers_json: string; payload_template: string | null;
  is_active: number; created_at: string; updated_at: string;
}
export interface WebhookTemplateUsage {
  id: string; tenant_id: string; template_id: string; webhook_id: string; applied_at: string;
}
export interface CreateTemplateData {
  template_name: string; event_type: string; url_pattern: string;
  headers_json?: string; payload_template?: string; is_active?: number;
}

/** List all active webhook templates for a tenant */
async function listTemplates(db: any, tenantId: string): Promise<WebhookTemplate[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM webhook_templates WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return result.results as WebhookTemplate[];
  } catch (err) {
    throw new Error(`listTemplates failed: ${String(err)}`);
  }
}

/** Create a new webhook template for a tenant */
async function createTemplate(
  db: any,
  tenantId: string,
  data: CreateTemplateData
): Promise<WebhookTemplate> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const headersJson = data.headers_json ?? '{}';
    const isActive = data.is_active ?? 1;

    const sql = `INSERT INTO webhook_templates
      (id, tenant_id, template_name, event_type, url_pattern, headers_json, payload_template, is_active, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
    await db.prepare(sql)
      .bind(id, tenantId, data.template_name, data.event_type, data.url_pattern,
        headersJson, data.payload_template ?? null, isActive, now, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM webhook_templates WHERE id = ?')
      .bind(id)
      .first();
    return row as WebhookTemplate;
  } catch (err) {
    throw new Error(`createTemplate failed: ${String(err)}`);
  }
}

/** List template usage logs for a tenant */
async function getUsage(db: any, tenantId: string): Promise<WebhookTemplateUsage[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM webhook_template_usage WHERE tenant_id = ? ORDER BY applied_at DESC')
      .bind(tenantId)
      .all();
    return result.results as WebhookTemplateUsage[];
  } catch (err) {
    throw new Error(`getUsage failed: ${String(err)}`);
  }
}

/** Admin: platform-wide overview of webhook templates */
async function getAdminOverview(db: any): Promise<Record<string, unknown>> {
  try {
    const [totalRow, activeRow, usageRow, byEventRows] = await Promise.all([
      db.prepare('SELECT COUNT(*) AS total FROM webhook_templates').first(),
      db.prepare('SELECT COUNT(*) AS total FROM webhook_templates WHERE is_active = 1').first(),
      db.prepare('SELECT COUNT(*) AS total FROM webhook_template_usage').first(),
      db.prepare('SELECT event_type, COUNT(*) AS count FROM webhook_templates GROUP BY event_type').all(),
    ]);

    const by_event_type: Record<string, number> = {};
    for (const row of byEventRows.results as { event_type: string; count: number }[]) {
      by_event_type[row.event_type] = row.count;
    }

    return {
      total_templates: (totalRow as { total: number } | null)?.total ?? 0,
      active_templates: (activeRow as { total: number } | null)?.total ?? 0,
      total_usage: (usageRow as { total: number } | null)?.total ?? 0,
      by_event_type,
    };
  } catch (err) {
    throw new Error(`getAdminOverview failed: ${String(err)}`);
  }
}

export const tenantWebhookTemplatesService = {
  listTemplates,
  createTemplate,
  getUsage,
  getAdminOverview,
};
