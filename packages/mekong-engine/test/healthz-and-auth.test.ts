import { describe, it, expect, beforeEach, vi } from 'vitest'
import { verify } from 'hono/jwt'
import { default as server } from '../src/index'

interface PreparedStatement {
  bind: (...args: any[]) => PreparedStatement
  first: <T = unknown>() => Promise<T | null>
  run: () => Promise<{ success: boolean }>
  all: <T = unknown>() => Promise<{ results: T[] }>
}

function createMockDB(rows: Record<string, any>) {
  return {
    prepare: vi.fn((sql: string): PreparedStatement => {
      const stmt: PreparedStatement = {
        bind: () => stmt,
        first: async () => rows[sql] ?? null,
        run: async () => ({ success: true }),
        all: async () => ({ results: [] }),
      }
      return stmt
    }),
    exec: vi.fn(async () => ({ success: true })),
  }
}

describe('GET /healthz', () => {
  it('returns 200 with status ok (no I/O)', async () => {
    const res = await server.fetch(new Request('http://localhost/healthz'), {})
    expect(res.status).toBe(200)
    const body = (await res.json()) as { status: string; version: string }
    expect(body.status).toBe('ok')
    expect(body.version).toBe('3.2.0')
  })

  it('does not query the database', async () => {
    const db = createMockDB({})
    await server.fetch(new Request('http://localhost/healthz'), { DB: db })
    expect(db.prepare).not.toHaveBeenCalled()
    expect(db.exec).not.toHaveBeenCalled()
  })
})

describe('POST /auth/login', () => {
  let db: ReturnType<typeof createMockDB>
  const JWT_SECRET=REDACTED = 'unit-test-secret-32bytes-min-aaaa'

  beforeEach(() => {
    // The route hashes the key, then SELECTs. We bypass via SQL match.
    db = createMockDB({})
  })

  it('returns 400 when license_key missing', async () => {
    const res = await server.fetch(
      new Request('http://localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }),
      { DB: db, JWT_SECRET=REDACTED },
    )
    expect(res.status).toBe(400)
  })

  it('returns 503 when DB unavailable', async () => {
    const res = await server.fetch(
      new Request('http://localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: 'lk_aaaaaaaa' }),
      }),
      { JWT_SECRET=REDACTED },
    )
    expect(res.status).toBe(503)
  })

  it('returns 401 when license unknown', async () => {
    const res = await server.fetch(
      new Request('http://localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: 'lk_unknown_999' }),
      }),
      { DB: db, JWT_SECRET=REDACTED },
    )
    expect(res.status).toBe(401)
    expect(((await res.json()) as { error: string }).error).toBe('invalid_license')
  })

  it('returns 402 when license suspended', async () => {
    db = createMockDB({
      'SELECT tenant_id, status, expires_at FROM license_keys WHERE key_hash = ?': {
        tenant_id: 't1',
        status: 'suspended',
        expires_at: null,
      },
    })
    const res = await server.fetch(
      new Request('http://localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: 'lk_suspended' }),
      }),
      { DB: db, JWT_SECRET=REDACTED },
    )
    expect(res.status).toBe(402)
    expect(((await res.json()) as { status: string }).status).toBe('suspended')
  })

  it('returns 200 with verifiable JWT on success', async () => {
    db = createMockDB({
      'SELECT tenant_id, status, expires_at FROM license_keys WHERE key_hash = ?': {
        tenant_id: 'tenant_42',
        status: 'active',
        expires_at: null,
      },
    })
    const res = await server.fetch(
      new Request('http://localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: 'lk_okay_99' }),
      }),
      { DB: db, JWT_SECRET=REDACTED },
    )
    expect(res.status).toBe(200)
    const body = (await res.json()) as {
      access_token: string
      tenant_id: string
      expires_in: number
    }
    expect(body.tenant_id).toBe('tenant_42')
    expect(body.expires_in).toBe(3600)

    const claims = (await verify(body.access_token, JWT_SECRET=REDACTED, 'HS256')) as {
      tenant_id: string
      license_status: string
    }
    expect(claims.tenant_id).toBe('tenant_42')
    expect(claims.license_status).toBe('active')
  })

  it('returns 500 when JWT_SECRET=REDACTED missing', async () => {
    db = createMockDB({
      'SELECT tenant_id, status, expires_at FROM license_keys WHERE key_hash = ?': {
        tenant_id: 'tenant_99',
        status: 'active',
        expires_at: null,
      },
    })
    const res = await server.fetch(
      new Request('http://localhost/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ license_key: 'lk_okay_99' }),
      }),
      { DB: db },
    )
    expect(res.status).toBe(500)
  })
})
