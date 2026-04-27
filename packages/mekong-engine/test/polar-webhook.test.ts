import { describe, it, expect } from 'vitest'
import {
  tierFromProductName,
  verifyPolarSignature,
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

async function hmacHex(secret: string, body: string): Promise<string> {
  const enc = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const buf = await crypto.subtle.sign('HMAC', key, enc.encode(body))
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

describe('verifyPolarSignature', () => {
  const secret = 'whsec_test_polar_secret_value'
  const body = JSON.stringify({ type: 'subscription.created', data: {} })

  it('returns false when signature missing', async () => {
    expect(await verifyPolarSignature(body, undefined, secret)).toBe(false)
  })

  it('returns false when secret missing', async () => {
    expect(await verifyPolarSignature(body, 'aabbcc', undefined)).toBe(false)
  })

  it('accepts raw hex signature', async () => {
    const sig = await hmacHex(secret, body)
    expect(await verifyPolarSignature(body, sig, secret)).toBe(true)
  })

  it('accepts v1=<hex> formatted signature', async () => {
    const sig = await hmacHex(secret, body)
    expect(await verifyPolarSignature(body, `v1=${sig}`, secret)).toBe(true)
  })

  it('rejects tampered signature', async () => {
    const sig = await hmacHex(secret, body + 'tampered')
    expect(await verifyPolarSignature(body, sig, secret)).toBe(false)
  })

  it('rejects mismatched secret', async () => {
    const sig = await hmacHex('wrong-secret', body)
    expect(await verifyPolarSignature(body, sig, secret)).toBe(false)
  })
})
