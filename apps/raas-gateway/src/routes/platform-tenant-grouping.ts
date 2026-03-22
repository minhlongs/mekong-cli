/**
 * Platform Tenant Grouping routes — admin-only group management
 * Protected by X-Admin-Key header, 403 on missing/invalid key
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { platformTenantGroupingService as svc } from '../services/platform-tenant-grouping-service';

export const platformTenantGrouping = new Hono<{ Bindings: Env }>();

// Admin-only guard
platformTenantGrouping.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;
  if (!expected || key !== expected) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  await next();
});

// GET /platform/groups?status=active
platformTenantGrouping.get('/groups', async (c) => {
  try {
    const status = c.req.query('status');
    const groups = await svc.listGroups(c.env.DB, status);
    return json({ groups, total: groups.length });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

// POST /platform/groups — body: { group_name, description?, parent_group_id?, settings_json?, status? }
platformTenantGrouping.post('/groups', async (c) => {
  try {
    const body = await c.req.json();
    if (!body.group_name) {
      return json({ error: 'group_name is required' }, { status: 400 });
    }
    const group = await svc.createGroup(c.env.DB, body);
    return json({ group }, { status: 201 });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

// GET /platform/members?group_id=...&role=member
platformTenantGrouping.get('/members', async (c) => {
  try {
    const groupId = c.req.query('group_id');
    if (!groupId) {
      return json({ error: 'group_id is required' }, { status: 400 });
    }
    const role = c.req.query('role');
    const members = await svc.getMembers(c.env.DB, groupId, role);
    return json({ members, total: members.length });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

// GET /platform/dashboard
platformTenantGrouping.get('/dashboard', async (c) => {
  try {
    const data = await svc.getDashboard(c.env.DB);
    return json(data);
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});
