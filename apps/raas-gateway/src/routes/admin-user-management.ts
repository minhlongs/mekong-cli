/**
 * Admin User Management routes — CRUD for admin users, roles, and activity log
 * All endpoints require X-Admin-Key header. Mount path: /admin/users-mgmt
 */

import { Hono } from 'hono';
import * as svc from '../services/admin-user-management-service';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /users — list all admin users
app.get('/users', async (c) => {
  try {
    const data = await svc.listAdminUsers(c.env.DB);
    return c.json({ success: true, data, count: data.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /users — create admin user
app.post('/users', async (c) => {
  try {
    const body = await c.req.json<{
      email: string;
      display_name: string;
      role?: string;
      permissions?: string[];
    }>();
    if (!body.email) return c.json({ error: 'email is required' }, 400);
    if (!body.display_name) return c.json({ error: 'display_name is required' }, 400);
    const user = await svc.createAdminUser(c.env.DB, body);
    await svc.logActivity(c.env.DB, 'system', 'create_user', 'user', null, { email: body.email }, c.req.header('CF-Connecting-IP') ?? null);
    return c.json({ success: true, data: user }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /users/:id — get admin user
app.get('/users/:id', async (c) => {
  try {
    const user = await svc.getAdminUser(c.env.DB, c.req.param('id'));
    if (!user) return c.json({ error: 'Admin user not found' }, 404);
    return c.json({ success: true, data: user });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /users/:id — update admin user
app.put('/users/:id', async (c) => {
  try {
    const body = await c.req.json<{
      display_name?: string;
      role?: string;
      permissions?: string[];
      is_active?: boolean;
    }>();
    const user = await svc.updateAdminUser(c.env.DB, c.req.param('id'), body);
    if (!user) return c.json({ error: 'Admin user not found' }, 404);
    await svc.logActivity(c.env.DB, 'system', 'update_user', 'user', c.req.param('id'), body, c.req.header('CF-Connecting-IP') ?? null);
    return c.json({ success: true, data: user });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// DELETE /users/:id — deactivate admin user
app.delete('/users/:id', async (c) => {
  try {
    const user = await svc.deactivateAdminUser(c.env.DB, c.req.param('id'));
    if (!user) return c.json({ error: 'Admin user not found' }, 404);
    await svc.logActivity(c.env.DB, 'system', 'deactivate_user', 'user', c.req.param('id'), null, c.req.header('CF-Connecting-IP') ?? null);
    return c.json({ success: true, data: user });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /roles — list all roles
app.get('/roles', async (c) => {
  try {
    const data = await svc.listRoles(c.env.DB);
    return c.json({ success: true, data, count: data.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /roles — create role
app.post('/roles', async (c) => {
  try {
    const body = await c.req.json<{ role_name: string; description?: string; permissions?: string[] }>();
    if (!body.role_name) return c.json({ error: 'role_name is required' }, 400);
    const role = await svc.createRole(c.env.DB, body);
    return c.json({ success: true, data: role }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /activity — activity log with optional filters
app.get('/activity', async (c) => {
  try {
    const filters = {
      admin_user_id: c.req.query('admin_user_id'),
      action: c.req.query('action'),
      limit: parseInt(c.req.query('limit') ?? '100', 10),
    };
    const data = await svc.getActivityLog(c.env.DB, filters);
    return c.json({ success: true, data, count: data.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — dashboard stats
app.get('/dashboard', async (c) => {
  try {
    const data = await svc.getDashboard(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as adminUserManagement };
