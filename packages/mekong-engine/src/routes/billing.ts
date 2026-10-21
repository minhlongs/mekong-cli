import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import type { Variables } from '../raas/auth-middleware'
import { authMiddleware } from '../raas/auth-middleware'
import { getBalance, getHistory, addCredits } from '../raas/credits'
import { createTenant, regenerateApiKey } from '../raas/tenant'
import { z } from 'zod'
import { handleAsync } from '../types/error'
import { authRateLimit } from '../raas/rate-limit-middleware'
import { constantTimeCompare } from '../lib/crypto-utils'
import {
  PilotInviteError,
  isPilotModeEnabled,
  issuePilotInviteCode,
  listPilotInvites,
  redeemInviteAndCreateTenant,
} from '../raas/invite-codes'
import { getPilotKpiSummary } from '../raas/mission-feedback'
import { registerBillingWebhookRoutes } from './billing-webhook'
import { registerBillingLicenseRoutes } from './billing-licenses'

const billingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

const createTenantSchema = z.object({
  name: z.string().min(1, 'Tenant name is required').trim(),
  invite_code: z.string().min(1).max(128).optional(),
})

const issueInviteSchema = z.object({
  partner_label: z.string().min(1).max(120).optional(),
})

const regenerateKeySchema = z.object({
  tenant_id: z.string().min(1, 'Tenant ID is required').trim(),
  name: z.string().min(1, 'Tenant name is required').trim(),
})

function verifyOperatorToken(authHeader: string | undefined, serviceToken: string | undefined): boolean {
  if (!authHeader?.startsWith('Bearer ') || !serviceToken) return false
  const provided = authHeader.slice(7).trim()
  return constantTimeCompare(provided, serviceToken)
}

billingRoutes.post('/invites', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  if (!verifyOperatorToken(c.req.header('Authorization'), c.env.SERVICE_TOKEN)) {
    return c.json({ error: 'Unauthorized - SERVICE_TOKEN required', code: 'UNAUTHORIZED' }, 401)
  }

  const parsed = issueInviteSchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) {
    return c.json({ error: parsed.error.errors[0]?.message || 'Invalid request' }, 400)
  }

  const maxInvites = Number(c.env.PILOT_MAX_INVITES || '5') || 5
  try {
    const { invite, inviteCode } = await issuePilotInviteCode(c.env.DB, {
      partnerLabel: parsed.data.partner_label,
      maxInvites,
      issuedBy: 'operator',
    })
    return c.json({
      invite_id: invite.id,
      invite_code: inviteCode,
      code_hash: invite.code_hash,
      partner_label: invite.partner_label,
      status: invite.status,
      max_invites: maxInvites,
      message: 'Save this invite_code now — only its SHA-256 hash is stored.',
    }, 201)
  } catch (err) {
    if (err instanceof PilotInviteError) {
      return c.json({ error: err.message, code: err.code }, err.statusCode)
    }
    throw err
  }
}))

billingRoutes.get('/invites', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  if (!verifyOperatorToken(c.req.header('Authorization'), c.env.SERVICE_TOKEN)) {
    return c.json({ error: 'Unauthorized - SERVICE_TOKEN required', code: 'UNAUTHORIZED' }, 401)
  }

  const invites = await listPilotInvites(c.env.DB)
  const maxInvites = Number(c.env.PILOT_MAX_INVITES || '5') || 5
  return c.json({
    invites,
    total_issued: invites.filter((i) => i.status !== 'revoked').length,
    max_invites: maxInvites,
  })
}))

billingRoutes.get('/pilot-kpis', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  if (!verifyOperatorToken(c.req.header('Authorization'), c.env.SERVICE_TOKEN)) {
    return c.json({ error: 'Unauthorized - SERVICE_TOKEN required', code: 'UNAUTHORIZED' }, 401)
  }
  const maxPartners = Number(c.env.PILOT_MAX_INVITES || '5') || 5
  const summary = await getPilotKpiSummary(c.env.DB, maxPartners)
  return c.json(summary)
}))

billingRoutes.post('/tenants', handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const parsed = createTenantSchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) return c.json({ error: parsed.error.errors[0]?.message || 'Invalid request' }, 400)

  if (isPilotModeEnabled(c.env.PILOT_MODE)) {
    try {
      const { tenant, apiKey, inviteId, initialCredits } = await redeemInviteAndCreateTenant(
        c.env.DB,
        parsed.data.invite_code,
        parsed.data.name,
      )
      return c.json({
        tenant_id: tenant.id,
        name: tenant.name,
        api_key: apiKey,
        tier: tenant.tier,
        credits: initialCredits,
        invite_id: inviteId,
        message: 'Save your API key - it cannot be recovered if lost!',
      }, 201)
    } catch (err) {
      if (err instanceof PilotInviteError) {
        return c.json({ error: err.message, code: err.code }, err.statusCode)
      }
      throw err
    }
  }

  const { tenant, apiKey } = await createTenant(c.env.DB, parsed.data.name)
  await addCredits(c.env.DB, tenant.id, 10, 'welcome: free tier bonus')
  return c.json({
    tenant_id: tenant.id, name: tenant.name, api_key: apiKey, tier: tenant.tier,
    credits: 10, message: 'Save your API key - it cannot be recovered if lost!',
  }, 201)
}))

billingRoutes.post('/tenants/regenerate-key', authRateLimit(), handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const parsed = regenerateKeySchema.safeParse(await c.req.json().catch(() => ({})))
  if (!parsed.success) return c.json({ error: parsed.error.errors[0]?.message || 'Invalid request' }, 400)
  const result = await regenerateApiKey(c.env.DB, parsed.data.tenant_id, parsed.data.name)
  if (!result) return c.json({ error: 'Tenant not found or name mismatch' }, 404)
  return c.json({
    api_key: result.apiKey,
    message: 'New API key generated. Old key is now invalid. Save this key!',
  })
}))

billingRoutes.get('/pricing', handleAsync(async (c) => {
  return c.json({
    tiers: [
      { id: 'free', name: 'Free', price: 0, credits: 10, description: 'Try it out' },
      { id: 'agencyos-starter', name: 'Starter', price: 29, credits: 50, description: 'Solo non-tech user' },
      { id: 'agencyos-pro', name: 'Pro', price: 99, credits: 200, description: 'Small agency' },
      { id: 'agencyos-agency', name: 'Agency', price: 199, credits: 500, description: 'Growing agency' },
      { id: 'agencyos-master', name: 'Master', price: 399, credits: 1000, description: 'Premium agency' },
    ],
    credit_packs: [
      { id: 'credits-10', credits: 10, price: 5 },
      { id: 'credits-50', credits: 50, price: 20 },
      { id: 'credits-100', credits: 100, price: 35 },
      { id: 'credits-500', credits: 500, price: 150 },
    ],
    credit_costs: { simple: 1, standard: 3, complex: 5 },
  })
}))

billingRoutes.get('/credits', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const balance = await getBalance(c.env.DB, tenant.id)
  return c.json({ tenant_id: tenant.id, balance, tier: tenant.tier })
}))

billingRoutes.get('/credits/history', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant') as Tenant
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '50', 10) || 50, 1), 200)
  const history = await getHistory(c.env.DB, tenant.id, limit)
  return c.json({ tenant_id: tenant.id, history, limit })
}))

registerBillingWebhookRoutes(billingRoutes)
registerBillingLicenseRoutes(billingRoutes)

export { billingRoutes }
