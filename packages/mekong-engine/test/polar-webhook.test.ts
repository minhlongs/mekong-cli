import { describe, it, expect } from 'vitest'
import {
  tierFromProductName,
  verifyPolarSignature,
  handleSubscriptionCreated,
  SUBSCRIPTION_CREDITS,
} from '../src/raas/polar-webhook'

describe('tierFromProductName', () => {
  it('detects pro tier', () => {
    expect(tierFromProductName('Mekong Pro Monthly')).toBe('pro')
  })

  it('detects growth tier', () => {
    expect(tierFromProductName('Mekong Growth')).toBe('growth')
  })

  it('falls back to starter', () => {
    expect(tierFromProductName('Foundation Plan')).toBe('starter')
    expect(tierFromProductName(undefined)).toBe('starter')
    expect(tierFromProductName('')).toBe('starter')
  })

  it('matches pro before growth', () => {
    expect(tierFromProductName('Pro Growth Suite')).toBe('pro')
  })
})

async function hmacBase64(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const buf = await crypto.subtle.sign('HMAC', key, enc.encode(message))
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return btoa(binary)
}

describe('verifyPolarSignature', () => {
  const secret = 'whsec_test_polar_secret_value'
  const body = JSON.stringify({ type: 'subscription.created', data: {} })
  const webhookId = 'test_event_001'
  const now = Math.floor(Date.now() / 1000)
  const webhookTimestamp = String(now)

  it('returns false when signature missing', async () => {
    expect(await verifyPolarSignature(body, webhookId, webhookTimestamp, undefined, secret)).toBe(false)
  })

  it('returns false when secret missing', async () => {
    expect(await verifyPolarSignature(body, webhookId, webhookTimestamp, 'v1,sig', undefined)).toBe(false)
  })

  it('returns false when headers missing', async () => {
    expect(await verifyPolarSignature(body, undefined, undefined, undefined, secret)).toBe(false)
  })

  it('accepts valid standard webhooks signature', async () => {
    const signingInput = `${webhookId}.${webhookTimestamp}.${body}`
    const sig = await hmacBase64(secret, signingInput)
    expect(await verifyPolarSignature(body, webhookId, webhookTimestamp, `v1,${sig}`, secret)).toBe(true)
  })

  it('rejects tampered body', async () => {
    const tamperedBody = JSON.stringify({ type: 'subscription.cancelled', data: {} })
    const signingInput = `${webhookId}.${webhookTimestamp}.${tamperedBody}`
    const sig = await hmacBase64(secret, signingInput)
    expect(await verifyPolarSignature(body, webhookId, webhookTimestamp, `v1,${sig}`, secret)).toBe(false)
  })

  it('rejects wrong secret', async () => {
    const signingInput = `${webhookId}.${webhookTimestamp}.${body}`
    const sig = await hmacBase64('wrong-secret', signingInput)
    expect(await verifyPolarSignature(body, webhookId, webhookTimestamp, `v1,${sig}`, secret)).toBe(false)
  })

  it('rejects expired timestamp (5 min window)', async () => {
    const oldTs = String(now - 301)
    const signingInput = `${webhookId}.${oldTs}.${body}`
    const sig = await hmacBase64(secret, signingInput)
    expect(await verifyPolarSignature(body, webhookId, oldTs, `v1,${sig}`, secret)).toBe(false)
  })
})

describe('SUBSCRIPTION_CREDITS', () => {
  it('maps starter to 200 credits', () => {
    expect(SUBSCRIPTION_CREDITS.starter).toBe(200)
  })

  it('maps growth to 1000 credits', () => {
    expect(SUBSCRIPTION_CREDITS.growth).toBe(1000)
  })

  it('maps pro to 5000 credits', () => {
    expect(SUBSCRIPTION_CREDITS.pro).toBe(5000)
  })
})

describe('handleSubscriptionCreated', () => {
  function mockDb(overrides = {}) {
    const store = new Map<string, any[]>()
    return {
      prepare: (sql: string) => ({
        bind: (...args: any[]) => ({
          first: async <T>() => {
            if (sql.includes('SELECT id FROM tenants')) {
              const id = args[0] as string
              return store.get('tenants')?.find((t) => t.id === id) as T ?? null
            }
            if (sql.includes('SELECT id FROM license_keys')) {
              return store.get('license_keys')?.find((l) => l.id === args[0]) as T ?? null
            }
            return null as T
          },
          run: async () => {
            if (sql.includes('INSERT INTO tenants')) {
              if (!store.has('tenants')) store.set('tenants', [])
              store.get('tenants')!.push({ id: args[0], name: args[1], api_key_hash: args[2], tier: args[3], created_at: args[4] })
            }
            if (sql.includes('INSERT INTO credits')) {
              if (!store.has('credits')) store.set('credits', [])
              store.get('credits')!.push({ tenant_id: args[0], amount: args[1], reason: args[2] })
            }
            if (sql.includes('INSERT INTO license_keys')) {
              if (!store.has('license_keys')) store.set('license_keys', [])
              store.get('license_keys')!.push({ id: args[0], tenant_id: args[1], status: 'active' })
            }
          },
          all: async () => ({ results: store.get('tenants') ?? [] }),
        }),
      }),
      ...overrides,
    } as any
  }

  it('creates tenant and grants credits for starter', async () => {
    const db = mockDb()
    const event = {
      type: 'subscription.created',
      data: {
        id: 'evt_001',
        subscription: {
          customer: { id: 'cus_starter_1', email: 'user@test.com' },
          product: { name: 'Starter Monthly' },
        },
      },
    }
    const result = await handleSubscriptionCreated(db, event)
    expect(result).not.toBeNull()
    expect(result!.tier).toBe('starter')
    expect(result!.creditsGranted).toBe(200)
    expect(result!.email).toBe('user@test.com')
  })

  it('grants 5000 credits for pro', async () => {
    const db = mockDb()
    const event = {
      type: 'subscription.created',
      data: {
        subscription: {
          customer: { id: 'cus_pro_1', email: 'pro@test.com' },
          product: { name: 'Mekong Pro Annual' },
        },
      },
    }
    const result = await handleSubscriptionCreated(db, event)
    expect(result).not.toBeNull()
    expect(result!.tier).toBe('pro')
    expect(result!.creditsGranted).toBe(5000)
  })

  it('returns null when customer id missing', async () => {
    const db = mockDb()
    const event = { type: 'subscription.created', data: { subscription: { product: { name: 'Starter' } } } }
    const result = await handleSubscriptionCreated(db, event)
    expect(result).toBeNull()
  })

  it('is idempotent on second call', async () => {
    const db = mockDb()
    const event = {
      type: 'subscription.created',
      data: {
        subscription: {
          customer: { id: 'cus_dup', email: 'dup@test.com' },
          product: { name: 'Growth Plan' },
        },
      },
    }
    const r1 = await handleSubscriptionCreated(db, event)
    const r2 = await handleSubscriptionCreated(db, event)
    expect(r1!.tier).toBe('growth')
    expect(r1!.creditsGranted).toBe(1000)
    expect(r2).not.toBeNull()
    expect(r2!.tenantId).toBe(r1!.tenantId)
  })
})
