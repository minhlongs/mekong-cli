import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { creditMeteringMiddleware } from '../raas/credit-metering-middleware'
import { createMission, getMission, listMissions, updateMissionStatus, estimateCredits } from '../raas/missions'
import { deductCredits, addCredits } from '../raas/credits'
import { createSSEStream } from '../raas/sse'
import { z } from 'zod'

type Variables = { tenant: Tenant; creditsUsed: number }

const taskRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

// Zod schema for mission creation
const createMissionSchema = z.object({
  goal: z.string().min(1, 'Goal is required').max(2000, 'Goal must be 2000 characters or less'),
})

// Guard: DB required for all task routes
taskRoutes.use('*', async (c, next) => {
  if (!c.env.DB) return c.json({ error: 'D1 database not configured' }, 503)
  await next()
})
taskRoutes.use('*', authMiddleware)

taskRoutes.post('/', creditMeteringMiddleware, async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')
  const body = await c.req.json()
  const parsed = createMissionSchema.safeParse(body)
  if (!parsed.success) return c.json({ error: parsed.error.errors[0]?.message || 'Invalid request' }, 400)

  const credits = estimateCredits(parsed.data.goal)
  const deducted = await deductCredits(db, tenant.id, credits, `mission: ${parsed.data.goal.slice(0, 50)}`)
  if (!deducted) return c.json({ error: 'Insufficient credits' }, 402)

  c.set('creditsUsed', credits)
  const mission = await createMission(db, tenant.id, body.goal, credits)
  return c.json(mission, 201)
})

taskRoutes.get('/', async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')
  const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '20', 10) || 20, 1), 100)
  const offset = Math.max(parseInt(c.req.query('offset') ?? '0', 10) || 0, 0)
  const missions = await listMissions(db, tenant.id, limit, offset)
  return c.json({ missions, limit, offset })
})

taskRoutes.get('/:id', async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')
  const id = c.req.param('id')
  const mission = await getMission(db, id, tenant.id)
  if (!mission) return c.json({ error: 'Mission not found' }, 404)
  return c.json(mission)
})

taskRoutes.get('/:id/stream', async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')
  const id = c.req.param('id')
  const mission = await getMission(db, id, tenant.id)
  if (!mission) return c.json({ error: 'Mission not found' }, 404)

  const { readable, send, close } = createSSEStream()
  send('status', { id: mission.id, status: mission.status, result: mission.result })
  close()

  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' },
  })
})

taskRoutes.post('/:id/cancel', async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')
  const id = c.req.param('id')
  const mission = await getMission(db, id, tenant.id)
  if (!mission) return c.json({ error: 'Mission not found' }, 404)
  if (mission.status !== 'pending') return c.json({ error: 'Only pending missions can be cancelled' }, 409)

  await updateMissionStatus(db, id, 'failed', 'Cancelled by user')
  await addCredits(db, tenant.id, mission.credits_used, 'refund: cancelled mission')
  return c.json({ id, status: 'cancelled', refunded: mission.credits_used })
})

export { taskRoutes }
