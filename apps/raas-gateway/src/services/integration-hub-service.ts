/**
 * Integration Hub Service — manages connector catalog and tenant integrations
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface CatalogItem {
  id: string;
  name: string;
  slug: string;
  category: string;
  description: string | null;
  icon_url: string | null;
  auth_type: string;
  config_schema: string;
  supported_events: string;
  is_active: number;
  created_at: string;
}

export interface TenantIntegration {
  id: string;
  tenant_id: string;
  catalog_id: string;
  config: string;
  credentials: string;
  status: string;
  last_sync_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationEvent {
  id: string;
  tenant_id: string;
  integration_id: string;
  event_type: string;
  direction: string;
  payload: string;
  status: string;
  error: string | null;
  created_at: string;
}

/** List available integrations from catalog */
export async function getCatalog(
  db: D1Database,
  filters: { category?: string } = {}
): Promise<CatalogItem[]> {
  let query = 'SELECT * FROM integration_catalog WHERE is_active = 1';
  const bindings: string[] = [];
  if (filters.category) {
    query += ' AND category = ?';
    bindings.push(filters.category);
  }
  query += ' ORDER BY name ASC';
  const result = await db.prepare(query).bind(...bindings).all<CatalogItem>();
  return result.results;
}

/** Get single catalog item by slug */
export async function getCatalogItem(db: D1Database, slug: string): Promise<CatalogItem | null> {
  return db.prepare('SELECT * FROM integration_catalog WHERE slug = ? AND is_active = 1')
    .bind(slug).first<CatalogItem>();
}

/** Install integration for tenant */
export async function installIntegration(
  db: D1Database,
  tenantId: string,
  data: { catalogId: string; config?: Record<string, unknown>; credentials?: Record<string, unknown> }
): Promise<TenantIntegration> {
  const id = crypto.randomUUID();
  const config = JSON.stringify(data.config ?? {});
  const credentials = JSON.stringify(data.credentials ?? {});
  await db.prepare(
    `INSERT INTO tenant_integrations (id, tenant_id, catalog_id, config, credentials, status, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, 'active', datetime('now'), datetime('now'))`
  ).bind(id, tenantId, data.catalogId, config, credentials).run();
  const row = await db.prepare('SELECT * FROM tenant_integrations WHERE id = ?')
    .bind(id).first<TenantIntegration>();
  return row!;
}

/** List tenant's installed integrations */
export async function getInstalledIntegrations(
  db: D1Database, tenantId: string
): Promise<TenantIntegration[]> {
  const result = await db.prepare(
    'SELECT * FROM tenant_integrations WHERE tenant_id = ? ORDER BY created_at DESC'
  ).bind(tenantId).all<TenantIntegration>();
  return result.results;
}

/** Get single installed integration */
export async function getIntegration(
  db: D1Database, tenantId: string, integrationId: string
): Promise<TenantIntegration | null> {
  return db.prepare(
    'SELECT * FROM tenant_integrations WHERE id = ? AND tenant_id = ?'
  ).bind(integrationId, tenantId).first<TenantIntegration>();
}

/** Update integration config/credentials/status */
export async function updateIntegration(
  db: D1Database,
  tenantId: string,
  integrationId: string,
  data: { config?: Record<string, unknown>; credentials?: Record<string, unknown>; status?: string }
): Promise<TenantIntegration | null> {
  const sets: string[] = ["updated_at = datetime('now')"];
  const bindings: unknown[] = [];
  if (data.config !== undefined) { sets.push('config = ?'); bindings.push(JSON.stringify(data.config)); }
  if (data.credentials !== undefined) { sets.push('credentials = ?'); bindings.push(JSON.stringify(data.credentials)); }
  if (data.status !== undefined) { sets.push('status = ?'); bindings.push(data.status); }
  bindings.push(integrationId, tenantId);
  await db.prepare(
    `UPDATE tenant_integrations SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ?`
  ).bind(...bindings).run();
  return getIntegration(db, tenantId, integrationId);
}

/** Delete tenant integration */
export async function uninstallIntegration(
  db: D1Database, tenantId: string, integrationId: string
): Promise<boolean> {
  const result = await db.prepare(
    'DELETE FROM tenant_integrations WHERE id = ? AND tenant_id = ?'
  ).bind(integrationId, tenantId).run();
  return (result.meta?.changes ?? 0) > 0;
}

/** Log an integration event */
export async function logEvent(
  db: D1Database,
  tenantId: string,
  integrationId: string,
  data: { eventType: string; direction?: string; payload?: Record<string, unknown>; status?: string; error?: string }
): Promise<void> {
  await db.prepare(
    `INSERT INTO integration_events (id, tenant_id, integration_id, event_type, direction, payload, status, error, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
  ).bind(
    crypto.randomUUID(), tenantId, integrationId,
    data.eventType, data.direction ?? 'outbound',
    JSON.stringify(data.payload ?? {}),
    data.status ?? 'success', data.error ?? null
  ).run();
}

/** Get event log for tenant, optionally filtered by integration */
export async function getEventLog(
  db: D1Database,
  tenantId: string,
  filters: { integrationId?: string; limit?: number } = {}
): Promise<IntegrationEvent[]> {
  const cap = Math.min(filters.limit ?? 50, 200);
  let query = 'SELECT * FROM integration_events WHERE tenant_id = ?';
  const bindings: unknown[] = [tenantId];
  if (filters.integrationId) { query += ' AND integration_id = ?'; bindings.push(filters.integrationId); }
  query += ' ORDER BY created_at DESC LIMIT ?';
  bindings.push(cap);
  const result = await db.prepare(query).bind(...bindings).all<IntegrationEvent>();
  return result.results;
}

/** Seed default integration catalog entries */
export async function seedCatalog(db: D1Database): Promise<number> {
  const entries = [
    { slug: 'slack', name: 'Slack', category: 'communication', auth_type: 'oauth2', description: 'Team messaging and notifications', events: '["message.sent","channel.created"]' },
    { slug: 'discord', name: 'Discord', category: 'communication', auth_type: 'webhook', description: 'Community messaging via webhooks', events: '["message.sent"]' },
    { slug: 'github', name: 'GitHub', category: 'devops', auth_type: 'oauth2', description: 'Source control and CI/CD', events: '["push","pull_request","issue"]' },
    { slug: 'jira', name: 'Jira', category: 'project_management', auth_type: 'api_key', description: 'Issue tracking and project management', events: '["issue.created","issue.updated"]' },
    { slug: 'linear', name: 'Linear', category: 'project_management', auth_type: 'api_key', description: 'Modern issue tracking for teams', events: '["issue.created","issue.updated"]' },
    { slug: 'notion', name: 'Notion', category: 'storage', auth_type: 'oauth2', description: 'Docs and database workspace', events: '["page.created","database.updated"]' },
    { slug: 'google-sheets', name: 'Google Sheets', category: 'analytics', auth_type: 'oauth2', description: 'Spreadsheet data sync', events: '["sheet.updated"]' },
  ];
  let inserted = 0;
  for (const e of entries) {
    const result = await db.prepare(
      `INSERT OR IGNORE INTO integration_catalog (id, name, slug, category, auth_type, description, supported_events, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))`
    ).bind(crypto.randomUUID(), e.name, e.slug, e.category, e.auth_type, e.description, e.events).run();
    inserted += result.meta?.changes ?? 0;
  }
  return inserted;
}
