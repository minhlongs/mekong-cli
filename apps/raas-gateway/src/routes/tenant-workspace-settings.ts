/**
 * Tenant Workspace Settings routes
 *
 * Tenant (auth):
 *   GET  /settings             — getSettings
 *   PUT  /settings             — updateSettings
 *   POST /settings/reset       — resetSettings
 *   GET  /invitations          — listInvitations
 *   POST /invitations          — createInvitation
 *   DELETE /invitations/:id    — cancelInvitation
 *
 * Public:
 *   POST /invitations/:id/accept — acceptInvitation
 *
 * Admin (X-Admin-Key):
 *   GET  /admin/overview       — getAdminOverview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantWorkspaceSettingsService as svc } from '../services/tenant-workspace-settings-service';

const app = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

// ---------------------------------------------------------------------------
// GET /settings — tenant workspace settings
// ---------------------------------------------------------------------------

app.get('/settings', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const settings = await svc.getSettings(c.env.DB, tenantId);
    return json({ settings });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// PUT /settings — update workspace settings
// ---------------------------------------------------------------------------

app.put('/settings', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  try {
    const settings = await svc.updateSettings(c.env.DB, tenantId, {
      workspace_name: body.workspace_name as string | undefined,
      theme: body.theme as string | undefined,
      timezone: body.timezone as string | undefined,
      language: body.language as string | undefined,
      date_format: body.date_format as string | undefined,
      notification_config_json: body.notification_config_json as string | undefined,
      branding_json: body.branding_json as string | undefined,
    });
    return json({ settings });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// POST /settings/reset — reset to defaults
// ---------------------------------------------------------------------------

app.post('/settings/reset', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const settings = await svc.resetSettings(c.env.DB, tenantId);
    if (!settings) return json({ error: 'Settings not found' }, { status: 404 });
    return json({ settings, reset: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// GET /invitations — list invitations
// ---------------------------------------------------------------------------

app.get('/invitations', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const invitations = await svc.listInvitations(c.env.DB, tenantId);
    return json({ invitations, count: invitations.length });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// POST /invitations — create invitation
// ---------------------------------------------------------------------------

app.post('/invitations', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try { body = await c.req.json(); } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }
  if (!body.email) return json({ error: 'email is required', code: 'BAD_REQUEST' }, { status: 400 });
  try {
    const invitation = await svc.createInvitation(c.env.DB, tenantId, {
      email: body.email as string,
      role: body.role as string | undefined,
      invited_by: body.invited_by as string | undefined,
      expires_at: body.expires_at as string | undefined,
    });
    return json({ invitation }, { status: 201 });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// DELETE /invitations/:id — cancel invitation
// ---------------------------------------------------------------------------

app.delete('/invitations/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const deleted = await svc.cancelInvitation(c.env.DB, tenantId, c.req.param('id'));
    if (!deleted) return json({ error: 'Invitation not found' }, { status: 404 });
    return json({ deleted: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// POST /invitations/:id/accept — public accept
// ---------------------------------------------------------------------------

app.post('/invitations/:id/accept', async (c) => {
  try {
    const invitation = await svc.acceptInvitation(c.env.DB, c.req.param('id'));
    if (!invitation) return json({ error: 'Invitation not found or already accepted' }, { status: 404 });
    return json({ invitation, accepted: true });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// GET /admin/overview — admin summary
// ---------------------------------------------------------------------------

app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  try {
    const overview = await svc.getAdminOverview(c.env.DB);
    return json({ overview });
  } catch (e: unknown) {
    return json({ error: (e as Error).message }, { status: 500 });
  }
});

export { app as tenantWorkspaceSettings };
