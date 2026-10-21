import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { creditMeteringMiddleware } from '../raas/credit-metering-middleware'
import { createMission, getMission, listMissions, updateMissionStatus, cancelPendingMission, estimateCredits } from '../raas/missions'
import { deductMissionCreditsOnce, refundMissionCreditsOnce, getBalance } from '../raas/credits'
import { enqueueMissionOutbox } from '../raas/mission-outbox-queue'
import { submitMissionFeedback } from '../raas/mission-feedback'
import { isPilotModeEnabled } from '../raas/invite-codes'
import { RecipeStepSchema } from '../types/recipe'
import { createSSEStream } from '../raas/sse'
import { z } from 'zod'
import { createError, handleAsync, handleDb } from '../types/error'

type Variables = { tenant: Tenant; creditsUsed: number }

const taskRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

const createMissionSchema = z.object({
  goal: z.string().min(1, 'Goal is required').max(2000, 'Goal must be 2000 characters or less'),
  steps: z.array(RecipeStepSchema).optional(),
})

const missionFeedbackSchema = z.object({
  rating: z.number().int().min(1).max(5),
  comment: z.string().max(1000).optional(),
})

const listTasksQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  offset: z.coerce.number().int().min(0).optional().default(0),
})

const idParamSchema = z.object({
  id: z.string().uuid('Invalid mission ID format'),
})

// Guard: DB required for all task routes
taskRoutes.use('*', async (c, next) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 database not configured'), 503)
  await next()
})
taskRoutes.use('*', authMiddleware)

taskRoutes.post('/', creditMeteringMiddleware, handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant') as Tenant
  const body = await c.req.json()
  const parsed = createMissionSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)

  if (isPilotModeEnabled(c.env.PILOT_MODE) && parsed.data.steps?.some((s) => s.mode !== 'llm')) {
    return c.json(createError('VALIDATION_ERROR', 'PILOT_STEP_MODE_REJECTED: Only llm step mode is permitted in pilot mode'), 400)
  }

  const credits = estimateCredits(parsed.data.goal)
  const tenantId = (tenant as { id: string }).id
  const balance = await getBalance(db, tenantId)
  if (balance < credits) {
    return c.json({
      error: 'Insufficient credits',
      code: 'INSUFFICIENT_CREDITS',
      required: credits,
      balance,
      message: `Task requires ${credits} credits but you only have ${balance}. Please add credits to continue.`,
    }, 402)
  }

  const mission = await handleDb(() => createMission(db, tenantId, parsed.data.goal, credits), 'DATABASE_ERROR', 'Failed to create mission')
  const debit = await deductMissionCreditsOnce(db, tenantId, mission.id, credits, `mission:${mission.id}: ${parsed.data.goal.slice(0, 50)}`)
  if (!debit.deducted) {
    await updateMissionStatus(db, mission.id, 'failed', 'Insufficient credits')
    return c.json(createError('INSUFFICIENT_CREDITS', 'Insufficient credits'), 402)
  }

  await enqueueMissionOutbox(db, c.env.MISSION_QUEUE, {
    mission_id: mission.id,
    tenant_id: tenantId,
    goal: parsed.data.goal,
    credits_cost: credits,
    steps: parsed.data.steps,
    enqueued_at: new Date().toISOString(),
  })

  return c.json(mission, 201)
}))

taskRoutes.get('/', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant') as Tenant

  const queryResult = listTasksQuerySchema.safeParse(c.req.query())
  if (!queryResult.success) return c.json(createError('VALIDATION_ERROR', queryResult.error.errors[0]?.message || 'Invalid query parameters'), 400)
  const { limit, offset } = queryResult.data
  const missions = await handleDb(() => listMissions(db, (tenant as { id: string }).id, limit, offset), 'DATABASE_ERROR', 'Failed to list missions')
  return c.json({ missions, limit, offset })
}))

taskRoutes.get('/:id', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant') as Tenant
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  const { id } = paramsResult.data
  const mission = await handleDb(() => getMission(db, id, (tenant as { id: string }).id), 'DATABASE_ERROR', 'Failed to fetch mission')
  if (!mission) return c.json(createError('NOT_FOUND', 'Mission not found'), 404)
  return c.json(mission)
}))

taskRoutes.get('/:id/stream', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant') as Tenant
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  const { id } = paramsResult.data
  const mission = await handleDb(() => getMission(db, id, (tenant as { id: string }).id), 'DATABASE_ERROR', 'Failed to fetch mission')
  if (!mission) return c.json(createError('NOT_FOUND', 'Mission not found'), 404)

  const { readable, send, close } = createSSEStream()
  send('status', { id: mission.id, status: mission.status, result: mission.result })
  close()

  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive' },
  })
}))

taskRoutes.post('/:id/cancel', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant') as Tenant

  // Validate route params
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) {
    return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  }
  const { id } = paramsResult.data

  const mission = await handleDb(
    () => getMission(db, id, (tenant as { id: string }).id),
    'DATABASE_ERROR',
    'Failed to fetch mission'
  )
  if (!mission) return c.json(createError('NOT_FOUND', 'Mission not found'), 404)
  if (mission.status !== 'pending') return c.json(createError('CONFLICT', 'Only pending missions can be cancelled'), 409)

  const cancelled = await handleDb(() => cancelPendingMission(db, id), 'DATABASE_ERROR', 'Failed to cancel mission')
  if (!cancelled) return c.json(createError('CONFLICT', 'Mission is no longer pending'), 409)

  const refund = await handleDb(
    () => refundMissionCreditsOnce(db, (tenant as { id: string }).id, id, mission.credits_used, `refund: cancelled mission ${id}`),
    'DATABASE_ERROR',
    'Failed to refund credits'
  )
  return c.json({ id, status: 'cancelled', refunded: refund.refunded ? mission.credits_used : 0 })
}))

taskRoutes.post('/:id/feedback', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant') as Tenant
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  const body = await c.req.json().catch(() => ({}))
  const parsed = missionFeedbackSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid feedback payload'), 400)
  const record = await handleDb(
    () => submitMissionFeedback(db, (tenant as { id: string }).id, paramsResult.data.id, parsed.data.rating, parsed.data.comment),
    'DATABASE_ERROR',
    'Failed to record mission feedback',
  )
  if (!record) return c.json(createError('NOT_FOUND', 'Mission not found'), 404)
  return c.json(record, 201)
}))

export { taskRoutes }
