/**
 * Platform Tenant Grouping Service — list groups, create group, get members, dashboard
 * Used by platform-tenant-grouping route (X-Admin-Key protected)
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type DB = any;

interface GroupData {
  group_name: string;
  description?: string;
  parent_group_id?: string;
  settings_json?: string;
  status?: string;
}

/** List all tenant groups with optional status filter */
async function listGroups(db: DB, status?: string) {
  try {
    const where = status ? `WHERE status = '${status}'` : '';
    const { results } = await db
      .prepare(`SELECT * FROM tenant_groups ${where} ORDER BY group_name ASC`)
      .all();
    return results as any[];
  } catch (err) {
    throw new Error(`listGroups failed: ${(err as Error).message}`);
  }
}

/** Create a new tenant group */
async function createGroup(db: DB, data: GroupData) {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO tenant_groups (id, group_name, description, parent_group_id, settings_json, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        data.group_name,
        data.description ?? null,
        data.parent_group_id ?? null,
        data.settings_json ?? '{}',
        data.status ?? 'active',
        now,
        now
      )
      .run();
    return db.prepare('SELECT * FROM tenant_groups WHERE id = ?').bind(id).first();
  } catch (err) {
    throw new Error(`createGroup failed: ${(err as Error).message}`);
  }
}

/** Get members of a group with optional role filter */
async function getMembers(db: DB, groupId: string, role?: string) {
  try {
    const where = role
      ? `WHERE m.group_id = ? AND m.role = '${role}'`
      : 'WHERE m.group_id = ?';
    const { results } = await db
      .prepare(
        `SELECT m.*, t.id as tenant_id
         FROM tenant_group_members m
         LEFT JOIN tenants t ON t.id = m.tenant_id
         ${where}
         ORDER BY m.joined_at DESC`
      )
      .bind(groupId)
      .all();
    return results as any[];
  } catch (err) {
    throw new Error(`getMembers failed: ${(err as Error).message}`);
  }
}

/** Dashboard: group counts by status + top 5 largest groups by member count */
async function getDashboard(db: DB) {
  try {
    const [statusCounts, topGroups] = await Promise.all([
      db
        .prepare(`SELECT status, COUNT(*) as count FROM tenant_groups GROUP BY status`)
        .all(),
      db
        .prepare(
          `SELECT g.id, g.group_name, g.status, COUNT(m.id) as member_count
           FROM tenant_groups g
           LEFT JOIN tenant_group_members m ON m.group_id = g.id
           GROUP BY g.id
           ORDER BY member_count DESC
           LIMIT 5`
        )
        .all(),
    ]);
    return {
      byStatus: statusCounts.results as any[],
      topGroups: topGroups.results as any[],
    };
  } catch (err) {
    throw new Error(`getDashboard failed: ${(err as Error).message}`);
  }
}

export const platformTenantGroupingService = { listGroups, createGroup, getMembers, getDashboard };
