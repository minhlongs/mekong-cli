/**
 * RBAC routes — role management and permission checks mounted at /v1/rbac
 * All routes require JWT auth. Static routes (/seed, /check) before /:id catch-all.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createRole,
  getRoles,
  getRole,
  updateRole,
  deleteRole,
  assignRole,
  revokeRole,
  getUserRoles,
  checkPermission,
  seedDefaultRoles,
} from '../services/rbac-service';

const app = new Hono<{ Bindings: Env }>();

// Apply auth to all routes
app.use('/*', auth());

// ── Roles ─────────────────────────────────────────────────────────────────────

// GET /roles — list all roles for tenant
app.get('/roles', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const roles = await getRoles(c.env.DB, tenantId);
    return c.json({ success: true, data: roles });
  } catch (err) {
    return c.json({ success: false, error: 'Failed to list roles' }, 500);
  }
});

// POST /roles — create custom role
app.post('/roles', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ name: string; description?: string; permissions: string[] }>();
    if (!body.name || !Array.isArray(body.permissions)) {
      return c.json({ success: false, error: 'name and permissions array are required' }, 400);
    }
    const role = await createRole(c.env.DB, tenantId, body);
    return c.json({ success: true, data: role }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to create role';
    return c.json({ success: false, error: msg }, 409);
  }
});

// POST /roles/seed — seed default system roles (BEFORE /:id)
app.post('/roles/seed', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const roles = await seedDefaultRoles(c.env.DB, tenantId);
    return c.json({ success: true, data: roles });
  } catch (err) {
    return c.json({ success: false, error: 'Failed to seed roles' }, 500);
  }
});

// GET /roles/:id — get single role
app.get('/roles/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const role = await getRole(c.env.DB, tenantId, c.req.param('id'));
    if (!role) return c.json({ success: false, error: 'Role not found' }, 404);
    return c.json({ success: true, data: role });
  } catch (err) {
    return c.json({ success: false, error: 'Failed to get role' }, 500);
  }
});

// PUT /roles/:id — update role
app.put('/roles/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ name?: string; description?: string; permissions?: string[] }>();
    const role = await updateRole(c.env.DB, tenantId, c.req.param('id'), body);
    if (!role) return c.json({ success: false, error: 'Role not found' }, 404);
    return c.json({ success: true, data: role });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to update role';
    const status = msg.includes('system') ? 403 : 500;
    return c.json({ success: false, error: msg }, status);
  }
});

// DELETE /roles/:id — delete role
app.delete('/roles/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const deleted = await deleteRole(c.env.DB, tenantId, c.req.param('id'));
    if (!deleted) return c.json({ success: false, error: 'Role not found' }, 404);
    return c.json({ success: true, data: { deleted: true } });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to delete role';
    const status = msg.includes('system') ? 403 : 500;
    return c.json({ success: false, error: msg }, status);
  }
});

// ── Permission Check ──────────────────────────────────────────────────────────

// GET /check?userId=&permission= — check if user has permission (BEFORE /users/:userId)
app.get('/check', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const userId = c.req.query('userId');
    const permission = c.req.query('permission');
    if (!userId || !permission) {
      return c.json({ success: false, error: 'userId and permission query params are required' }, 400);
    }
    const allowed = await checkPermission(c.env.DB, tenantId, userId, permission);
    return c.json({ success: true, data: { user_id: userId, permission, allowed } });
  } catch (err) {
    return c.json({ success: false, error: 'Failed to check permission' }, 500);
  }
});

// ── User Role Assignments ─────────────────────────────────────────────────────

// GET /users/:userId/roles — get roles assigned to user
app.get('/users/:userId/roles', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await getUserRoles(c.env.DB, tenantId, c.req.param('userId'));
    return c.json({ success: true, data: result });
  } catch (err) {
    return c.json({ success: false, error: 'Failed to get user roles' }, 500);
  }
});

// POST /users/:userId/roles — assign role to user
app.post('/users/:userId/roles', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const { tenantId: assignedBy } = getTenant(c); // caller identity
    const body = await c.req.json<{ roleId: string }>();
    if (!body.roleId) return c.json({ success: false, error: 'roleId is required' }, 400);
    const assignment = await assignRole(c.env.DB, tenantId, c.req.param('userId'), body.roleId, assignedBy);
    return c.json({ success: true, data: assignment }, 201);
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to assign role';
    return c.json({ success: false, error: msg }, 400);
  }
});

// DELETE /users/:userId/roles/:roleId — revoke role from user
app.delete('/users/:userId/roles/:roleId', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const { userId, roleId } = c.req.param();
    const revoked = await revokeRole(c.env.DB, tenantId, userId, roleId);
    if (!revoked) return c.json({ success: false, error: 'Assignment not found' }, 404);
    return c.json({ success: true, data: { revoked: true } });
  } catch (err) {
    return c.json({ success: false, error: 'Failed to revoke role' }, 500);
  }
});

export const rbac = app;
