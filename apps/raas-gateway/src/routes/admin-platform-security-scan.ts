/**
 * Admin Platform Security Scan routes — security scan and findings management
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-security-scan
 */

import { Hono } from 'hono';
import { adminPlatformSecurityScanService } from '../services/admin-platform-security-scan';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// Admin auth guard for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /scans — list all scans, optional ?scan_type= and ?status= filters
app.get('/scans', async (c) => {
  try {
    const scan_type = c.req.query('scan_type');
    const status = c.req.query('status');
    const result = await adminPlatformSecurityScanService.listScans(c.env.DB, { scan_type, status });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ scans: result.data, count: (result.data as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /scans — create a new security scan
app.post('/scans', async (c) => {
  try {
    const body = await c.req.json() as { scan_type: string; target: string };
    if (!body.scan_type || !body.target) {
      return c.json({ error: 'scan_type and target are required' }, 400);
    }
    const result = await adminPlatformSecurityScanService.createScan(c.env.DB, body);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /findings — list findings, optional ?scan_id= ?severity= ?status= filters
app.get('/findings', async (c) => {
  try {
    const scan_id = c.req.query('scan_id');
    const severity = c.req.query('severity');
    const status = c.req.query('status');
    const result = await adminPlatformSecurityScanService.getFindings(c.env.DB, { scan_id, severity, status });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ findings: result.data, count: (result.data as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — summary counts by status/type, severity breakdown, recent findings
app.get('/dashboard', async (c) => {
  try {
    const result = await adminPlatformSecurityScanService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json(result.data);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminPlatformSecurityScan };
