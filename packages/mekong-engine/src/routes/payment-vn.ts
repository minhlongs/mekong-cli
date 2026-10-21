import { Hono, type Context } from 'hono'
import type { Bindings } from '../index'
import { PRICING_VN } from './payment-vn-helpers'

const paymentVnRoutes = new Hono<{ Bindings: Bindings }>()

const paymentSandboxOnly = (c: Context<{ Bindings: Bindings }>) => c.json({
  error: {
    code: 'PAYMENT_SANDBOX_ONLY',
    message: 'Payment checkout and webhook crediting are disabled until a verified sandbox integration is available.',
  },
}, 503)

// These provider paths were mock implementations: checkout URLs were not
// signed and webhook callbacks could credit accounts without signature checks.
// Fail closed until provider signing, order storage, amount checks, and
// idempotency are implemented and exercised in a real sandbox.
paymentVnRoutes.post('/momo/ipn', paymentSandboxOnly)
paymentVnRoutes.get('/vnpay/ipn', paymentSandboxOnly)
paymentVnRoutes.post('/create', paymentSandboxOnly)

paymentVnRoutes.get('/pricing-vn', (c) => c.json({ tiers: PRICING_VN }))

export { paymentVnRoutes }
