/**
 * Tenant export service - data export/import/delete for GDPR
 */

export interface TenantExport {
  tenant: any;
  missions: any[];
  credits: any[];
  apiKeys: any[];
  projects: any[];
  exportedAt: string;
  version: string;
}

export interface ImportResult {
  tenantId: string;
  imported: Record<string, number>;
}

export interface DeleteResult {
  deleted: Record<string, number>;
}

export class TenantExportService {
  async exportTenantData(db: D1Database, tenantId: string): Promise<TenantExport> {
    const [tenant, missions, credits, apiKeys, projects] = await Promise.all([
      db.prepare('SELECT * FROM tenants WHERE id = ?').bind(tenantId).first(),
      db.prepare('SELECT * FROM missions WHERE tenant_id = ? LIMIT 10000').bind(tenantId).all(),
      db.prepare('SELECT * FROM credit_transactions WHERE tenant_id = ? LIMIT 10000').bind(tenantId).all(),
      db.prepare('SELECT id, name, scope, created_at FROM api_keys WHERE tenant_id = ?').bind(tenantId).all(),
      db.prepare('SELECT * FROM projects WHERE tenant_id = ?').bind(tenantId).all(),
    ]);
    return { tenant, missions: missions.results, credits: credits.results, apiKeys: apiKeys.results, projects: projects.results, exportedAt: new Date().toISOString(), version: '1.0' };
  }

  async deleteTenantData(db: D1Database, tenantId: string): Promise<DeleteResult> {
    const tables = ['missions', 'credit_transactions', 'api_keys', 'projects', 'team_members', 'webhooks'];
    const deleted: Record<string, number> = {};
    for (const t of tables) {
      const r = await db.prepare('DELETE FROM ' + t + ' WHERE tenant_id = ?').bind(tenantId).run();
      deleted[t] = r.meta?.changes ?? 0;
    }
    await db.prepare('DELETE FROM tenants WHERE id = ?').bind(tenantId).run();
    deleted['tenants'] = 1;
    return { deleted };
  }
}
