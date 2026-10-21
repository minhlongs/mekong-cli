import { describe, it, expect } from 'vitest'
import server from '../src/index'
import { createInMemoryPilotDb } from './helpers/pilot-test-db'

const SERVICE_TOKEN = 'test-operator-service-token-123456'

describe('Pilot single-use invite gate & tenant creation', () => {
  it('requires operator SERVICE_TOKEN to issue or list invite codes', async () => {
    const { db } = createInMemoryPilotDb()
    const unauthPost = await server.fetch(
      new Request('http://localhost/billing/invites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ partner_label: 'Partner 1' }),
      }),
      { DB: db, SERVICE_TOKEN },
    )
    expect(unauthPost.status).toBe(401)

    const unauthGet = await server.fetch(
      new Request('http://localhost/billing/invites'),
      { DB: db, SERVICE_TOKEN },
    )
    expect(unauthGet.status).toBe(401)
  })

  it('issues up to 5 partner invite codes, stores only SHA-256 hashes, and enforces the 5-code cap', async () => {
    const { db, state } = createInMemoryPilotDb()
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true', PILOT_MAX_INVITES: '5' }

    const issuedCodes: string[] = []
    for (let i = 1; i <= 5; i++) {
      const res = await server.fetch(
        new Request('http://localhost/billing/invites', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${SERVICE_TOKEN}`,
          },
          body: JSON.stringify({ partner_label: `Partner ${i}` }),
        }),
        env,
      )
      expect(res.status).toBe(201)
      const data = (await res.json()) as {
        invite_id: string
        invite_code: string
        code_hash: string
      }
      expect(data.invite_code).toMatch(/^mk_inv_[0-9a-f]{32}$/)
      expect(data.code_hash).not.toBe(data.invite_code)
      expect(data.code_hash).toMatch(/^[0-9a-f]{64}$/)
      issuedCodes.push(data.invite_code)
    }

    // Verify D1 stores only code hashes, never raw invite codes
    for (const stored of state.invites) {
      expect(issuedCodes).not.toContain(stored.code_hash)
    }

    // 6th invite must be rejected with 409 PILOT_INVITE_LIMIT_REACHED
    const sixth = await server.fetch(
      new Request('http://localhost/billing/invites', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${SERVICE_TOKEN}`,
        },
        body: JSON.stringify({ partner_label: 'Partner 6' }),
      }),
      env,
    )
    expect(sixth.status).toBe(409)
    const sixthBody = (await sixth.json()) as { code: string }
    expect(sixthBody.code).toBe('PILOT_INVITE_LIMIT_REACHED')
  })

  it('rejects missing, invalid, or reused invite codes and returns API key once on redemption', async () => {
    const { db, state } = createInMemoryPilotDb()
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true' }

    // 1. Missing invite_code on POST /billing/tenants -> 403 INVITE_CODE_REQUIRED
    const missingRes = await server.fetch(
      new Request('http://localhost/billing/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Public Signup Attempt' }),
      }),
      env,
    )
    expect(missingRes.status).toBe(403)
    expect(((await missingRes.json()) as { code: string }).code).toBe('INVITE_CODE_REQUIRED')

    // 2. Invalid invite_code -> 403 INVALID_INVITE_CODE
    const invalidRes = await server.fetch(
      new Request('http://localhost/billing/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Bad Code Partner', invite_code: 'mk_inv_invalid' }),
      }),
      env,
    )
    expect(invalidRes.status).toBe(403)
    expect(((await invalidRes.json()) as { code: string }).code).toBe('INVALID_INVITE_CODE')

    // 3. Issue a valid code and redeem it
    const inviteRes = await server.fetch(
      new Request('http://localhost/billing/invites', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${SERVICE_TOKEN}`,
        },
        body: JSON.stringify({ partner_label: 'Design Partner Alpha' }),
      }),
      env,
    )
    const { invite_code: inviteCode } = (await inviteRes.json()) as { invite_code: string }

    const redeemRes = await server.fetch(
      new Request('http://localhost/billing/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Design Partner Alpha', invite_code: inviteCode }),
      }),
      env,
    )
    expect(redeemRes.status).toBe(201)
    const created = (await redeemRes.json()) as {
      tenant_id: string
      api_key: string
      credits: number
    }
    expect(created.api_key).toMatch(/^mk_/)
    expect(created.credits).toBe(10)
    expect(state.tenants[0]?.api_key_hash).not.toBe(created.api_key)

    // 4. Reusing the same invite_code on /billing/tenants -> 409 INVITE_CODE_ALREADY_USED
    const reuseRes = await server.fetch(
      new Request('http://localhost/billing/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Second Use Attempt', invite_code: inviteCode }),
      }),
      env,
    )
    expect(reuseRes.status).toBe(409)
    expect(((await reuseRes.json()) as { code: string }).code).toBe('INVITE_CODE_ALREADY_USED')

    // 5. POST /v1/onboard/signup also requires a valid single-use invite_code in pilot mode
    const onboardNoCode = await server.fetch(
      new Request('http://localhost/v1/onboard/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'alpha@example.com', business_name: 'Alpha Co' }),
      }),
      env,
    )
    expect(onboardNoCode.status).toBe(403)
  })
})
