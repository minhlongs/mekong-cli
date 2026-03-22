/**
 * Tenant Data Export routes — request, track, and download tenant data exports
 */
import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantDataExportService } from '../services/tenant-data-export-service';

const app = new Hono<{ Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } }>();

function isAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

/** POST /exports — request a new data export */
app.post('/exports', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ export_type: string; format?: string; filters_json?: string }>();
    if (!body.export_type) return c.json({ error: 'export_type is required' }, 400);

    const record = await tenantDataExportService.requestExport(c.env.DB, tenant.tenantId, body);
    return c.json({ success: true, data: record }, 201);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to create export' }, 500);
  }
});

/** GET /exports — list exports for authenticated tenant */
app.get('/exports', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const status = c.req.query('status');
    const export_type = c.req.query('export_type');
    const records = await tenantDataExportService.listExports(c.env.DB, tenant.tenantId, { status, export_type });
    return c.json({ success: true, data: records });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to list exports' }, 500);
  }
});

/** GET /exports/:id — get single export request */
app.get('/exports/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const record = await tenantDataExportService.getExport(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!record) return c.json({ error: 'Export not found' }, 404);
    return c.json({ success: true, data: record });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to get export' }, 500);
  }
});

/** POST /exports/:id/cancel — cancel a pending export */
app.post('/exports/:id/cancel', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const record = await tenantDataExportService.cancelExport(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!record) return c.json({ error: 'Export not found' }, 404);
    return c.json({ success: true, data: record });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to cancel export' }, 400);
  }
});

/** DELETE /exports/:id — delete an export request */
app.delete('/exports/:id', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await tenantDataExportService.deleteExport(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!result) return c.json({ error: 'Export not found' }, 404);
    return c.json({ success: true, data: result });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to delete export' }, 500);
  }
});

/** GET /exports/:id/download — get download URL for completed export */
app.get('/exports/:id/download', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await tenantDataExportService.getDownloadUrl(c.env.DB, tenant.tenantId, c.req.param('id'));
    if (!result) return c.json({ error: 'Export not found' }, 404);
    return c.json({ success: true, data: result });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Export not ready' }, 400);
  }
});

/** GET /templates — list all export templates (public) */
app.get('/templates', async (c) => {
  try {
    const templates = await tenantDataExportService.listTemplates(c.env.DB);
    return c.json({ success: true, data: templates });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to list templates' }, 500);
  }
});

/** POST /templates/:id/export — create export from template */
app.post('/templates/:id/export', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{ format?: string; filters_json?: string }>().catch(() => ({}));
    const record = await tenantDataExportService.createFromTemplate(c.env.DB, tenant.tenantId, c.req.param('id'), body);
    return c.json({ success: true, data: record }, 201);
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to create export from template' }, 400);
  }
});

/** GET /admin/overview — admin export stats */
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  try {
    const overview = await tenantDataExportService.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (e: any) {
    return c.json({ error: e.message ?? 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantDataExport };
