/**
 * Audit Export routes — export logs, compliance checks, GDPR, data retention
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  exportAuditLogs,
  getComplianceStatus,
  getDataRetentionPolicy,
  setDataRetentionPolicy,
  purgeExpiredData,
  getGDPRExport,
  requestDataDeletion,
  getExportHistory,
} from '../services/audit-export-service';

export const auditExport = new Hono<{ Bindings: Env }>();

// All routes require auth
auditExport.use('*', auth());

/**
 * POST /audit/export — export audit logs as JSON or CSV
 */
auditExport.post('/export', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{
    format?: 'json' | 'csv';
    start_date?: string;
    end_date?: string;
    event_types?: string[];
    limit?: number;
  }>();

  const format = body.format === 'csv' ? 'csv' : 'json';

  const output = await exportAuditLogs(c.env.DB, {
    tenant_id: tenantId,
    format,
    start_date: body.start_date,
    end_date: body.end_date,
    event_types: body.event_types,
    limit: body.limit,
  });

  // Track export in history — count rows from output
  const rowCount = format === 'csv'
    ? Math.max(0, output.split('\n').length - 1)
    : (JSON.parse(output).count ?? 0);

  await c.env.DB.prepare(
    `INSERT INTO audit_exports (id, tenant_id, format, row_count, status) VALUES (?, ?, ?, ?, 'completed')`
  ).bind(crypto.randomUUID(), tenantId, format, rowCount).run();

  if (format === 'csv') {
    return new Response(output, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="audit-${tenantId}-${Date.now()}.csv"`,
      },
    });
  }

  return new Response(output, {
    headers: { 'Content-Type': 'application/json' },
  });
});

/**
 * GET /audit/compliance — compliance checklist
 */
auditExport.get('/compliance', async (c) => {
  const { tenantId } = getTenant(c);
  const checks = await getComplianceStatus(c.env.DB, tenantId);
  const passed = checks.filter(ch => ch.status === 'pass').length;
  return json({ total: checks.length, passed, checks });
});

/**
 * GET /audit/retention — get data retention policy
 */
auditExport.get('/retention', async (c) => {
  const { tenantId } = getTenant(c);
  const policy = await getDataRetentionPolicy(c.env.DB, tenantId);
  return json(policy);
});

/**
 * PUT /audit/retention — set data retention policy
 */
auditExport.put('/retention', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{ retention_days?: number; auto_delete?: boolean }>();

  const days = Math.max(30, Math.min(body.retention_days ?? 365, 3650));
  const autoDelete = Boolean(body.auto_delete);

  await setDataRetentionPolicy(c.env.DB, tenantId, days, autoDelete);
  return json({ retention_days: days, auto_delete: autoDelete, updated: true });
});

/**
 * POST /audit/purge — manually purge expired data
 */
auditExport.post('/purge', async (c) => {
  const { tenantId } = getTenant(c);
  const result = await purgeExpiredData(c.env.DB, tenantId);
  return json(result);
});

/**
 * GET /audit/gdpr-export — full GDPR data export
 */
auditExport.get('/gdpr-export', async (c) => {
  const { tenantId } = getTenant(c);
  const data = await getGDPRExport(c.env.DB, tenantId);
  return json(data);
});

/**
 * POST /audit/deletion-request — GDPR right to be forgotten
 */
auditExport.post('/deletion-request', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{ reason?: string }>();
  const result = await requestDataDeletion(c.env.DB, tenantId, body.reason ?? '');
  return json(result, { status: 202 });
});

/**
 * GET /audit/exports — export history
 */
auditExport.get('/exports', async (c) => {
  const { tenantId } = getTenant(c);
  const history = await getExportHistory(c.env.DB, tenantId);
  return json({ count: history.length, exports: history });
});
