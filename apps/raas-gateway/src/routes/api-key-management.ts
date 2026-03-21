/**
 * API key management routes — CRUD + rotate for tenant API keys
 * POST   /v1/api-keys          create key with scope
 * GET    /v1/api-keys          list keys (masked)
 * GET    /v1/api-keys/:id      single key detail
 * PUT    /v1/api-keys/:id      update name/scope/description
 * DELETE /v1/api-keys/:id      revoke (soft delete)
 * POST   /v1/api-keys/:id/rotate  rotate — create new, revoke old
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const apiKeyManagement = new Hono<{ Bindings: Env }>();

// All routes require auth
apiKeyManagement.use('*', auth());

/** Generate a raw API key + its SHA-256 hash */
async function generateKey(): Promise<{ raw: string; hash: string }> {
  const keyBytes = new Uint8Array(32);
  crypto.getRandomValues(keyBytes);
  const raw = 'rk_' + Array.from(keyBytes).map((b) => b.toString(16).padStart(2, '0')).join('');
  const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
  const hash = Array.from(new Uint8Array(hashBuffer)).map((b) => b.toString(16).padStart(2, '0')).join('');
  return { raw, hash };
}

/** Mask key — show prefix + last 4 chars of the raw key */
function maskKey(keyHint: string): string {
  return `rk_${'*'.repeat(12)}${keyHint}`;
}

type Scope = 'read' | 'write' | 'admin';
const VALID_SCOPES: Scope[] = ['read', 'write', 'admin'];

// POST /v1/api-keys — create
apiKeyManagement.post('/', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    name?: string; scope?: string; description?: string; expires_at?: string;
  };

  const name = body.name?.trim();
  if (!name) return json({ error: 'name is required', code: 'VALIDATION_ERROR' }, { status: 400 });

  const scope: Scope = VALID_SCOPES.includes(body.scope as Scope) ? (body.scope as Scope) : 'write';
  const { raw, hash } = await generateKey();
  const id = crypto.randomUUID();
  const keyHint = raw.slice(-4);

  await c.env.DB.prepare(
    `INSERT INTO api_keys (id, tenant_id, key_hash, name, scope, description, expires_at, permissions, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
  ).bind(id, tenant.tenantId, hash, name, scope, body.description ?? null, body.expires_at ?? null,
    JSON.stringify([`scope:${scope}`])).run();

  return json({ id, name, scope, description: body.description ?? null,
    expires_at: body.expires_at ?? null, key: raw,
    hint: 'Store this key securely — it will not be shown again' }, { status: 201 });
});

// GET /v1/api-keys — list (masked)
apiKeyManagement.get('/', async (c) => {
  const tenant = getTenant(c);
  const rows = await c.env.DB.prepare(
    `SELECT id, name, scope, description, expires_at, created_at, last_used_at, revoked,
            substr(key_hash, -4) as key_hint
     FROM api_keys WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenant.tenantId).all<any>();

  const keys = (rows.results ?? []).map((r) => ({
    id: r.id, name: r.name, scope: r.scope ?? 'write',
    description: r.description, expires_at: r.expires_at,
    created_at: r.created_at, last_used_at: r.last_used_at,
    revoked: Boolean(r.revoked), key_masked: maskKey(r.key_hint),
  }));

  return json({ keys, total: keys.length });
});

// GET /v1/api-keys/:id — single
apiKeyManagement.get('/:id', async (c) => {
  const tenant = getTenant(c);
  const row = await c.env.DB.prepare(
    `SELECT id, name, scope, description, expires_at, created_at, last_used_at, revoked,
            substr(key_hash, -4) as key_hint
     FROM api_keys WHERE id = ? AND tenant_id = ?`
  ).bind(c.req.param('id'), tenant.tenantId).first<any>();

  if (!row) return json({ error: 'API key not found', code: 'NOT_FOUND' }, { status: 404 });

  return json({ id: row.id, name: row.name, scope: row.scope ?? 'write',
    description: row.description, expires_at: row.expires_at,
    created_at: row.created_at, last_used_at: row.last_used_at,
    revoked: Boolean(row.revoked), key_masked: maskKey(row.key_hint) });
});

// PUT /v1/api-keys/:id — update
apiKeyManagement.put('/:id', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    name?: string; scope?: string; description?: string;
  };

  const existing = await c.env.DB.prepare(
    'SELECT id FROM api_keys WHERE id = ? AND tenant_id = ? AND revoked = 0'
  ).bind(c.req.param('id'), tenant.tenantId).first<any>();
  if (!existing) return json({ error: 'API key not found', code: 'NOT_FOUND' }, { status: 404 });

  const scope = VALID_SCOPES.includes(body.scope as Scope) ? body.scope : undefined;
  const fields: string[] = [];
  const binds: unknown[] = [];
  if (body.name?.trim()) { fields.push('name = ?'); binds.push(body.name.trim()); }
  if (scope) {
    fields.push('scope = ?', 'permissions = ?');
    binds.push(scope, JSON.stringify([`scope:${scope}`]));
  }
  if ('description' in body) { fields.push('description = ?'); binds.push(body.description ?? null); }
  if (!fields.length) return json({ error: 'No fields to update', code: 'VALIDATION_ERROR' }, { status: 400 });

  binds.push(c.req.param('id'), tenant.tenantId);
  await c.env.DB.prepare(
    `UPDATE api_keys SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`
  ).bind(...binds).run();

  return json({ success: true });
});

// DELETE /v1/api-keys/:id — revoke (soft)
apiKeyManagement.delete('/:id', async (c) => {
  const tenant = getTenant(c);
  const result = await c.env.DB.prepare(
    'UPDATE api_keys SET revoked = 1 WHERE id = ? AND tenant_id = ? AND revoked = 0'
  ).bind(c.req.param('id'), tenant.tenantId).run();

  if (!result.meta?.changes) return json({ error: 'API key not found', code: 'NOT_FOUND' }, { status: 404 });
  return json({ success: true, message: 'API key revoked' });
});

// POST /v1/api-keys/:id/rotate — rotate key
apiKeyManagement.post('/:id/rotate', async (c) => {
  const tenant = getTenant(c);
  const old = await c.env.DB.prepare(
    'SELECT id, name, scope, description FROM api_keys WHERE id = ? AND tenant_id = ? AND revoked = 0'
  ).bind(c.req.param('id'), tenant.tenantId).first<any>();
  if (!old) return json({ error: 'API key not found', code: 'NOT_FOUND' }, { status: 404 });

  const { raw, hash } = await generateKey();
  const newId = crypto.randomUUID();
  const scope: Scope = (old.scope as Scope) ?? 'write';

  await c.env.DB.batch([
    c.env.DB.prepare('UPDATE api_keys SET revoked = 1 WHERE id = ?').bind(old.id),
    c.env.DB.prepare(
      `INSERT INTO api_keys (id, tenant_id, key_hash, name, scope, description, permissions, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))`
    ).bind(newId, tenant.tenantId, hash, old.name, scope, old.description ?? null,
      JSON.stringify([`scope:${scope}`])),
  ]);

  return json({ id: newId, name: old.name, scope, key: raw,
    hint: 'Previous key has been revoked — store this new key securely' }, { status: 201 });
});
