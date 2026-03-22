/**
 * Tenant Data Export Service — CRUD for export requests and templates
 */

/** Create a new export request for a tenant */
async function requestExport(db: any, tenantId: string, data: {
  export_type: string;
  format?: string;
  filters_json?: string;
}) {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  // Expires 7 days after request
  const expiresAt = new Date(Date.now() + 7 * 86400000).toISOString();

  await db.prepare(
    `INSERT INTO data_export_requests
      (id, tenant_id, export_type, format, filters_json, status, requested_at, expires_at)
     VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)`
  ).bind(
    id, tenantId,
    data.export_type,
    data.format ?? 'json',
    data.filters_json ?? '{}',
    now, expiresAt
  ).run();

  return db.prepare('SELECT * FROM data_export_requests WHERE id = ?').bind(id).first();
}

/** List export requests for a tenant, optionally filtered by status or export_type */
async function listExports(db: any, tenantId: string, filters?: { status?: string; export_type?: string }) {
  let query = 'SELECT * FROM data_export_requests WHERE tenant_id = ?';
  const params: any[] = [tenantId];

  if (filters?.status) { query += ' AND status = ?'; params.push(filters.status); }
  if (filters?.export_type) { query += ' AND export_type = ?'; params.push(filters.export_type); }

  query += ' ORDER BY requested_at DESC LIMIT 100';
  const result = await db.prepare(query).bind(...params).all();
  return result.results ?? [];
}

/** Get a single export request by id, scoped to tenant */
async function getExport(db: any, tenantId: string, id: string) {
  return db.prepare(
    'SELECT * FROM data_export_requests WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).first();
}

/** Cancel a pending export request */
async function cancelExport(db: any, tenantId: string, id: string) {
  const row = await getExport(db, tenantId, id);
  if (!row) return null;
  if (row.status !== 'pending' && row.status !== 'processing') {
    throw new Error(`Cannot cancel export with status: ${row.status}`);
  }
  await db.prepare(
    `UPDATE data_export_requests SET status = 'cancelled' WHERE id = ? AND tenant_id = ?`
  ).bind(id, tenantId).run();
  return db.prepare('SELECT * FROM data_export_requests WHERE id = ?').bind(id).first();
}

/** Delete a completed or cancelled export request */
async function deleteExport(db: any, tenantId: string, id: string) {
  const row = await getExport(db, tenantId, id);
  if (!row) return null;
  await db.prepare(
    'DELETE FROM data_export_requests WHERE id = ? AND tenant_id = ?'
  ).bind(id, tenantId).run();
  return { deleted: true, id };
}

/** Get the download URL for a completed export */
async function getDownloadUrl(db: any, tenantId: string, id: string) {
  const row = await getExport(db, tenantId, id);
  if (!row) return null;
  if (row.status !== 'completed' || !row.file_url) {
    throw new Error('Export not ready for download');
  }
  return { url: row.file_url, expires_at: row.expires_at, file_size_bytes: row.file_size_bytes };
}

/** List all export templates (public catalog) */
async function listTemplates(db: any) {
  const result = await db.prepare(
    'SELECT * FROM data_export_templates ORDER BY name ASC'
  ).all();
  return result.results ?? [];
}

/** Create an export request from a template, with optional field overrides */
async function createFromTemplate(db: any, tenantId: string, templateId: string, overrides?: {
  format?: string;
  filters_json?: string;
}) {
  const template = await db.prepare(
    'SELECT * FROM data_export_templates WHERE id = ?'
  ).bind(templateId).first();
  if (!template) throw new Error(`Template not found: ${templateId}`);

  return requestExport(db, tenantId, {
    export_type: template.export_type,
    format: overrides?.format ?? template.default_format,
    filters_json: overrides?.filters_json ?? template.default_filters_json,
  });
}

/** Admin overview: export counts by status and aggregate storage usage */
async function getAdminOverview(db: any) {
  const [countRows, storageRow, recentRow] = await Promise.all([
    db.prepare(
      'SELECT status, COUNT(*) as count FROM data_export_requests GROUP BY status'
    ).all(),
    db.prepare(
      'SELECT SUM(file_size_bytes) as total_bytes, COUNT(*) as total_exports FROM data_export_requests'
    ).first(),
    db.prepare(
      'SELECT COUNT(*) as last_24h FROM data_export_requests WHERE requested_at >= datetime("now", "-1 day")'
    ).first(),
  ]);

  return {
    by_status: countRows.results ?? [],
    total_exports: storageRow?.total_exports ?? 0,
    storage_bytes: storageRow?.total_bytes ?? 0,
    exports_last_24h: recentRow?.last_24h ?? 0,
  };
}

export const tenantDataExportService = {
  requestExport,
  listExports,
  getExport,
  cancelExport,
  deleteExport,
  getDownloadUrl,
  listTemplates,
  createFromTemplate,
  getAdminOverview,
};
