/**
 * Admin Platform Migration Routes — manage D1 schema migration records
 * All routes require X-Admin-Key header. Returns 403 if missing or invalid.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { adminPlatformMigrationService as svc } from '../services/admin-platform-migration-service';

export const adminPlatformMigration = new Hono<{ Bindings: Env }>();

// Admin-only guard
adminPlatformMigration.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  await next();
});

// GET /migrations?status=&version=
adminPlatformMigration.get('/migrations', async (c) => {
  try {
    const status = c.req.query('status');
    const version = c.req.query('version');
    const migrations = await svc.listMigrations(c.env.DB, { status, version });
    return c.json({ migrations, count: migrations.length });
  } catch (err) {
    return c.json({ error: (err as Error).message }, 500);
  }
});

// POST /migrations — body: { id, migration_name, version, migration_type?, sql_content?, applied_by? }
adminPlatformMigration.post('/migrations', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.id || !body.migration_name || !body.version) {
      return c.json({ error: 'id, migration_name, version are required' }, 400);
    }
    const migration = await svc.createMigration(c.env.DB, body);
    return c.json({ migration }, 201);
  } catch (err) {
    return c.json({ error: (err as Error).message }, 500);
  }
});

// GET /rollbacks?migration_id=
adminPlatformMigration.get('/rollbacks', async (c) => {
  try {
    const migration_id = c.req.query('migration_id');
    const rollbacks = await svc.getRollbacks(c.env.DB, migration_id);
    return c.json({ rollbacks, count: rollbacks.length });
  } catch (err) {
    return c.json({ error: (err as Error).message }, 500);
  }
});

// GET /dashboard — summary counts + recent activity
adminPlatformMigration.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json(dashboard);
  } catch (err) {
    return c.json({ error: (err as Error).message }, 500);
  }
});
