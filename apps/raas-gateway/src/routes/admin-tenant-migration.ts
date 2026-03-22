/**
 * Admin tenant migration routes — migrate tenants between tiers/plans
 * All routes require X-Admin-Key header (403 if missing or invalid)
 */

import { Hono } from 'hono';
import { adminTenantMigrationService } from '../services/admin-tenant-migration';

type Bindings = {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: any;
};

const app = new Hono<{ Bindings: Bindings }>();

/** Verify X-Admin-Key on every request */
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

/** GET /migrations — list migrations with optional ?tenantId=&status= filters */
app.get('/migrations', async (c) => {
  try {
    const tenantId = c.req.query('tenantId');
    const status = c.req.query('status');
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : undefined;
    const result = await adminTenantMigrationService.listMigrations(c.env.DB, { tenantId, status, limit });
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** POST /migrations — create a new tenant migration */
app.post('/migrations', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const { tenantId, fromTier, toTier, migrationType, initiatedBy } = body;
    if (!tenantId || !fromTier || !toTier) {
      return c.json({ error: 'tenantId, fromTier, and toTier are required' }, 400);
    }
    const result = await adminTenantMigrationService.createMigration(c.env.DB, {
      tenantId,
      fromTier,
      toTier,
      migrationType,
      initiatedBy,
    });
    return c.json(result, result.success ? 201 : 500);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /steps — get migration steps for a given ?migrationId= */
app.get('/steps', async (c) => {
  try {
    const migrationId = c.req.query('migrationId');
    if (!migrationId) {
      return c.json({ error: 'migrationId query param is required' }, 400);
    }
    const result = await adminTenantMigrationService.getSteps(c.env.DB, migrationId);
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

/** GET /dashboard — aggregated migration stats */
app.get('/dashboard', async (c) => {
  try {
    const result = await adminTenantMigrationService.getDashboard(c.env.DB);
    return c.json(result);
  } catch (err: any) {
    return c.json({ error: err.message }, 500);
  }
});

export { app as adminTenantMigration };
