/**
 * Team members routes — invite, list, update, remove team members with role-based access
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const team = new Hono<{ Bindings: Env }>();
team.use('*', auth());

/** Tiers that can manage team members */
const TEAM_TIERS = ['pro', 'agency', 'master', 'enterprise'];
function canManageTeam(tier: string): boolean {
  return TEAM_TIERS.includes(tier);
}

/** Email format validator */
function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * POST /v1/team/invite — invite a new team member (pro+ only)
 */
team.post('/invite', async (c) => {
  const tenant = getTenant(c);

  if (!canManageTeam(tenant.tier)) {
    return json({ error: 'Team management requires Pro tier or above', code: 'UPGRADE_REQUIRED' }, { status: 403 });
  }

  const body = await c.req.json().catch(() => ({})) as { email?: string; name?: string; role?: string };
  const email = body.email?.trim().toLowerCase();
  const role = body.role ?? 'member';

  if (!email || !isValidEmail(email)) {
    return json({ error: 'Valid email required', code: 'INVALID_EMAIL' }, { status: 400 });
  }
  if (!['admin', 'member'].includes(role)) {
    return json({ error: 'Role must be admin or member', code: 'INVALID_ROLE' }, { status: 400 });
  }

  const id = crypto.randomUUID();
  try {
    await c.env.DB.prepare(
      `INSERT INTO team_members (id, tenant_id, email, name, role, status, invited_by)
       VALUES (?, ?, ?, ?, ?, 'pending', ?)`
    ).bind(id, tenant.tenantId, email, body.name ?? null, role, tenant.tenantId).run();
  } catch {
    return json({ error: 'Member already invited', code: 'ALREADY_EXISTS' }, { status: 409 });
  }

  return json({ id, email, role, status: 'pending' }, { status: 201 });
});

/**
 * GET /v1/team/members — list all team members for tenant
 */
team.get('/members', async (c) => {
  const tenant = getTenant(c);

  const result = await c.env.DB.prepare(
    `SELECT id, email, name, role, status, created_at FROM team_members WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenant.tenantId).all<{ id: string; email: string; name: string | null; role: string; status: string; created_at: string }>();

  return json({ members: result.results, total: result.results.length });
});

/**
 * PUT /v1/team/members/:id — update role or name
 */
team.put('/members/:id', async (c) => {
  const tenant = getTenant(c);
  const memberId = c.req.param('id');
  const body = await c.req.json().catch(() => ({})) as { role?: string; name?: string };

  if (body.role && !['admin', 'member'].includes(body.role)) {
    return json({ error: 'Role must be admin or member', code: 'INVALID_ROLE' }, { status: 400 });
  }

  const member = await c.env.DB.prepare(
    'SELECT id, email, role, name, status FROM team_members WHERE id = ? AND tenant_id = ?'
  ).bind(memberId, tenant.tenantId).first<{ id: string; email: string; role: string; name: string | null; status: string }>();

  if (!member) {
    return json({ error: 'Member not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  const newRole = body.role ?? member.role;
  const newName = body.name ?? member.name;
  await c.env.DB.prepare(
    'UPDATE team_members SET role = ?, name = ? WHERE id = ? AND tenant_id = ?'
  ).bind(newRole, newName, memberId, tenant.tenantId).run();

  return json({ id: member.id, email: member.email, role: newRole, name: newName, status: member.status });
});

/**
 * DELETE /v1/team/members/:id — remove a team member
 */
team.delete('/members/:id', async (c) => {
  const tenant = getTenant(c);
  const memberId = c.req.param('id');

  const result = await c.env.DB.prepare(
    'DELETE FROM team_members WHERE id = ? AND tenant_id = ?'
  ).bind(memberId, tenant.tenantId).run();

  if (result.meta.changes === 0) {
    return json({ error: 'Member not found', code: 'NOT_FOUND' }, { status: 404 });
  }

  return json({ success: true });
});
