// Tenant Workspace Settings Service — CRUD for workspace settings and invitations

/** Generate a random ID */
function newId(): string {
  return crypto.randomUUID();
}

/** ISO timestamp */
function now(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

/** Get workspace settings for a tenant, creating defaults if missing */
async function getSettings(db: any, tenantId: string): Promise<unknown> {
  const existing = await db
    .prepare('SELECT * FROM workspace_settings WHERE tenant_id = ?')
    .bind(tenantId)
    .first();
  if (existing) return existing;

  // Auto-create defaults on first access
  return db
    .prepare(
      `INSERT INTO workspace_settings (id, tenant_id)
       VALUES (?, ?) RETURNING *`
    )
    .bind(newId(), tenantId)
    .first();
}

/** Update workspace settings for a tenant (upsert) */
async function updateSettings(
  db: any,
  tenantId: string,
  data: {
    workspace_name?: string;
    theme?: string;
    timezone?: string;
    language?: string;
    date_format?: string;
    notification_config_json?: string;
    branding_json?: string;
  }
): Promise<unknown> {
  // Ensure row exists
  await getSettings(db, tenantId);

  const fields: string[] = [];
  const values: unknown[] = [];

  if (data.workspace_name !== undefined) { fields.push('workspace_name = ?'); values.push(data.workspace_name); }
  if (data.theme !== undefined) { fields.push('theme = ?'); values.push(data.theme); }
  if (data.timezone !== undefined) { fields.push('timezone = ?'); values.push(data.timezone); }
  if (data.language !== undefined) { fields.push('language = ?'); values.push(data.language); }
  if (data.date_format !== undefined) { fields.push('date_format = ?'); values.push(data.date_format); }
  if (data.notification_config_json !== undefined) { fields.push('notification_config_json = ?'); values.push(data.notification_config_json); }
  if (data.branding_json !== undefined) { fields.push('branding_json = ?'); values.push(data.branding_json); }

  if (fields.length === 0) return getSettings(db, tenantId);

  fields.push('updated_at = ?');
  values.push(now());
  values.push(tenantId);

  return db
    .prepare(`UPDATE workspace_settings SET ${fields.join(', ')} WHERE tenant_id = ? RETURNING *`)
    .bind(...values)
    .first();
}

/** Reset workspace settings to defaults */
async function resetSettings(db: any, tenantId: string): Promise<unknown> {
  return db
    .prepare(
      `UPDATE workspace_settings
       SET workspace_name = NULL, theme = 'system', timezone = 'UTC',
           language = 'en', date_format = 'YYYY-MM-DD',
           notification_config_json = '{"email":true,"slack":false,"webhook":true}',
           branding_json = '{}', updated_at = ?
       WHERE tenant_id = ? RETURNING *`
    )
    .bind(now(), tenantId)
    .first();
}

// ---------------------------------------------------------------------------
// Invitations
// ---------------------------------------------------------------------------

/** List all invitations for a tenant */
async function listInvitations(db: any, tenantId: string): Promise<unknown[]> {
  const rows = await db
    .prepare('SELECT * FROM workspace_invitations WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all();
  return rows.results;
}

/** Create a workspace invitation */
async function createInvitation(
  db: any,
  tenantId: string,
  data: { email: string; role?: string; invited_by?: string; expires_at?: string }
): Promise<unknown> {
  return db
    .prepare(
      `INSERT INTO workspace_invitations (id, tenant_id, email, role, invited_by, expires_at)
       VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
    )
    .bind(newId(), tenantId, data.email, data.role ?? 'member', data.invited_by ?? null, data.expires_at ?? null)
    .first();
}

/** Cancel (delete) an invitation by ID for a tenant */
async function cancelInvitation(db: any, tenantId: string, id: string): Promise<boolean> {
  const r = await db
    .prepare('DELETE FROM workspace_invitations WHERE id = ? AND tenant_id = ?')
    .bind(id, tenantId)
    .run();
  return (r.meta?.changes ?? 0) > 0;
}

/** Accept an invitation (set status = accepted) */
async function acceptInvitation(db: any, invitationId: string): Promise<unknown | null> {
  const inv = await db
    .prepare('SELECT * FROM workspace_invitations WHERE id = ? AND status = ?')
    .bind(invitationId, 'pending')
    .first();
  if (!inv) return null;

  return db
    .prepare(`UPDATE workspace_invitations SET status = 'accepted' WHERE id = ? RETURNING *`)
    .bind(invitationId)
    .first();
}

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

/** Admin overview: settings count, invitations by status */
async function getAdminOverview(db: any): Promise<unknown> {
  const [settings, invitations] = await Promise.all([
    db.prepare('SELECT COUNT(*) AS total FROM workspace_settings').first(),
    db.prepare(
      `SELECT status, COUNT(*) AS count FROM workspace_invitations GROUP BY status`
    ).all(),
  ]);
  return {
    total_workspaces: (settings as any)?.total ?? 0,
    invitations_by_status: (invitations as any).results ?? [],
  };
}

export const tenantWorkspaceSettingsService = {
  getSettings,
  updateSettings,
  resetSettings,
  listInvitations,
  createInvitation,
  cancelInvitation,
  acceptInvitation,
  getAdminOverview,
};
