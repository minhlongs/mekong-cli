import { describe, it, expect, vi } from 'vitest'
import type { Ai, ExecutionContext, Queue, ScheduledEvent } from '@cloudflare/workers-types'
import server from '../src/index'
import { processMissionQueueMessage, type MissionQueuePayload } from '../src/raas/mission-outbox-queue'
import { createInMemoryPilotDb } from './helpers/pilot-test-db'

const SERVICE_TOKEN = 'test-operator-service-token-123456'

async function createRedeemedPartner(
  db: ReturnType<typeof createInMemoryPilotDb>['db'],
  partnerLabel: string,
) {
  const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true' }
  const invRes = await server.fetch(
    new Request('http://localhost/billing/invites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${SERVICE_TOKEN}` },
      body: JSON.stringify({ partner_label: partnerLabel }),
    }),
    env,
  )
  const { invite_code } = (await invRes.json()) as { invite_code: string }
  const tenantRes = await server.fetch(
    new Request('http://localhost/billing/tenants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: partnerLabel, invite_code }),
    }),
    env,
  )
  return (await tenantRes.json()) as { tenant_id: string; api_key: string }
}

describe('Pilot feedback loop, operator KPI summary, active_workers & cron/webhook hardening', () => {
  it('records 48h partner feedback on POST /v1/tasks/:id/feedback and computes GET /billing/pilot-kpis', async () => {
    const { db } = createInMemoryPilotDb()
    const partner = await createRedeemedPartner(db, 'Alpha Partner')
    const mockAi = { run: vi.fn(async () => ({ response: 'Completed pilot task output' })) } as unknown as Ai
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true', AI: mockAi }

    const missionIds: string[] = []
    for (let i = 1; i <= 5; i++) {
      const res = await server.fetch(
        new Request('http://localhost/v1/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${partner.api_key}` },
          body: JSON.stringify({ goal: `Pilot mission #${i}` }),
        }),
        env,
      )
      expect(res.status).toBe(201)
      const body = (await res.json()) as { id: string }
      missionIds.push(body.id)

      await processMissionQueueMessage(
        db,
        env,
        {
          mission_id: body.id,
          tenant_id: partner.tenant_id,
          goal: `Pilot mission #${i}`,
          credits_cost: 1,
          enqueued_at: new Date().toISOString(),
        },
        { attempts: 1 },
      )
    }

    for (const [idx, missionId] of missionIds.slice(0, 2).entries()) {
      const fbRes = await server.fetch(
        new Request(`http://localhost/v1/tasks/${missionId}/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${partner.api_key}` },
          body: JSON.stringify({ rating: idx === 0 ? 5 : 4, comment: `Great synthetic run ${idx + 1}` }),
        }),
        env,
      )
      expect(fbRes.status).toBe(201)
      const fbBody = (await fbRes.json()) as { within_48h: boolean; rating: number }
      expect(fbBody.within_48h).toBe(true)
      expect(fbBody.rating).toBe(idx === 0 ? 5 : 4)
    }

    const missingFb = await server.fetch(
      new Request(`http://localhost/v1/tasks/${crypto.randomUUID()}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${partner.api_key}` },
        body: JSON.stringify({ rating: 5 }),
      }),
      env,
    )
    expect(missingFb.status).toBe(404)

    const unauthKpi = await server.fetch(new Request('http://localhost/billing/pilot-kpis'), env)
    expect(unauthKpi.status).toBe(401)

    const kpiRes = await server.fetch(
      new Request('http://localhost/billing/pilot-kpis', { headers: { Authorization: `Bearer ${SERVICE_TOKEN}` } }),
      env,
    )
    expect(kpiRes.status).toBe(200)
    const kpi = (await kpiRes.json()) as {
      targets: { max_partners: number; missions_per_partner_per_week: number; feedback_sla_hours: number }
      totals: Record<string, number>
      partners: Array<{ tenant_id: string; missions_total: number; missions_completed: number; feedback_submitted: number; meets_weekly_target: boolean }>
    }
    expect(kpi.targets.missions_per_partner_per_week).toBe(5)
    expect(kpi.targets.feedback_sla_hours).toBe(48)
    expect(kpi.totals.redeemed_partners).toBe(1)
    expect(kpi.totals.missions_submitted).toBe(5)
    expect(kpi.totals.missions_completed).toBe(5)
    expect(kpi.totals.feedback_count).toBe(2)
    expect(kpi.totals.feedback_within_48h_count).toBe(2)
    expect(kpi.totals.feedback_within_48h_rate).toBe(1)
    expect(kpi.totals.average_rating).toBe(4.5)
    expect(kpi.partners[0]?.meets_weekly_target).toBe(true)
  })

  it('counts planning/executing/verifying missions in GET /health active_workers, guards scheduled(), and applies webhook security headers', async () => {
    const { db, state } = createInMemoryPilotDb()
    const partner = await createRedeemedPartner(db, 'Beta Partner')
    const env = { DB: db, SERVICE_TOKEN, PILOT_MODE: 'true' }
    const now = new Date().toISOString()

    state.missions.push(
      { id: 'm-planning', tenant_id: partner.tenant_id, goal: 'Planning test', status: 'planning', credits_used: 1, total_steps: 2, completed_steps: 0, result: null, created_at: now, completed_at: null },
      { id: 'm-verifying', tenant_id: partner.tenant_id, goal: 'Verifying test', status: 'verifying', credits_used: 1, total_steps: 2, completed_steps: 2, result: null, created_at: now, completed_at: null },
    )

    const healthRes = await server.fetch(new Request('http://localhost/health'), env)
    expect(healthRes.status).toBe(200)
    const health = (await healthRes.json()) as { active_workers: number }
    expect(health.active_workers).toBe(2)

    state.outbox.push({
      id: 'out-1',
      mission_id: 'm-planning',
      tenant_id: partner.tenant_id,
      payload_json: JSON.stringify({ mission_id: 'm-planning', tenant_id: partner.tenant_id, goal: 'Planning test', credits_cost: 1, enqueued_at: now }),
      status: 'pending',
      attempts: 0,
      last_error: null,
      created_at: now,
      updated_at: now,
    })
    const sendSpy = vi.fn(async () => {})
    const mockQueue = { send: sendSpy } as unknown as Queue<MissionQueuePayload>

    await server.scheduled({} as ScheduledEvent, { ...env, MISSION_QUEUE: mockQueue }, {} as ExecutionContext)
    expect(sendSpy).toHaveBeenCalledTimes(1)
    expect(state.outbox[0]?.status).toBe('published')

    for (const path of ['/polar', '/webhooks/polar']) {
      const whRes = await server.fetch(new Request(`http://localhost${path}`, { method: 'POST', body: '{}' }), env)
      expect(whRes.headers.get('X-Content-Type-Options')).toBe('nosniff')
    }
  })
})
