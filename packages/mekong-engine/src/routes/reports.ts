/**
 * reports.ts — Analytics and reporting routes
 * GET /weekly   — 7-day aggregated stats + AI-generated summary
 * GET /overview — real-time dashboard metrics (today)
 */
import { Hono } from 'hono'
import { z } from 'zod'
import { authMiddleware } from '../raas/auth-middleware'
import { LLMClient } from '../core/llm-client'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync, handleExternalApi } from '../types/error'
import {
  weeklyQuerySchema,
  overviewQuerySchema,
  fetchWeeklyStats,
  fetchOverviewStats,
} from './reports-queries'

type Variables = { tenant: Tenant }

export const reportRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

reportRoutes.use('*', authMiddleware)

// GET /reports/weekly — last 7 days aggregated + AI summary
reportRoutes.get('/weekly', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant

  let query: { days: number }
  try {
    query = weeklyQuerySchema.parse(c.req.query())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid query params', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid query params'), 400)
  }

  const days = Math.min(Math.max(query.days ?? 7, 1), 30)
  const tenantId = (tenant as { id: string }).id
  const stats = await fetchWeeklyStats(c.env.DB!, tenantId, days)

  const llm = new LLMClient({
    ai: c.env.AI,
    llmApiKey: c.env.LLM_API_KEY,
    llmBaseUrl: c.env.LLM_BASE_URL,
    model: c.env.DEFAULT_LLM_MODEL,
  })

  const summary = await handleExternalApi(
    () => llm.generate(
      `Business weekly report summary (be concise, 3 sentences max, in Vietnamese):
      - Messages handled: ${stats.messages}
      - New contacts: ${stats.new_contacts}
      - Conversations: ${stats.conversations}
      - Content posts: ${JSON.stringify(stats.content)}`
    )
  )

  return c.json({ period: `${days}d`, stats, ai_summary: summary })
}))

// GET /reports/overview — real-time dashboard: today + totals
reportRoutes.get('/overview', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant

  let query: { include_history: boolean }
  try {
    query = overviewQuerySchema.parse(c.req.query())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Invalid query params', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid query params'), 400)
  }

  const tenantId = (tenant as { id: string }).id
  const response = await fetchOverviewStats(c.env.DB!, tenantId, query.include_history)

  return c.json(response)
}))
