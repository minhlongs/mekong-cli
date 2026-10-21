import { describe, it, expect, vi } from 'vitest'
import type { Ai, Queue } from '@cloudflare/workers-types'
import server from '../src/index'
import {
  processMissionQueueMessage,
  republishPendingOutbox,
  type MissionQueuePayload,
} from '../src/raas/mission-outbox-queue'
import { getBalance, refundMissionCreditsOnce } from '../src/raas/credits'
import { createInMemoryPilotDb } from './helpers/pilot-test-db'
import { SERVICE_TOKEN, setupPilotTenantWithInvite } from './pilot-mission-queue.test'

describe('Pilot mission retries, DLQ routing, outbox recovery & credit guards', () => {
  it('retries transient failures up to 3 attempts, then routes to DLQ and refunds once', async () => {
    const { db } = createInMemoryPilotDb()
    const tenant = await setupPilotTenantWithInvite(db)
    const failingAi = {
      run: vi.fn(async () => {
        throw new Error('Workers AI temporary timeout')
      }),
    } as unknown as Ai
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true', AI: failingAi }

    const submitRes = await server.fetch(
      new Request('http://localhost/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${tenant.api_key}`,
        },
        body: JSON.stringify({ goal: 'Transient failure mission' }),
      }),
      env,
    )
    const { id: mission_id } = (await submitRes.json()) as { id: string }
    expect(await getBalance(db, tenant.tenant_id)).toBe(9)

    const payload: MissionQueuePayload = {
      mission_id,
      tenant_id: tenant.tenant_id,
      goal: 'Transient failure mission',
      credits_cost: 1,
      enqueued_at: new Date().toISOString(),
    }

    const attempt1 = await processMissionQueueMessage(db, env, payload, { attempts: 1, maxRetries: 3 })
    expect(attempt1.status).toBe('retrying')
    expect(attempt1.shouldRetry).toBe(true)
    expect(attempt1.refunded).toBe(false)

    const attempt2 = await processMissionQueueMessage(db, env, payload, { attempts: 2, maxRetries: 3 })
    expect(attempt2.status).toBe('retrying')
    expect(attempt2.shouldRetry).toBe(true)

    const attempt3 = await processMissionQueueMessage(db, env, payload, { attempts: 3, maxRetries: 3 })
    expect(attempt3.status).toBe('failed')
    expect(attempt3.shouldRetry).toBe(false)
    expect(attempt3.refunded).toBe(true)
    expect(await getBalance(db, tenant.tenant_id)).toBe(10)

    const dlqOutcome = await processMissionQueueMessage(db, env, payload, { attempts: 3, isDlq: true })
    expect(dlqOutcome.idempotentSkip).toBe(true)
    expect(dlqOutcome.refunded).toBe(false)
    expect(await getBalance(db, tenant.tenant_id)).toBe(10)
  })

  it('rejects non-llm steps at POST /v1/tasks boundary, sweeps pending outbox rows, and guards refunds without prior debit', async () => {
    const { db, state } = createInMemoryPilotDb()
    const tenant = await setupPilotTenantWithInvite(db)
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true' }

    const rejectRes = await server.fetch(
      new Request('http://localhost/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${tenant.api_key}`,
        },
        body: JSON.stringify({
          goal: 'Attempt direct shell step at HTTP boundary',
          steps: [{ order: 1, title: 'shell_step', description: 'ls', mode: 'shell', depends_on: [], params: {} }],
        }),
      }),
      env,
    )
    expect(rejectRes.status).toBe(400)
    expect(await getBalance(db, tenant.tenant_id)).toBe(10)

    const bogusRefund = await refundMissionCreditsOnce(db, tenant.tenant_id, crypto.randomUUID(), 5, 'bogus refund')
    expect(bogusRefund.refunded).toBe(false)
    expect(await getBalance(db, tenant.tenant_id)).toBe(10)

    let shouldFailSend = true
    const sentMessages: MissionQueuePayload[] = []
    const flakyQueue = {
      send: vi.fn(async (msg: MissionQueuePayload) => {
        if (shouldFailSend) throw new Error('Queue temporarily unavailable')
        sentMessages.push(msg)
      }),
    } as unknown as Queue<MissionQueuePayload>

    const submitRes = await server.fetch(
      new Request('http://localhost/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${tenant.api_key}`,
        },
        body: JSON.stringify({ goal: 'Outbox recovery mission' }),
      }),
      { ...env, MISSION_QUEUE: flakyQueue },
    )
    expect(submitRes.status).toBe(201)
    expect(state.outbox[0]?.status).toBe('pending')

    shouldFailSend = false
    const republished = await republishPendingOutbox(db, flakyQueue)
    expect(republished).toBe(1)
    expect(state.outbox[0]?.status).toBe('published')
    expect(sentMessages).toHaveLength(1)
  })
})
