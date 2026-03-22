// Admin User Management Service — CRUD for admin users, roles, and activity log
import type { D1Database } from '@cloudflare/workers-types';

// --- Admin Users ---

/** List all admin users ordered by creation date */
export async function listAdminUsers(db: D1Database): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM admin_users ORDER BY created_at DESC`
  ).all();
  return rows.results;
}

/** Create a new admin user */
export async function createAdminUser(
  db: D1Database,
  data: {
    email: string;
    display_name: string;
    role?: string;
    permissions?: string[];
  }
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO admin_users (email, display_name, role, permissions_json)
     VALUES (?, ?, ?, ?) RETURNING *`
  ).bind(
    data.email,
    data.display_name,
    data.role ?? 'viewer',
    JSON.stringify(data.permissions ?? [])
  ).first();
}

/** Get a single admin user by ID */
export async function getAdminUser(db: D1Database, userId: string): Promise<unknown | null> {
  return db.prepare(`SELECT * FROM admin_users WHERE id = ?`).bind(userId).first();
}

/** Update admin user fields */
export async function updateAdminUser(
  db: D1Database,
  userId: string,
  data: {
    display_name?: string;
    role?: string;
    permissions?: string[];
    is_active?: boolean;
  }
): Promise<unknown | null> {
  const sets: string[] = [`updated_at = datetime('now')`];
  const binds: unknown[] = [];

  if (data.display_name !== undefined) { sets.push('display_name = ?'); binds.push(data.display_name); }
  if (data.role !== undefined) { sets.push('role = ?'); binds.push(data.role); }
  if (data.permissions !== undefined) { sets.push('permissions_json = ?'); binds.push(JSON.stringify(data.permissions)); }
  if (data.is_active !== undefined) { sets.push('is_active = ?'); binds.push(data.is_active ? 1 : 0); }

  if (sets.length === 1) return getAdminUser(db, userId); // no-op
  binds.push(userId);

  return db.prepare(
    `UPDATE admin_users SET ${sets.join(', ')} WHERE id = ? RETURNING *`
  ).bind(...binds).first();
}

/** Deactivate an admin user (soft delete) */
export async function deactivateAdminUser(db: D1Database, userId: string): Promise<unknown | null> {
  return db.prepare(
    `UPDATE admin_users SET is_active = 0, updated_at = datetime('now') WHERE id = ? RETURNING *`
  ).bind(userId).first();
}

// --- Roles ---

/** List all admin roles */
export async function listRoles(db: D1Database): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM admin_roles ORDER BY role_name ASC`
  ).all();
  return rows.results;
}

/** Create a new role */
export async function createRole(
  db: D1Database,
  data: { role_name: string; description?: string; permissions?: string[] }
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO admin_roles (role_name, description, permissions_json) VALUES (?, ?, ?) RETURNING *`
  ).bind(
    data.role_name,
    data.description ?? null,
    JSON.stringify(data.permissions ?? [])
  ).first();
}

// --- Activity Log ---

/** Log an admin action */
export async function logActivity(
  db: D1Database,
  adminUserId: string,
  action: string,
  resourceType: string,
  resourceId: string | null,
  details: unknown,
  ipAddress: string | null
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO admin_activity_log (admin_user_id, action, resource_type, resource_id, details, ip_address)
     VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    adminUserId,
    action,
    resourceType,
    resourceId ?? null,
    details ? JSON.stringify(details) : null,
    ipAddress ?? null
  ).first();
}

/** Get activity log with optional filters */
export async function getActivityLog(
  db: D1Database,
  filters: { admin_user_id?: string; action?: string; limit?: number }
): Promise<unknown[]> {
  const conditions: string[] = [];
  const binds: unknown[] = [];

  if (filters.admin_user_id) { conditions.push('admin_user_id = ?'); binds.push(filters.admin_user_id); }
  if (filters.action) { conditions.push('action = ?'); binds.push(filters.action); }

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  binds.push(Math.min(filters.limit ?? 100, 500));

  const rows = await db.prepare(
    `SELECT * FROM admin_activity_log ${where} ORDER BY created_at DESC LIMIT ?`
  ).bind(...binds).all();
  return rows.results;
}

// --- Dashboard ---

/** Dashboard stats: user counts, role breakdown, recent activity */
export async function getDashboard(db: D1Database): Promise<unknown> {
  const [total, active, superAdmins, admins, viewers, recentActivity] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM admin_users`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM admin_users WHERE is_active = 1`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM admin_users WHERE role = 'super_admin' AND is_active = 1`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM admin_users WHERE role = 'admin' AND is_active = 1`).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM admin_users WHERE role = 'viewer' AND is_active = 1`).first<{ count: number }>(),
    db.prepare(`SELECT * FROM admin_activity_log ORDER BY created_at DESC LIMIT 10`).all(),
  ]);

  return {
    users: {
      total: total?.count ?? 0,
      active: active?.count ?? 0,
      inactive: (total?.count ?? 0) - (active?.count ?? 0),
      byRole: {
        super_admin: superAdmins?.count ?? 0,
        admin: admins?.count ?? 0,
        viewer: viewers?.count ?? 0,
      },
    },
    recentActivity: recentActivity.results,
  };
}
