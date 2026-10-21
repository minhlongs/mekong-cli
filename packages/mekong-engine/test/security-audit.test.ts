/**
 * Security Test Suite — Input Validation, API Key Security & Security Headers
 */

import { describe, it, expect } from 'vitest'
import type { Context } from 'hono'
import { z } from 'zod'
import { validateBody, validateQuery, validateParam, MAX_PAYLOAD_SIZE } from '../src/raas/validation'
import { constantTimeCompare } from '../src/lib/crypto-utils'
import type { SecurityHeadersOptions } from '../src/middleware/security'

export const createSecurityMockContext = (
  body?: unknown,
  query?: Record<string, string>,
  params?: Record<string, string>,
): Context =>
  ({
    req: {
      header: (name: string) => {
        if (name === 'content-length') {
          return String(JSON.stringify(body || {}).length)
        }
        return undefined
      },
      json: async () => body,
      query: () => query || {},
      param: () => params || {},
    },
  }) as unknown as Context

export async function hashApiKey(key: string): Promise<string> {
  const encoded = new TextEncoder().encode(key)
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

export function buildCspValue(csp: NonNullable<SecurityHeadersOptions['csp']>): string {
  const directives: string[] = []
  if (csp.defaultSrc?.length) directives.push(`default-src ${csp.defaultSrc.join(' ')}`)
  if (csp.scriptSrc?.length) directives.push(`script-src ${csp.scriptSrc.join(' ')}`)
  if (csp.styleSrc?.length) directives.push(`style-src ${csp.styleSrc.join(' ')}`)
  if (csp.imgSrc?.length) directives.push(`img-src ${csp.imgSrc.join(' ')}`)
  if (csp.connectSrc?.length) directives.push(`connect-src ${csp.connectSrc.join(' ')}`)
  if (csp.fontSrc?.length) directives.push(`font-src ${csp.fontSrc.join(' ')}`)
  if (csp.objectSrc?.length) directives.push(`object-src ${csp.objectSrc.join(' ')}`)
  if (csp.frameAncestors?.length) directives.push(`frame-ancestors ${csp.frameAncestors.join(' ')}`)
  if (csp.baseUri?.length) directives.push(`base-uri ${csp.baseUri.join(' ')}`)
  if (csp.formAction?.length) directives.push(`form-action ${csp.formAction.join(' ')}`)
  if (csp.upgradeInsecureRequests) directives.push('upgrade-insecure-requests')
  return directives.join('; ')
}

describe('Input Validation', () => {
  describe('validateBody', () => {
    it('should have MAX_PAYLOAD_SIZE constant defined', () => {
      expect(MAX_PAYLOAD_SIZE).toBe(10000)
    })

    it('should validate valid body with schema', async () => {
      const schema = z.object({
        name: z.string().min(1),
        email: z.string().email(),
      })

      const ctx = createSecurityMockContext({ name: 'Test', email: 'test@example.com' })
      const result = await validateBody(ctx, schema)

      expect(result).toEqual({ name: 'Test', email: 'test@example.com' })
    })
  })

  describe('validateQuery', () => {
    it('should validate query parameters', () => {
      const schema = z.object({
        limit: z.string().transform(Number).default('10'),
        offset: z.string().transform(Number).default('0'),
      })

      const ctx = createSecurityMockContext(undefined, { limit: '20', offset: '5' })
      const result = validateQuery(ctx, schema)

      expect(result).toEqual({ limit: 20, offset: 5 })
    })
  })

  describe('validateParam', () => {
    it('should validate route parameters', () => {
      const schema = z.object({
        id: z.string().uuid(),
      })

      const validId = '123e4567-e89b-12d3-a456-426614174000'
      const ctx = createSecurityMockContext(undefined, undefined, { id: validId })
      const result = validateParam(ctx, schema)

      expect(result).toEqual({ id: validId })
    })
  })
})

describe('API Key Security', () => {
  describe('hashApiKey', () => {
    it('should produce consistent hashes', async () => {
      const key = 'test-api-key-123'
      const hash1 = await hashApiKey(key)
      const hash2 = await hashApiKey(key)

      expect(hash1).toBe(hash2)
    })

    it('should produce different hashes for different keys', async () => {
      const hash1 = await hashApiKey('key-one')
      const hash2 = await hashApiKey('key-two')

      expect(hash1).not.toBe(hash2)
    })

    it('should use SHA-256 (64 char hex)', async () => {
      const hash = await hashApiKey('test-key')
      expect(hash).toHaveLength(64)
      expect(hash).toMatch(/^[0-9a-f]+$/)
    })
  })

  describe('constantTimeCompare', () => {
    it('should return true for equal strings', () => {
      expect(constantTimeCompare('abc123', 'abc123')).toBe(true)
    })

    it('should return false for different strings', () => {
      expect(constantTimeCompare('abc123', 'abc124')).toBe(false)
    })

    it('should return false for different length strings', () => {
      expect(constantTimeCompare('abc123', 'abc1234')).toBe(false)
    })

    it('should handle empty strings', () => {
      expect(constantTimeCompare('', '')).toBe(true)
      expect(constantTimeCompare('', 'a')).toBe(false)
    })
  })
})

describe('Security Headers', () => {
  describe('buildCspValue', () => {
    it('should build CSP string from directives', () => {
      const csp = {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", 'data:'],
        frameAncestors: ["'none'"],
        upgradeInsecureRequests: true,
      }

      const result = buildCspValue(csp)

      expect(result).toContain("default-src 'self'")
      expect(result).toContain("script-src 'self' 'unsafe-inline'")
      expect(result).toContain("img-src 'self' data:")
      expect(result).toContain("frame-ancestors 'none'")
      expect(result).toContain('upgrade-insecure-requests')
    })

    it('should handle empty directives', () => {
      const csp = {
        defaultSrc: ["'none'"], scriptSrc: [], styleSrc: [], imgSrc: [], connectSrc: [],
        fontSrc: [], objectSrc: [], frameAncestors: [], baseUri: [], formAction: [],
        upgradeInsecureRequests: false,
      }
      expect(buildCspValue(csp)).toBe("default-src 'none'")
    })
  })
})
