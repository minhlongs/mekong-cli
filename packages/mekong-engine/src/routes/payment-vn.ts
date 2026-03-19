import { Hono } from 'hono'
import type { Bindings } from '../index'
import { addCredits } from '../raas/credits'

const paymentVnRoutes = new Hono<{ Bindings: Bindings }>()

// VND pricing tiers
const PRICING_VN = [
  { id: 'free', name: 'Miễn phí', price_vnd: 0, credits: 10, description: 'Dùng thử' },
  { id: 'starter', name: 'Starter', price_vnd: 199_000, credits: 50, description: 'Cá nhân' },
  { id: 'pro', name: 'Pro', price_vnd: 499_000, credits: 200, description: 'Nhóm nhỏ' },
  { id: 'enterprise', name: 'Enterprise', price_vnd: 2_990_000, credits: 1000, description: 'Doanh nghiệp' },
]

// Plan → tier upgrade mapping
const PLAN_TIER_MAP: Record<string, string> = {
  starter: 'pro',
  pro: 'pro',
  enterprise: 'enterprise',
}

// POST /momo/ipn — MoMo Instant Payment Notification
paymentVnRoutes.post('/momo/ipn', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  let body: {
    partnerCode?: string
    orderId?: string
    amount?: number
    resultCode?: number
    extraData?: string
    signature?: string
  }

  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  const { partnerCode, orderId, amount, resultCode, extraData } = body

  // MoMo: resultCode 0 = success
  if (resultCode !== 0) {
    return c.json({ received: true, status: 'ignored', reason: 'non-zero resultCode' })
  }

  if (!extraData) {
    return c.json({ error: 'Missing extraData' }, 400)
  }

  let parsed: { tenant_id?: string; credits?: number; plan?: string }
  try {
    parsed = JSON.parse(atob(extraData))
  } catch {
    return c.json({ error: 'Invalid extraData encoding' }, 400)
  }

  const { tenant_id, credits, plan } = parsed

  if (!tenant_id || !credits) {
    return c.json({ error: 'Missing tenant_id or credits in extraData' }, 400)
  }

  const reason = `MoMo: order ${orderId ?? 'unknown'}, ${amount ?? 0}đ`
  await addCredits(c.env.DB, tenant_id, credits, reason)

  if (plan && PLAN_TIER_MAP[plan]) {
    await c.env.DB
      .prepare('UPDATE tenants SET tier = ? WHERE id = ?')
      .bind(PLAN_TIER_MAP[plan], tenant_id)
      .run()
  }

  return c.json({ received: true, tenant_id, credits_added: credits })
})

// GET /vnpay/ipn — VNPAY Return + IPN handler
paymentVnRoutes.get('/vnpay/ipn', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)

  const responseCode = c.req.query('vnp_ResponseCode')
  const orderInfo = c.req.query('vnp_OrderInfo') // "tenant_id|credits|plan"
  const txnRef = c.req.query('vnp_TxnRef')
  const amount = c.req.query('vnp_Amount') // VNPAY amount = actual * 100

  if (responseCode !== '00') {
    return c.json({ received: true, status: 'ignored', reason: 'payment not successful' })
  }

  if (!orderInfo) {
    return c.json({ error: 'Missing vnp_OrderInfo' }, 400)
  }

  const parts = orderInfo.split('|')
  const tenant_id = parts[0]
  const credits = parseInt(parts[1] ?? '0', 10)
  const plan = parts[2] ?? ''

  if (!tenant_id || !credits) {
    return c.json({ error: 'Invalid vnp_OrderInfo format, expected: tenant_id|credits|plan' }, 400)
  }

  const vndAmount = Math.round(parseInt(amount ?? '0', 10) / 100)
  const reason = `VNPAY: txn ${txnRef ?? 'unknown'}, ${vndAmount}đ`
  await addCredits(c.env.DB, tenant_id, credits, reason)

  if (plan && PLAN_TIER_MAP[plan]) {
    await c.env.DB
      .prepare('UPDATE tenants SET tier = ? WHERE id = ?')
      .bind(PLAN_TIER_MAP[plan], tenant_id)
      .run()
  }

  return c.json({ received: true, tenant_id, credits_added: credits })
})

// POST /create — Create payment URL (mock)
paymentVnRoutes.post('/create', async (c) => {
  let body: {
    method?: string
    tenant_id?: string
    plan?: string
    amount?: number
    credits?: number
  }

  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }

  const { method, tenant_id, plan, amount, credits } = body

  if (!method || !tenant_id || !amount || !credits) {
    return c.json({ error: 'Missing required fields: method, tenant_id, amount, credits' }, 400)
  }

  if (!['momo', 'vnpay'].includes(method)) {
    return c.json({ error: 'Invalid method, use: momo or vnpay' }, 400)
  }

  const orderId = `${tenant_id}-${Date.now()}`

  if (method === 'momo') {
    const extraData = btoa(JSON.stringify({ tenant_id, credits, plan: plan ?? '' }))
    return c.json({
      method: 'momo',
      order_id: orderId,
      amount,
      payment_url: `https://payment.momo.vn/pay?partnerCode=MEKONG&orderId=${orderId}&amount=${amount}&extraData=${extraData}`,
      note: 'Mock URL — replace with real MoMo API integration',
    })
  }

  // VNPAY
  const orderInfo = `${tenant_id}|${credits}|${plan ?? ''}`
  const vnpAmount = amount * 100 // VNPAY requires amount * 100
  return c.json({
    method: 'vnpay',
    order_id: orderId,
    amount,
    payment_url: `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_TxnRef=${orderId}&vnp_Amount=${vnpAmount}&vnp_OrderInfo=${encodeURIComponent(orderInfo)}`,
    note: 'Mock URL — replace with real VNPAY API integration',
  })
})

// GET /pricing-vn — VND pricing tiers
paymentVnRoutes.get('/pricing-vn', (c) => {
  return c.json({ tiers: PRICING_VN })
})

export { paymentVnRoutes }
