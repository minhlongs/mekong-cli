import type { D1Database } from '@cloudflare/workers-types'
import { z } from 'zod'
import { constantTimeCompare } from '../lib/crypto-utils'
import { addCredits } from '../raas/credits'
import { handleDb } from '../types/error'

export const createPaymentSchema = z.object({
  method: z.enum(['momo', 'vnpay']),
  tenant_id: z.string().min(1, 'tenant_id is required'),
  amount: z.number().positive('amount must be positive').max(1_000_000_000, 'amount too large'),
  credits: z.number().int().positive('credits must be positive').max(1_000_000, 'credits too large'),
  plan: z.enum(['starter', 'pro', 'enterprise']).optional(),
})

export const momoWebhookSchema = z.object({
  partnerCode: z.string().optional(),
  orderId: z.string().optional(),
  amount: z.number().optional(),
  resultCode: z.number(),
  extraData: z.string().optional(),
  signature: z.string().optional(),
})
export type MomoWebhookBody = z.infer<typeof momoWebhookSchema>

export const vnpayQuerySchema = z.object({
  vnp_ResponseCode: z.string().optional(),
  vnp_OrderInfo: z.string().optional(),
  vnp_TxnRef: z.string().optional(),
  vnp_Amount: z.string().optional(),
  vnp_SecureHash: z.string().optional().transform((val) => val?.replace('SHA512=', '')),
})

export const PRICING_VN = [
  { id: 'free', name: 'Miễn phí', price_vnd: 0, credits: 10, description: 'Dùng thử' },
  { id: 'starter', name: 'Starter', price_vnd: 199_000, credits: 50, description: 'Cá nhân' },
  { id: 'pro', name: 'Pro', price_vnd: 499_000, credits: 200, description: 'Nhóm nhỏ' },
  { id: 'enterprise', name: 'Enterprise', price_vnd: 2_990_000, credits: 1000, description: 'Doanh nghiệp' },
]

export const PLAN_TIER_MAP: Record<string, string> = {
  starter: 'pro',
  pro: 'pro',
  enterprise: 'enterprise',
}

export async function verifyMomoSignature(
  secret: string,
  rawBody: string,
  signature: string,
): Promise<boolean> {
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

  return constantTimeCompare(signature, expectedHex)
}

export async function verifyVnpaySignature(
  hashSecret: string,
  params: Record<string, string>,
  secureHash: string,
): Promise<boolean> {
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

  return constantTimeCompare(secureHash.toLowerCase(), expectedHex.toLowerCase())
}

export async function applyPaymentCreditsAndPlan(
  db: D1Database,
  tenantId: string,
  credits: number,
  reason: string,
  creditErrorMessage: string,
  plan?: string,
): Promise<void> {
  await handleDb(
    () => addCredits(db, tenantId, credits, reason),
    'DATABASE_ERROR',
    creditErrorMessage
  )

  if (plan && PLAN_TIER_MAP[plan]) {
    await handleDb(
      () => db
        .prepare('UPDATE tenants SET tier = ? WHERE id = ?')
        .bind(PLAN_TIER_MAP[plan], tenantId)
        .run(),
      'DATABASE_ERROR',
      'Failed to upgrade tenant tier'
    )
  }
}
