import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import { addCredits } from '../raas/credits'
import { handleAsync, handleDb, createError, validateJsonBody } from '../types/error'
import { constantTimeCompare, encryptPaymentMetadata, decryptPaymentMetadata } from '../lib/crypto-utils'

const paymentVnRoutes = new Hono<{ Bindings: Bindings }>()

// Zod schemas for payment operations
const createPaymentSchema = z.object({
  method: z.enum(['momo', 'vnpay']),
  tenant_id: z.string().min(1, 'tenant_id is required'),
  amount: z.number().positive('amount must be positive').max(1_000_000_000, 'amount too large'),
  credits: z.number().int().positive('credits must be positive').max(1_000_000, 'credits too large'),
  plan: z.enum(['starter', 'pro', 'enterprise']).optional(),
})

// MoMo webhook payload schema
const momoWebhookSchema = z.object({
  partnerCode: z.string().optional(),
  orderId: z.string().optional(),
  amount: z.number().optional(),
  resultCode: z.number(),
  extraData: z.string().optional(),
  signature: z.string().optional(),
})
type MomoWebhookBody = z.infer<typeof momoWebhookSchema>

// VNPAY webhook query schema
const vnpayQuerySchema = z.object({
  vnp_ResponseCode: z.string().optional(),
  vnp_OrderInfo: z.string().optional(),
  vnp_TxnRef: z.string().optional(),
  vnp_Amount: z.string().optional(),
  vnp_SecureHash: z.string().optional().transform((val) => val?.replace('SHA512=', '')),
})

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
paymentVnRoutes.post('/momo/ipn', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const db = c.env.DB

  const secret = c.env.MOMO_SECRET_KEY
  const signature = c.req.header('x-signature') || c.req.header('x-momo-signature')

  // Verify MoMo HMAC signature if secret configured
  if (secret && signature) {
    const rawBody = await c.req.text()
    const expectedSig = await crypto.subtle.sign(
      'HMAC',
      await crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(secret),
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
      ),
      new TextEncoder().encode(rawBody)
    )
    const expectedHex = Array.from(new Uint8Array(expectedSig))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    if (!constantTimeCompare(signature, expectedHex)) {
      return c.json(createError('UNAUTHORIZED', 'Invalid MoMo signature'), 401)
    }
  }

  let body: MomoWebhookBody
  try {
    body = momoWebhookSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid MoMo webhook payload', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const { partnerCode, orderId, amount, resultCode, extraData } = body

  // MoMo: resultCode 0 = success
  if (resultCode !== 0) {
    return c.json({ received: true, status: 'ignored', reason: 'non-zero resultCode' })
  }

  if (!extraData) {
    return c.json(createError('VALIDATION_ERROR', 'Missing extraData'), 400)
  }

  let parsed: { tenant_id?: string; credits?: number; plan?: string }
  try {
    // Use encrypted decryption for payment metadata
    const metadataSecret = c.env.PAYMENT_METADATA_SECRET || c.env.MOMO_SECRET_KEY || 'fallback-secret'
    parsed = await decryptPaymentMetadata(extraData, metadataSecret)
  } catch {
    return c.json(createError('VALIDATION_ERROR', 'Invalid extraData encoding'), 400)
  }

  const { tenant_id, credits, plan } = parsed

  if (!tenant_id || !credits) {
    return c.json(createError('VALIDATION_ERROR', 'Missing tenant_id or credits in extraData'), 400)
  }

  const reason = `MoMo: order ${orderId ?? 'unknown'}, ${amount ?? 0}đ`
  await handleDb(
    () => addCredits(db, tenant_id, credits, reason),
    'DATABASE_ERROR',
    'Failed to add credits from MoMo payment'
  )

  if (plan && PLAN_TIER_MAP[plan]) {
    await handleDb(
      () => db
        .prepare('UPDATE tenants SET tier = ? WHERE id = ?')
        .bind(PLAN_TIER_MAP[plan], tenant_id)
        .run(),
      'DATABASE_ERROR',
      'Failed to upgrade tenant tier'
    )
  }

  return c.json({ received: true, tenant_id, credits_added: credits })
}))

// GET /vnpay/ipn — VNPAY Return + IPN handler
paymentVnRoutes.get('/vnpay/ipn', handleAsync(async (c) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 not configured'), 503)
  const db = c.env.DB

  const hashSecret = c.env.VNPAY_HASH_SECRET
  const secureHash = c.req.query('vnp_SecureHash')?.replace('SHA512=', '')

  // Verify VNPAY secure hash if secret configured
  if (hashSecret && secureHash) {
    const params = c.req.query()
    // Build hash string from sorted query params (exclude vnp_SecureHash itself)
    const hashParams = Object.entries(params)
      .filter(([key]) => key !== 'vnp_SecureHash')
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v ?? ''}`)
      .join('&')

    const expectedHash = await crypto.subtle.sign(
      'HMAC',
      await crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(hashSecret),
        { name: 'HMAC', hash: 'SHA-512' },
        false,
        ['sign']
      ),
      new TextEncoder().encode(hashParams)
    )
    const expectedHex = Array.from(new Uint8Array(expectedHash))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')

    // Constant-time comparison to prevent timing attacks
    if (!constantTimeCompare(secureHash.toLowerCase(), expectedHex.toLowerCase())) {
      return c.json(createError('UNAUTHORIZED', 'Invalid VNPAY signature'), 401)
    }
  }

  // Validate VNPAY query params with Zod
  const queryResult = vnpayQuerySchema.safeParse(c.req.query())
  if (!queryResult.success) {
    return c.json(createError('VALIDATION_ERROR', 'Invalid VNPAY query params', queryResult.error.errors), 400)
  }
  const { vnp_ResponseCode: responseCode, vnp_OrderInfo: orderInfo, vnp_TxnRef: txnRef, vnp_Amount: amount } = queryResult.data as { vnp_ResponseCode?: string; vnp_OrderInfo?: string; vnp_TxnRef?: string; vnp_Amount?: string }

  if (responseCode !== '00') {
    return c.json({ received: true, status: 'ignored', reason: 'payment not successful' })
  }

  if (!orderInfo) {
    return c.json(createError('VALIDATION_ERROR', 'Missing vnp_OrderInfo'), 400)
  }

  const parts = (orderInfo as string).split('|')
  const tenant_id = parts[0]
  const credits = parseInt(parts[1] ?? '0', 10)
  const plan = parts[2] ?? ''

  if (!tenant_id || !credits) {
    return c.json(createError('VALIDATION_ERROR', 'Invalid vnp_OrderInfo format, expected: tenant_id|credits|plan'), 400)
  }

  const vndAmount = Math.round(parseInt((amount as string) ?? '0', 10) / 100)
  const reason = `VNPAY: txn ${txnRef ?? 'unknown'}, ${vndAmount}đ`
  await handleDb(
    () => addCredits(db, tenant_id, credits, reason),
    'DATABASE_ERROR',
    'Failed to add credits from VNPAY payment'
  )

  if (plan && PLAN_TIER_MAP[plan]) {
    await handleDb(
      () => db
        .prepare('UPDATE tenants SET tier = ? WHERE id = ?')
        .bind(PLAN_TIER_MAP[plan], tenant_id)
        .run(),
      'DATABASE_ERROR',
      'Failed to upgrade tenant tier'
    )
  }

  return c.json({ received: true, tenant_id, credits_added: credits })
}))

// POST /create — Create payment URL (mock)
paymentVnRoutes.post('/create', handleAsync(async (c) => {
  const body = await validateJsonBody(c, createPaymentSchema)

  const { method, tenant_id, plan, amount, credits } = body

  const orderId = `${tenant_id}-${Date.now()}`
  const vnpAmount = amount * 100 // VNPAY requires amount * 100

  if (method === 'momo') {
    // Use encrypted metadata instead of base64
    const metadataSecret = c.env.PAYMENT_METADATA_SECRET || c.env.MOMO_SECRET_KEY || 'fallback-secret'
    const extraData = await encryptPaymentMetadata({ tenant_id, credits, plan: plan ?? '' }, metadataSecret)
    return c.json({
      method: 'momo',
      order_id: orderId,
      amount,
      payment_url: `https://payment.momo.vn/pay?partnerCode=MEKONG&orderId=${orderId}&amount=${amount}&extraData=${encodeURIComponent(extraData)}`,
      note: 'Mock URL — replace with real MoMo API integration',
    })
  }

  // VNPAY - Use encrypted metadata
  const metadataSecretVnp = c.env.PAYMENT_METADATA_SECRET || c.env.VNPAY_HASH_SECRET || 'fallback-secret'
  const encryptedMetadata = await encryptPaymentMetadata({ tenant_id, credits, plan: plan ?? '' }, metadataSecretVnp)
  return c.json({
    method: 'vnpay',
    order_id: orderId,
    amount,
    payment_url: `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_TxnRef=${orderId}&vnp_Amount=${vnpAmount}&vnp_OrderInfo=${encodeURIComponent(encryptedMetadata)}`,
    note: 'Mock URL — replace with real VNPAY API integration',
  })
}))

// GET /pricing-vn — VND pricing tiers
paymentVnRoutes.get('/pricing-vn', (c) => {
  return c.json({ tiers: PRICING_VN })
})

export { paymentVnRoutes }
