import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { creditMeteringMiddleware } from '../raas/credit-metering-middleware'
import { createMission, getMission, listMissions, updateMissionStatus, estimateCredits } from '../raas/missions'
import { deductCredits, addCredits, getBalance } from '../raas/credits'
import { createSSEStream } from '../raas/sse'
import { z } from 'zod'
import { createError, ERROR_CODES, handleAsync, handleDb, requireResource } from '../types/error'

type Variables = { tenant: Tenant; creditsUsed: number }

const taskRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

// Zod schema for mission creation
const createMissionSchema = z.object({
  goal: z.string().min(1, 'Goal is required').max(2000, 'Goal must be 2000 characters or less'),
})

// Zod schema for list query params
const listTasksQuerySchema = z.object({
  limit: z.coerce.number()
    .int()
    .min(1)
    .max(100)
    .optional()
    .default(20),
  offset: z.coerce.number()
    .int()
    .min(0)
    .optional()
    .default(0),
})

// Zod schema for route params
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
  const tenant = c.get('tenant')
  const body = await c.req.json()
  const parsed = createMissionSchema.safeParse(body)
  if (!parsed.success) return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)

  const credits = estimateCredits(parsed.data.goal)

  // Check balance BEFORE deducting (P0 credit gate)
  const balance = await getBalance(db, tenant.id)
  if (balance < credits) {
    return c.json({
      error: 'Insufficient credits',
      code: 'INSUFFICIENT_CREDITS',
      required: credits,
      balance,
      message: `Task requires ${credits} credits but you only have ${balance}. Please add credits to continue.`
    }, 402)
  }

  const deducted = await deductCredits(db, tenant.id, credits, `mission: ${parsed.data.goal.slice(0, 50)}`)
  if (!deducted) return c.json(createError('INSUFFICIENT_CREDITS', 'Insufficient credits'), 402)

  c.set('creditsUsed', credits)
  const mission = await handleDb(
    () => createMission(db, tenant.id, body.goal, credits),
    'DATABASE_ERROR',
    'Failed to create mission'
  )
  return c.json(mission, 201)
}))

taskRoutes.get('/', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')

  // Validate query params with Zod
  const queryResult = listTasksQuerySchema.safeParse(c.req.query())
  if (!queryResult.success) {
    return c.json(createError('VALIDATION_ERROR', queryResult.error.errors[0]?.message || 'Invalid query parameters'), 400)
  }
  const { limit, offset } = queryResult.data

  const missions = await handleDb(
    () => listMissions(db, tenant.id, limit, offset),
    'DATABASE_ERROR',
    'Failed to list missions'
  )
  return c.json({ missions, limit, offset })
}))

taskRoutes.get('/:id', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')

  // Validate route params
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) {
    return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  }
  const { id } = paramsResult.data

  const mission = await handleDb(
    () => getMission(db, id, tenant.id),
    'DATABASE_ERROR',
    'Failed to fetch mission'
  )
  if (!mission) return c.json(createError('NOT_FOUND', 'Mission not found'), 404)
  return c.json(mission)
}))

taskRoutes.get('/:id/stream', handleAsync(async (c) => {
  const db = c.env.DB!
  const tenant = c.get('tenant')

  // Validate route params
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) {
    return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  }
  const { id } = paramsResult.data

  const mission = await handleDb(
    () => getMission(db, id, tenant.id),
    'DATABASE_ERROR',
    'Failed to fetch mission'
  )
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
  const tenant = c.get('tenant')

  // Validate route params
  const paramsResult = idParamSchema.safeParse({ id: c.req.param('id') })
  if (!paramsResult.success) {
    return c.json(createError('VALIDATION_ERROR', paramsResult.error.errors[0]?.message || 'Invalid route parameters'), 400)
  }
  const { id } = paramsResult.data

  const mission = await handleDb(
    () => getMission(db, id, tenant.id),
    'DATABASE_ERROR',
    'Failed to fetch mission'
  )
  if (!mission) return c.json(createError('NOT_FOUND', 'Mission not found'), 404)
  if (mission.status !== 'pending') return c.json(createError('CONFLICT', 'Only pending missions can be cancelled'), 409)

  await handleDb(
    () => updateMissionStatus(db, id, 'failed', 'Cancelled by user'),
    'DATABASE_ERROR',
    'Failed to cancel mission'
  )
  await handleDb(
    () => addCredits(db, tenant.id, mission.credits_used, 'refund: cancelled mission'),
    'DATABASE_ERROR',
    'Failed to refund credits'
  )
  return c.json({ id, status: 'cancelled', refunded: mission.credits_used })
}))

export { taskRoutes }
