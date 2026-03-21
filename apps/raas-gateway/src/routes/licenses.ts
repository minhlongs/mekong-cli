/**
 * License key management routes for source code access sales
 * Public: GET /verify/:key, POST /activate/:key
 * Auth required: POST / (create), GET / (list)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const licenses = new Hono<{ Bindings: Env }>();

// License types with pricing (cents)
const LICENSE_TYPES = {
  personal:   { price: 4900,  maxActivations: 1,  validYears: 1  },
  team:        { price: 19900, maxActivations: 5,  validYears: 2  },
  enterprise:  { price: 99900, maxActivations: -1, validYears: -1 }, // unlimited
  oem:         { price: 0,     maxActivations: -1, validYears: -1 }, // custom pricing
} as const;

type LicenseType = keyof typeof LICENSE_TYPES;

// Generate license key: MEKONG-XXXX-XXXX-XXXX
function generateKey(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  const seg = () => Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  return `MEKONG-${seg()}-${seg()}-${seg()}`;
}

// POST /v1/licenses — Generate license (auth required)
licenses.post('/', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, string>;
  const type = body.type as LicenseType;

  if (!LICENSE_TYPES[type]) {
    return json({ error: 'Invalid license type', types: Object.keys(LICENSE_TYPES) }, { status: 400 });
  }

  const config = LICENSE_TYPES[type];
  const key = generateKey();
  const id = crypto.randomUUID();
  const expiresAt = config.validYears > 0
    ? new Date(Date.now() + config.validYears * 365 * 24 * 60 * 60 * 1000).toISOString()
    : null;

  await c.env.DB.prepare(
    `INSERT INTO licenses (id, license_key, type, owner_email, owner_name, max_activations, expires_at, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))`
  ).bind(id, key, type, body.email || tenant.tenantId, body.name || '', config.maxActivations, expiresAt).run();

  return json({ licenseKey: key, type, expiresAt, maxActivations: config.maxActivations }, { status: 201 });
});

// GET /v1/licenses/verify/:key — Public: verify a license key
licenses.get('/verify/:key', async (c) => {
  const key = c.req.param('key');

  const license = await c.env.DB.prepare(
    'SELECT * FROM licenses WHERE license_key = ?'
  ).bind(key).first<Record<string, unknown>>();

  if (!license) return json({ valid: false, error: 'License not found' }, { status: 404 });
  if (license.status === 'revoked') return json({ valid: false, error: 'License revoked' });
  if (license.expires_at && new Date(license.expires_at as string) < new Date()) {
    return json({ valid: false, error: 'License expired' });
  }

  return json({
    valid: true,
    type: license.type,
    activations: { current: license.current_activations, max: license.max_activations },
    expiresAt: license.expires_at,
  });
});

// POST /v1/licenses/activate/:key — Public: activate a license (increment counter)
licenses.post('/activate/:key', async (c) => {
  const key = c.req.param('key');

  const license = await c.env.DB.prepare(
    "SELECT * FROM licenses WHERE license_key = ? AND status = 'active'"
  ).bind(key).first<Record<string, unknown>>();

  if (!license) return json({ error: 'Invalid or inactive license' }, { status: 404 });

  const maxAct = license.max_activations as number;
  const curAct = license.current_activations as number;

  if (maxAct > 0 && curAct >= maxAct) {
    return json({ error: 'Activation limit reached', max: maxAct }, { status: 403 });
  }

  await c.env.DB.prepare(
    "UPDATE licenses SET current_activations = current_activations + 1, activated_at = datetime('now') WHERE id = ?"
  ).bind(license.id).run();

  return json({ activated: true, activations: curAct + 1, max: maxAct });
});

// GET /v1/licenses — List licenses owned by tenant (auth required)
licenses.get('/', auth(), async (c) => {
  const tenant = getTenant(c);

  const result = await c.env.DB.prepare(
    `SELECT id, license_key, type, status, current_activations, max_activations, expires_at, created_at
     FROM licenses WHERE owner_email = ? ORDER BY created_at DESC`
  ).bind(tenant.tenantId).all();

  return json({ licenses: result.results });
});
