/**
 * Mission Template Library Service
 * CRUD + versioning + instantiation for reusable mission config templates
 */

import type { D1Database } from '@cloudflare/workers-types';

interface Template {
  id: string;
  tenant_id: string | null;
  name: string;
  description: string | null;
  category: string;
  config_json: string;
  parameters_json: string;
  version: number;
  is_public: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface ListFilters {
  category?: string;
  is_public?: boolean;
  limit?: number;
  offset?: number;
}

interface CreateData {
  name: string;
  description?: string;
  category?: string;
  config_json?: string;
  parameters_json?: string;
  is_public?: boolean;
}

interface UpdateData {
  name?: string;
  description?: string;
  category?: string;
  config_json?: string;
  parameters_json?: string;
  is_public?: boolean;
  changelog?: string;
}

export const missionTemplateLibraryService = {

  async listTemplates(db: D1Database, tenantId: string, filters: ListFilters = {}) {
    const { category, is_public, limit = 20, offset = 0 } = filters;
    const cap = Math.min(limit, 100);

    const conditions: string[] = ['(tenant_id = ? OR is_public = 1)'];
    const binds: unknown[] = [tenantId];

    if (category) { conditions.push('category = ?'); binds.push(category); }
    if (is_public !== undefined) { conditions.push('is_public = ?'); binds.push(is_public ? 1 : 0); }

    const where = conditions.join(' AND ');
    const [rows, cnt] = await Promise.all([
      db.prepare(`SELECT * FROM mission_templates WHERE ${where} ORDER BY usage_count DESC, created_at DESC LIMIT ? OFFSET ?`)
        .bind(...binds, cap, offset).all<Template>(),
      db.prepare(`SELECT COUNT(*) as total FROM mission_templates WHERE ${where}`)
        .bind(...binds).first<{ total: number }>(),
    ]);
    return { templates: rows.results, total: cnt?.total ?? 0, pagination: { limit: cap, offset } };
  },

  async getTemplate(db: D1Database, tenantId: string, id: string) {
    return db.prepare(
      'SELECT * FROM mission_templates WHERE id = ? AND (tenant_id = ? OR is_public = 1)'
    ).bind(id, tenantId).first<Template>();
  },

  async createTemplate(db: D1Database, tenantId: string, data: CreateData) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db.prepare(
      `INSERT INTO mission_templates (id, tenant_id, name, description, category, config_json, parameters_json, is_public, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      id, tenantId, data.name, data.description ?? null,
      data.category ?? 'general', data.config_json ?? '{}',
      data.parameters_json ?? '[]', data.is_public ? 1 : 0, now, now
    ).run();
    return { id };
  },

  async updateTemplate(db: D1Database, tenantId: string, id: string, data: UpdateData) {
    const tpl = await db.prepare(
      'SELECT * FROM mission_templates WHERE id = ? AND tenant_id = ?'
    ).bind(id, tenantId).first<Template>();
    if (!tpl) return null;

    const newVersion = tpl.version + 1;
    const now = new Date().toISOString();

    // Archive current version before update
    await db.prepare(
      `INSERT INTO template_versions (id, template_id, version, config_json, changelog, created_by, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(crypto.randomUUID(), id, tpl.version, tpl.config_json, data.changelog ?? null, tenantId, now).run();

    const fields: string[] = ['version = ?', 'updated_at = ?'];
    const vals: unknown[] = [newVersion, now];

    if (data.name !== undefined) { fields.push('name = ?'); vals.push(data.name); }
    if (data.description !== undefined) { fields.push('description = ?'); vals.push(data.description); }
    if (data.category !== undefined) { fields.push('category = ?'); vals.push(data.category); }
    if (data.config_json !== undefined) { fields.push('config_json = ?'); vals.push(data.config_json); }
    if (data.parameters_json !== undefined) { fields.push('parameters_json = ?'); vals.push(data.parameters_json); }
    if (data.is_public !== undefined) { fields.push('is_public = ?'); vals.push(data.is_public ? 1 : 0); }

    await db.prepare(`UPDATE mission_templates SET ${fields.join(', ')} WHERE id = ?`)
      .bind(...vals, id).run();
    return { id, version: newVersion };
  },

  async deleteTemplate(db: D1Database, tenantId: string, id: string) {
    const result = await db.prepare(
      'DELETE FROM mission_templates WHERE id = ? AND tenant_id = ?'
    ).bind(id, tenantId).run();
    return (result.meta?.changes ?? 0) > 0;
  },

  async listCategories(db: D1Database) {
    const rows = await db.prepare(
      'SELECT * FROM template_categories ORDER BY sort_order ASC'
    ).all();
    return rows.results;
  },

  async createFromTemplate(db: D1Database, tenantId: string, templateId: string, overrides: Partial<CreateData> = {}) {
    const tpl = await db.prepare(
      'SELECT * FROM mission_templates WHERE id = ? AND (tenant_id = ? OR is_public = 1)'
    ).bind(templateId, tenantId).first<Template>();
    if (!tpl) return null;

    // Bump usage count
    await db.prepare('UPDATE mission_templates SET usage_count = usage_count + 1 WHERE id = ?')
      .bind(templateId).run();

    return this.createTemplate(db, tenantId, {
      name: overrides.name ?? `Copy of ${tpl.name}`,
      description: overrides.description ?? tpl.description ?? undefined,
      category: overrides.category ?? tpl.category,
      config_json: overrides.config_json ?? tpl.config_json,
      parameters_json: overrides.parameters_json ?? tpl.parameters_json,
      is_public: overrides.is_public ?? false,
    });
  },

  async listVersions(db: D1Database, templateId: string) {
    const rows = await db.prepare(
      'SELECT * FROM template_versions WHERE template_id = ? ORDER BY version DESC'
    ).bind(templateId).all();
    return rows.results;
  },

  async getAdminOverview(db: D1Database) {
    const [totals, popular, cats] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as total, SUM(is_public) as public_count, SUM(usage_count) as total_usage FROM mission_templates`).first(),
      db.prepare(`SELECT id, name, category, usage_count FROM mission_templates ORDER BY usage_count DESC LIMIT 5`).all(),
      db.prepare(`SELECT category, COUNT(*) as count FROM mission_templates GROUP BY category ORDER BY count DESC`).all(),
    ]);
    return { totals, popular: popular.results, by_category: cats.results };
  },
};
