import { describe, it, expect, vi } from 'vitest'
import type { Ai, MessageBatch, Queue } from '@cloudflare/workers-types'
import server from '../src/index'
import {
  handleMissionQueueBatch,
  processMissionQueueMessage,
  type MissionQueuePayload,
} from '../src/raas/mission-outbox-queue'
import { getBalance } from '../src/raas/credits'
import { createInMemoryPilotDb } from './helpers/pilot-test-db'

export const SERVICE_TOKEN = 'test-operator-service-token-123456'

export async function setupPilotTenantWithInvite(db: ReturnType<typeof createInMemoryPilotDb>['db']) {
  const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true' }
  const invRes = await server.fetch(
    new Request('http://localhost/billing/invites', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${SERVICE_TOKEN}`,
      },
      body: JSON.stringify({ partner_label: 'Mission Partner' }),
    }),
    env,
  )
  const { invite_code } = (await invRes.json()) as { invite_code: string }
  const tenantRes = await server.fetch(
    new Request('http://localhost/billing/tenants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Mission Partner', invite_code }),
    }),
    env,
  )
  return (await tenantRes.json()) as { tenant_id: string; api_key: string; credits: number }
}

describe('Pilot mission submission, outbox, queue execution & step validation', () => {
  it('enqueues pending mission on POST /v1/tasks, executes LLM-only steps via queue, and serves result', async () => {
    const { db, state } = createInMemoryPilotDb()
    const tenant = await setupPilotTenantWithInvite(db)
    const queuedMessages: MissionQueuePayload[] = []
    const mockQueue = {
      send: vi.fn(async (msg: MissionQueuePayload) => {
        queuedMessages.push(msg)
      }),
    } as unknown as Queue<MissionQueuePayload>
    const mockAi = {
      run: vi.fn(async () => ({
        response: 'Synthetic Q1 summary: 5 pilot partners completed onboarding with 98% satisfaction.',
      })),
    } as unknown as Ai

    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true', MISSION_QUEUE: mockQueue, AI: mockAi }

    const submitRes = await server.fetch(
      new Request('http://localhost/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${tenant.api_key}`,
        },
        body: JSON.stringify({ goal: 'Summarize synthetic Q1 partner feedback' }),
      }),
      env,
    )
    expect(submitRes.status).toBe(201)
    const submitted = (await submitRes.json()) as {
      id: string
      status: string
      credits_used: number
    }
    expect(submitted.status).toBe('pending')
    expect(submitted.credits_used).toBe(1)
    expect(await getBalance(db, tenant.tenant_id)).toBe(9)
    expect(state.outbox[0]?.status).toBe('published')
    expect(queuedMessages).toHaveLength(1)

    const ackFn = vi.fn()
    const retryFn = vi.fn()
    const batch = {
      queue: 'mekong-mission-queue',
      messages: [{ body: queuedMessages[0]!, attempts: 1, ack: ackFn, retry: retryFn }],
    } as unknown as MessageBatch<MissionQueuePayload>

    await handleMissionQueueBatch(batch, env)
    expect(ackFn).toHaveBeenCalledTimes(1)
    expect(retryFn).not.toHaveBeenCalled()

    const transitions = state.statusHistory
      .filter((s) => s.missionId === submitted.id)
      .map((s) => s.status)
    expect(transitions).toEqual(['pending', 'planning', 'executing', 'verifying', 'completed'])

    const pollRes = await server.fetch(
      new Request(`http://localhost/v1/tasks/${submitted.id}`, {
        headers: { Authorization: `Bearer ${tenant.api_key}` },
      }),
      env,
    )
    expect(pollRes.status).toBe(200)
    const polled = (await pollRes.json()) as { status: string; result: string }
    expect(polled.status).toBe('completed')
    const parsedResult = JSON.parse(polled.result) as { status: string }
    expect(parsedResult.status).toBe('success')

    const duplicateOutcome = await processMissionQueueMessage(db, env, queuedMessages[0]!, { attempts: 2 })
    expect(duplicateOutcome.idempotentSkip).toBe(true)
    expect(await getBalance(db, tenant.tenant_id)).toBe(9)
  })

  it('rejects api and shell steps in pilot mode and refunds credits exactly once', async () => {
    const { db, state } = createInMemoryPilotDb()
    const tenant = await setupPilotTenantWithInvite(db)
    const mockAi = {
      run: vi.fn(async () => ({ response: 'Valid LLM response output' })),
    } as unknown as Ai
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true', AI: mockAi }

    for (const forbiddenType of ['api', 'shell'] as const) {
      const submitRes = await server.fetch(
        new Request('http://localhost/v1/tasks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${tenant.api_key}`,
          },
          body: JSON.stringify({ goal: `Forbidden ${forbiddenType} mission` }),
        }),
        env,
      )
      const { id: mission_id } = (await submitRes.json()) as { id: string }
      const payload: MissionQueuePayload = {
        mission_id,
        tenant_id: tenant.tenant_id,
        goal: `Forbidden ${forbiddenType} mission`,
        credits_cost: 1,
        steps: [
          {
            order: 1,
            title: `step_${forbiddenType}`,
            description: `Attempt ${forbiddenType} execution`,
            mode: forbiddenType,
            depends_on: [],
            params: {},
          },
        ],
        enqueued_at: new Date().toISOString(),
      }

      const outcome = await processMissionQueueMessage(db, env, payload, { attempts: 1 })
      expect(outcome.status).toBe('failed')
      expect(outcome.shouldRetry).toBe(false)
      expect(outcome.refunded).toBe(true)

      const dup = await processMissionQueueMessage(db, env, payload, { attempts: 2 })
      expect(dup.idempotentSkip).toBe(true)
      expect(dup.refunded).toBe(false)
    }

    expect(await getBalance(db, tenant.tenant_id)).toBe(10)
    expect(state.creditEvents.filter((e) => e.event_type === 'refund')).toHaveLength(2)
  })
})
