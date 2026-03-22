// Platform Compliance Audit routes — admin-only SOC2/compliance check and result management

import { Hono } from 'hono';
import type { Env } from '../index';
import { platformComplianceAuditService as svc } from '../services/platform-compliance-audit-service';

export const platformComplianceAudit = new Hono<{ Bindings: Env }>();

/** Returns true when request carries valid admin key */
function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── GET /checks — list all active compliance checks ───────────────────────────

platformComplianceAudit.get('/checks', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Forbidden' }, 403);
  try {
    const data = await svc.listChecks(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[compliance-audit GET /checks]', err);
    return c.json({ success: false, error: 'Failed to list checks' }, 500);
  }
});

// ── POST /checks — create a compliance check definition ───────────────────────

platformComplianceAudit.post('/checks', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Forbidden' }, 403);
  try {
    const body = await c.req.json();
    if (!body.check_name || !body.category || !body.check_query) {
      return c.json({ success: false, error: 'check_name, category, and check_query are required' }, 400);
    }
    const data = await svc.createCheck(c.env.DB, body);
    return c.json({ success: true, data }, 201);
  } catch (err) {
    console.error('[compliance-audit POST /checks]', err);
    return c.json({ success: false, error: 'Failed to create check' }, 500);
  }
});

// ── GET /results — get compliance results, optionally filtered by check_id ────

platformComplianceAudit.get('/results', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Forbidden' }, 403);
  try {
    const checkId = c.req.query('check_id');
    const data = await svc.getResults(c.env.DB, checkId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[compliance-audit GET /results]', err);
    return c.json({ success: false, error: 'Failed to get results' }, 500);
  }
});

// ── GET /dashboard — summary counts by status and severity ────────────────────

platformComplianceAudit.get('/dashboard', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Forbidden' }, 403);
  try {
    const data = await svc.getDashboard(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[compliance-audit GET /dashboard]', err);
    return c.json({ success: false, error: 'Failed to get dashboard' }, 500);
  }
});
