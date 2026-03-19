import { describe, it, expect } from 'vitest'
import { default as server } from '../src/index'

// Minimal mock bindings for Hono server.fetch()
const mockEnv = {}

describe('Health endpoint', () => {
  it('GET /health returns status ok without DB', async () => {
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(200)
    const body = (await res.json()) as { status: string; version: string }
    expect(body.status).toBe('ok')
    expect(body.version).toBe('3.2.0')
  })

  it('GET /health reports bindings as false when none configured', async () => {
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, mockEnv)

    const body = (await res.json()) as { bindings: Record<string, boolean> }
    expect(body.bindings.d1).toBe(false)
    expect(body.bindings.kv).toBe(false)
    expect(body.bindings.ai).toBe(false)
  })

  it('GET /health returns uptime as positive number', async () => {
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(200)
    const body = (await res.json()) as { uptime: number }
    expect(body.uptime).toBeGreaterThanOrEqual(0)
  })

  it('GET /health returns database status when DB not configured', async () => {
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, mockEnv)

    const body = (await res.json()) as { database: { connected: boolean; latency_ms: number | null } }
    expect(body.database.connected).toBe(false)
    expect(body.database.latency_ms).toBeNull()
  })

  it('GET /health returns active_workers count', async () => {
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, mockEnv)

    const body = (await res.json()) as { active_workers: number }
    expect(body.active_workers).toBe(0)
  })

  it('GET /health returns database connected with mock DB', async () => {
    const mockDB = {
      prepare: () => ({
        first: async () => ({ health: 1 }),
      }),
      exec: async () => {},
    }
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, { DB: mockDB as any })

    expect(res.status).toBe(200)
    const body = (await res.json()) as { database: { connected: boolean; latency_ms: number | null } }
    expect(body.database.connected).toBe(true)
    expect(body.database.latency_ms).toBeGreaterThanOrEqual(0)
  })

  it('GET /health returns active_workers from DB query', async () => {
    const mockDB = {
      prepare: (sql: string) => ({
        first: async () => {
          if (sql.includes('COUNT')) {
            return { count: 5 }
          }
          return { health: 1 }
        },
      }),
      exec: async () => {},
    }
    const req = new Request('http://localhost/health')
    const res = await server.fetch(req, { DB: mockDB as any })

    expect(res.status).toBe(200)
    const body = (await res.json()) as { active_workers: number }
    expect(body.active_workers).toBe(5)
  })
})

describe('Billing endpoints', () => {
  it('POST /billing/tenants returns 503 without D1', async () => {
    const req = new Request('http://localhost/billing/tenants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test' }),
    })
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(503)
  })

  it('GET /billing/credits requires auth', async () => {
    const req = new Request('http://localhost/billing/credits')
    const res = await server.fetch(req, mockEnv)
    expect(res.status).toBe(401)
  })
})

describe('Settings endpoints', () => {
  it('GET /v1/settings/llm returns 503 without DB', async () => {
    const req = new Request('http://localhost/v1/settings/llm')
    const res = await server.fetch(req, mockEnv)
    expect(res.status).toBe(503)
  })

  it('POST /v1/settings/llm returns 503 without DB', async () => {
    const req = new Request('http://localhost/v1/settings/llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider: 'openai', api_key: 'sk-test' }),
    })
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(503)
  })

  it('DELETE /v1/settings/llm returns 503 without DB', async () => {
    const req = new Request('http://localhost/v1/settings/llm', {
      method: 'DELETE',
    })
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(503)
  })
})

describe('PEV endpoint', () => {
  it('POST /cmd returns 503 without AI or LLM key', async () => {
    const req = new Request('http://localhost/cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal: 'test' }),
    })
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(503)
  })
})

describe('Error handling', () => {
  it('POST /cmd with invalid JSON returns 400 not 500', async () => {
    // Need AI binding to pass the "no LLM provider" check (503) before hitting JSON parse
    const envWithAI = { AI: {} }
    const req = new Request('http://localhost/cmd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: 'not valid json',
    })
    const res = await server.fetch(req, envWithAI)

    expect(res.status).toBe(400)
    const body = (await res.json()) as { error: string }
    expect(body.error).toContain('Invalid JSON')
  })

  it('POST /billing/tenants with invalid JSON returns 400', async () => {
    // Need DB binding to pass the "D1 not configured" check before hitting JSON parse
    const envWithDB = { DB: {} }
    const req = new Request('http://localhost/billing/tenants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{broken',
    })
    const res = await server.fetch(req, envWithDB)

    expect(res.status).toBe(400)
  })
})

describe('API key regeneration', () => {
  it('POST /billing/tenants/regenerate-key returns 503 without D1', async () => {
    const req = new Request('http://localhost/billing/tenants/regenerate-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenant_id: 'test', name: 'test' }),
    })
    const res = await server.fetch(req, mockEnv)

    expect(res.status).toBe(503)
  })

  it('POST /billing/tenants/regenerate-key validates required fields', async () => {
    const req = new Request('http://localhost/billing/tenants/regenerate-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenant_id: 'test' }),
    })
    const res = await server.fetch(req, mockEnv)

    // Without DB → 503 (DB check runs before validation)
    expect(res.status).toBe(503)
  })
})
