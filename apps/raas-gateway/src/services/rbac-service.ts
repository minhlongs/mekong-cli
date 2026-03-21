/**
 * RBAC Service — role-based access control: roles, assignments, permission checks
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface Role {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  permissions: string; // JSON array
  is_system: number;   // 0 | 1
  created_at: string;
  updated_at: string;
}

export interface RoleAssignment {
  id: string;
  tenant_id: string;
  user_id: string;
  role_id: string;
  assigned_by: string | null;
  created_at: string;
}

export interface CreateRoleInput {
  name: string;
  description?: string;
  permissions: string[];
}

export interface UpdateRoleInput {
  name?: string;
  description?: string;
  permissions?: string[];
}

/** System role definitions seeded per tenant */
const SYSTEM_ROLES = [
  { name: 'admin',   description: 'Full access',             permissions: ['*'] },
  { name: 'editor',  description: 'Read/write missions & projects',
    permissions: ['missions:read', 'missions:write', 'projects:read', 'projects:write', 'templates:read'] },
  { name: 'viewer',  description: 'Read-only access',
    permissions: ['missions:read', 'projects:read', 'templates:read', 'dashboard:read'] },
  { name: 'billing', description: 'Billing & usage access',
    permissions: ['billing:read', 'billing:write', 'usage:read', 'invoices:read'] },
];

// ── Role CRUD ─────────────────────────────────────────────────────────────────

export async function createRole(db: D1Database, tenantId: string, input: CreateRoleInput): Promise<Role> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO roles (id, tenant_id, name, description, permissions, is_system)
     VALUES (?, ?, ?, ?, ?, 0)`
  ).bind(id, tenantId, input.name, input.description ?? null, JSON.stringify(input.permissions)).run();
  return getRole(db, tenantId, id) as Promise<Role>;
}

export async function getRoles(db: D1Database, tenantId: string): Promise<Role[]> {
  const { results } = await db.prepare(
    'SELECT * FROM roles WHERE tenant_id = ? ORDER BY is_system DESC, name ASC'
  ).bind(tenantId).all<Role>();
  return results;
}

export async function getRole(db: D1Database, tenantId: string, roleId: string): Promise<Role | null> {
  return db.prepare(
    'SELECT * FROM roles WHERE id = ? AND tenant_id = ?'
  ).bind(roleId, tenantId).first<Role>();
}

export async function updateRole(db: D1Database, tenantId: string, roleId: string, input: UpdateRoleInput): Promise<Role | null> {
  const role = await getRole(db, tenantId, roleId);
  if (!role) return null;
  if (role.is_system) throw new Error('Cannot modify system roles');

  const fields: string[] = ["updated_at = datetime('now')"];
  const values: unknown[] = [];

  if (input.name !== undefined)        { fields.push('name = ?');        values.push(input.name); }
  if (input.description !== undefined) { fields.push('description = ?'); values.push(input.description); }
  if (input.permissions !== undefined) { fields.push('permissions = ?'); values.push(JSON.stringify(input.permissions)); }

  if (fields.length === 1) return role;

  values.push(roleId, tenantId);
  await db.prepare(`UPDATE roles SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`).bind(...values).run();
  return getRole(db, tenantId, roleId);
}

export async function deleteRole(db: D1Database, tenantId: string, roleId: string): Promise<boolean> {
  const role = await getRole(db, tenantId, roleId);
  if (!role) return false;
  if (role.is_system) throw new Error('Cannot delete system roles');
  const { success } = await db.prepare(
    'DELETE FROM roles WHERE id = ? AND tenant_id = ?'
  ).bind(roleId, tenantId).run();
  return success;
}

// ── Role Assignments ──────────────────────────────────────────────────────────

export async function assignRole(
  db: D1Database, tenantId: string, userId: string, roleId: string, assignedBy?: string
): Promise<RoleAssignment> {
  const role = await getRole(db, tenantId, roleId);
  if (!role) throw new Error('Role not found');
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO role_assignments (id, tenant_id, user_id, role_id, assigned_by)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(tenant_id, user_id, role_id) DO NOTHING`
  ).bind(id, tenantId, userId, roleId, assignedBy ?? null).run();
  return db.prepare(
    'SELECT * FROM role_assignments WHERE tenant_id = ? AND user_id = ? AND role_id = ?'
  ).bind(tenantId, userId, roleId).first<RoleAssignment>() as Promise<RoleAssignment>;
}

export async function revokeRole(db: D1Database, tenantId: string, userId: string, roleId: string): Promise<boolean> {
  const { success } = await db.prepare(
    'DELETE FROM role_assignments WHERE tenant_id = ? AND user_id = ? AND role_id = ?'
  ).bind(tenantId, userId, roleId).run();
  return success;
}

export async function getUserRoles(db: D1Database, tenantId: string, userId: string): Promise<{
  roles: Role[]; permissions: string[];
}> {
  const { results: assignments } = await db.prepare(
    'SELECT role_id FROM role_assignments WHERE tenant_id = ? AND user_id = ?'
  ).bind(tenantId, userId).all<{ role_id: string }>();

  if (!assignments.length) return { roles: [], permissions: [] };

  const roleIds = assignments.map(a => a.role_id);
  const placeholders = roleIds.map(() => '?').join(',');
  const { results: roles } = await db.prepare(
    `SELECT * FROM roles WHERE id IN (${placeholders}) AND tenant_id = ?`
  ).bind(...roleIds, tenantId).all<Role>();

  const permSet = new Set<string>();
  for (const role of roles) {
    const perms: string[] = JSON.parse(role.permissions);
    for (const p of perms) permSet.add(p);
  }

  return { roles, permissions: Array.from(permSet) };
}

export async function checkPermission(db: D1Database, tenantId: string, userId: string, permission: string): Promise<boolean> {
  const { permissions } = await getUserRoles(db, tenantId, userId);
  return permissions.includes('*') || permissions.includes(permission);
}

// ── Seed ──────────────────────────────────────────────────────────────────────

export async function seedDefaultRoles(db: D1Database, tenantId: string): Promise<Role[]> {
  const seeded: Role[] = [];
  for (const def of SYSTEM_ROLES) {
    const id = crypto.randomUUID();
    try {
      await db.prepare(
        `INSERT INTO roles (id, tenant_id, name, description, permissions, is_system)
         VALUES (?, ?, ?, ?, ?, 1)
         ON CONFLICT(tenant_id, name) DO NOTHING`
      ).bind(id, tenantId, def.name, def.description, JSON.stringify(def.permissions)).run();
    } catch { /* skip duplicates */ }
    const role = await db.prepare(
      'SELECT * FROM roles WHERE tenant_id = ? AND name = ?'
    ).bind(tenantId, def.name).first<Role>();
    if (role) seeded.push(role);
  }
  return seeded;
}
