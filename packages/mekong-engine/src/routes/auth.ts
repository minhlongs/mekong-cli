import { Hono } from 'hono'
import { z } from 'zod'
import { sign } from 'hono/jwt'
import type { Bindings } from '../index'
import { validateLicenseKey } from '../raas/license-keys'

const ACCESS_TOKEN_TTL_SECONDS = 60 * 60 // 1h

const loginSchema = z.object({
  license_key: z.string().min(8).max(512),
})

export const authRoutes = new Hono<{ Bindings: Bindings }>()

// POST /auth/login — exchange a license key for a short-lived JWT.
authRoutes.post('/login', async (c) => {
  const body = await c.req.json().catch(() => null)
  const parsed = loginSchema.safeParse(body)
  if (!parsed.success) {
    return c.json({ error: 'invalid_request', details: parsed.error.issues }, 400)
  }

  if (!c.env.DB) {
    return c.json({ error: 'database_unavailable' }, 503)
  }

  const result = await validateLicenseKey(c.env.DB, parsed.data.license_key)
  if (!result) {
    return c.json({ error: 'invalid_license' }, 401)
  }
  if (result.status !== 'active') {
    return c.json({ error: 'license_inactive', status: result.status }, 402)
  }

  const secret = c.env.JWT_SECRET
  if (!secret) {
    return c.json({ error: 'auth_misconfigured' }, 500)
  }

  const now = Math.floor(Date.now() / 1000)
  const payload = {
    tenant_id: result.tenantId,
    license_status: result.status,
    iat: now,
    exp: now + ACCESS_TOKEN_TTL_SECONDS,
  }
  const token = await sign(payload, secret, 'HS256')

  return c.json({
    access_token: token,
    token_type: 'Bearer',
    expires_in: ACCESS_TOKEN_TTL_SECONDS,
    tenant_id: result.tenantId,
  })
})
