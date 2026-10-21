import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import type { Variables } from '../raas/auth-middleware'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync } from '../types/error'
import {
  checkLicenseStatus,
  suspendTenant,
  reactivateTenant,
  getDunningSchedule,
  emitLicenseEvent,
} from '../raas/dunning'
import { requireActiveLicense } from '../raas/license-middleware'
import {
  generateLicenseKey,
  validateLicenseKey,
  revokeLicenseKey,
  listLicenseKeys,
  getLicenseKey,
} from '../raas/license-keys'

export function registerBillingLicenseRoutes(billingRoutes: Hono<{ Bindings: Bindings; Variables: Variables }>): void {
  billingRoutes.get('/license/status', authMiddleware, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const status = await checkLicenseStatus(c.env.DB, tenant.id)
    const schedule = await getDunningSchedule(c.env.DB, tenant.id)
    return c.json({ tenant_id: tenant.id, status, schedule })
  }))

  billingRoutes.post('/license/suspend', authMiddleware, requireActiveLicense, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const body = (await c.req.json().catch(() => ({}))) as { reason?: string }
    const reason = body.reason || 'Suspended by admin'

    const success = await suspendTenant(c.env.DB, tenant.id, reason)
    if (!success) return c.json({ error: 'Failed to suspend tenant' }, 500)

    await emitLicenseEvent(c.env.DB, tenant.id, 'license.suspended', { reason })
    return c.json({ tenant_id: tenant.id, status: 'suspended', reason })
  }))

  billingRoutes.post('/license/reactivate', authMiddleware, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const body = (await c.req.json().catch(() => ({}))) as { tier?: string }
    const tier = body.tier || 'free'

    const success = await reactivateTenant(c.env.DB, tenant.id, tier)
    if (!success) return c.json({ error: 'Failed to reactivate tenant' }, 500)

    await emitLicenseEvent(c.env.DB, tenant.id, 'license.reactivated', { tier })
    return c.json({ tenant_id: tenant.id, status: 'active', tier })
  }))

  billingRoutes.get('/dunning/schedule', authMiddleware, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const schedule = await getDunningSchedule(c.env.DB, tenant.id)
    return c.json({ tenant_id: tenant.id, schedule })
  }))

  billingRoutes.post('/licenses', authMiddleware, requireActiveLicense, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const body = (await c.req.json().catch(() => ({}))) as { expires_at?: string }
    const result = await generateLicenseKey(c.env.DB, tenant.id, body.expires_at)
    if (!result) return c.json({ error: 'Failed to generate license key' }, 500)

    return c.json({
      license_key: result.key,
      license: result.licenseKey,
      message: 'Save your license key - it cannot be recovered if lost!',
    }, 201)
  }))

  billingRoutes.get('/licenses', authMiddleware, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const keys = await listLicenseKeys(c.env.DB, tenant.id)
    return c.json({ tenant_id: tenant.id, licenses: keys })
  }))

  billingRoutes.get('/licenses/:id', authMiddleware, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const keyId = c.req.param('id')
    if (!keyId) return c.json({ error: 'License key ID required' }, 400)
    const key = await getLicenseKey(c.env.DB, keyId)
    if (!key) return c.json({ error: 'License key not found' }, 404)
    return c.json({ license: key })
  }))

  billingRoutes.delete('/licenses/:id', authMiddleware, requireActiveLicense, handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const tenant = c.get('tenant') as Tenant
    const keyId = c.req.param('id')
    if (!keyId) return c.json({ error: 'License key ID required' }, 400)
    const body = (await c.req.json().catch(() => ({}))) as { reason?: string }
    const reason = body.reason || 'Revoked by admin'

    const success = await revokeLicenseKey(c.env.DB, keyId, reason)
    if (!success) return c.json({ error: 'Failed to revoke license key or already revoked' }, 400)

    await emitLicenseEvent(c.env.DB, tenant.id, 'license.suspended', { reason, license_key_id: keyId })
    return c.json({ success: true, message: 'License key revoked' })
  }))

  billingRoutes.post('/licenses/validate', handleAsync(async (c) => {
    if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
    const body = (await c.req.json().catch(() => ({}))) as { key?: string }
    if (!body.key) return c.json({ error: 'License key required' }, 400)

    const result = await validateLicenseKey(c.env.DB, body.key)
    if (!result) return c.json({ valid: false, error: 'Invalid license key' }, 404)

    return c.json({
      valid: true,
      tenant_id: result.tenantId,
      status: result.status,
      expires_at: result.expiresAt,
    })
  }))
}
