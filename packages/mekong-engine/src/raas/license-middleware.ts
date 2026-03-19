import { createMiddleware } from 'hono/factory'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { checkLicenseStatus } from './dunning'

type Variables = { tenant: Tenant }

/**
 * Middleware to check if tenant has active license
 * Blocks suspended/blocked/expired tenants
 */
export const requireActiveLicense = createMiddleware<{ Bindings: Bindings; Variables: Variables }>(
  async (c, next) => {
    const tenant = c.get('tenant')
    if (!tenant) {
      return c.json({ error: 'Authentication required' }, 401)
    }

    if (!c.env.DB) {
      return c.json({ error: 'D1 not configured' }, 503)
    }

    const status = await checkLicenseStatus(c.env.DB, tenant.id)

    if (status === 'suspended' || status === 'blocked') {
      return c.json(
        {
          error: 'Account suspended',
          code: 'ACCOUNT_SUSPENDED',
          message: 'Your account has been suspended. Please contact support or add credits to reactivate.',
        },
        403
      )
    }

    if (status === 'expired') {
      return c.json(
        {
          error: 'Account expired',
          code: 'ACCOUNT_EXPIRED',
          message: 'Your account has expired. Please create a new account or contact support.',
        },
        403
      )
    }

    // Status is 'active' - allow request
    await next()
  },
)
