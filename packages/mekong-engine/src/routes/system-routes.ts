import { Hono } from 'hono'
import { z } from 'zod'
import type { AiModels } from '@cloudflare/workers-types'
import type { Bindings } from '../index'
import { createError, handleAsync } from '../types/error'
import {
  getMetrics as getObservabilityMetrics,
  formatPrometheusMetrics as formatObservabilityMetrics,
} from '../observability/metrics'
import { getAlertStatus } from '../observability/alerts'

const START_TIME = Date.now()

const cmdSchema = z.object({
  goal: z.string()
    .min(1, 'Goal is required')
    .max(5000, 'Goal must be 5000 characters or less'),
  params: z.record(z.unknown())
    .optional()
    .describe('Optional parameters for the command'),
})

export function registerSystemRoutes(app: Hono<{ Bindings: Bindings }>): void {
  app.get('/', (c) => c.json({
    service: 'mekong-engine',
    version: '3.2.0',
    docs: 'https://www.mekongmind.com/docs',
    health: '/health',
    api: '/v1',
  }))

  app.get('/v1/pricing', (c) => c.json({
    tiers: [
      { id: 'free', name: 'Free', price: 0, credits: 10, description: 'Try it out', checkout_url: 'https://buy.polar.sh/a09a5fa0-63db-42a4-a547-3b1523ffc263' },
      { id: 'agencyos-starter', name: 'Starter', price: 29, credits: 50, description: 'Solo non-tech user', checkout_url: 'https://buy.polar.sh/c06a03a3-25cd-4cd3-a13d-e795ee592a4e' },
      { id: 'agencyos-pro', name: 'Pro', price: 99, credits: 200, description: 'Small agency', checkout_url: 'https://buy.polar.sh/52b7404c-b420-48cc-a382-ab4b5979f766' },
      { id: 'agencyos-agency', name: 'Agency', price: 199, credits: 500, description: 'Growing agency' },
      { id: 'agencyos-master', name: 'Master', price: 399, credits: 1000, description: 'Premium agency' },
    ],
    credit_packs: [
      { id: 'credits-10', credits: 10, price: 5 },
      { id: 'credits-50', credits: 50, price: 20 },
      { id: 'credits-100', credits: 100, price: 35 },
      { id: 'credits-500', credits: 500, price: 150 },
    ],
    credit_costs: { simple: 1, standard: 3, complex: 5 },
    checkout_url_template: 'https://buy.polar.sh',
  }))

  app.get('/v1/auth/me', (c) => {
    const auth = c.req.header('authorization') || ''
    if (!auth) return c.json({ authenticated: false, message: 'missing Authorization header' }, 200)
    return c.json({ authenticated: true, message: 'token-present' }, 200)
  })

  app.get('/healthz', (c) => c.json({ status: 'ok', version: '3.2.0' }))

  app.get('/health', async (c) => {
    if (c.env.DB) {
      await c.env.DB.exec(
        `CREATE TABLE IF NOT EXISTS tenant_settings (tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, llm_provider TEXT NOT NULL DEFAULT 'workers-ai', llm_api_key_encrypted TEXT, llm_base_url TEXT, llm_model TEXT, updated_at TEXT NOT NULL DEFAULT (datetime('now')))`,
      ).catch(() => {})
    }

    const uptime = Math.floor((Date.now() - START_TIME) / 1000)
    let databaseConnected = false
    let databaseLatencyMs: number | null = null

    if (c.env.DB) {
      const dbStart = Date.now()
      try {
        await c.env.DB.prepare('SELECT 1 as health').first()
        databaseConnected = true
        databaseLatencyMs = Date.now() - dbStart
      } catch {
        databaseConnected = false
      }
    }

    let activeWorkers = 0
    if (c.env.DB) {
      try {
        const result = await c.env.DB
          .prepare("SELECT COUNT(*) as count FROM missions WHERE status IN ('planning', 'executing', 'verifying', 'running')")
          .first<{ count: number }>()
        activeWorkers = result?.count ?? 0
      } catch {
        activeWorkers = 0
      }
    }

    const BUILD_SHA = (c.env as Record<string, string>)?.BUILD_SHA || 'dev'

    return c.json({
      status: 'ok',
      version: '3.2.0',
      build: BUILD_SHA,
      uptime,
      database: { connected: databaseConnected, latency_ms: databaseLatencyMs },
      active_workers: activeWorkers,
      bindings: {
        d1: !!c.env.DB,
        kv: !!c.env.RATE_LIMIT_KV,
        r2: !!c.env.RECIPES,
        ai: !!c.env.AI,
        llm: !!c.env.LLM_API_KEY,
        queue: !!c.env.MISSION_QUEUE,
        pilot_mode: c.env.PILOT_MODE !== 'false',
      },
      pilot: {
        invite_only: c.env.PILOT_MODE !== 'false',
        llm_only: c.env.PILOT_MODE !== 'false',
      },
    })
  })

  app.post('/cmd', async (c) => {
    if (!c.env.AI && !c.env.LLM_API_KEY) return c.json({ error: 'No LLM provider configured (need AI binding or LLM_API_KEY)' }, 503)

    let body: z.infer<typeof cmdSchema>
    try {
      const json = await c.req.json()
      body = cmdSchema.parse(json)
    } catch (error) {
      if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
      return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
    }

    const { MekongEngineAdapter } = await import('../core/mekong-engine-adapter')
    let llmApiKey = c.env.LLM_API_KEY
    let llmBaseUrl = c.env.LLM_BASE_URL ?? 'https://api.openai.com/v1'
    let model = c.env.DEFAULT_LLM_MODEL ?? '@cf/meta/llama-3.1-8b-instruct'

    const authHeader = c.req.header('Authorization')
    if (authHeader?.startsWith('Bearer ') && c.env.DB && c.env.SERVICE_TOKEN) {
      const { getLLMSettings } = await import('../raas/tenant-settings')
      const { getByApiKey } = await import('../raas/tenant')
      const tenant = await getByApiKey(c.env.DB, authHeader.slice(7).trim())
      if (tenant) {
        const settings = await getLLMSettings(c.env.DB, tenant.id, c.env.SERVICE_TOKEN)
        if (settings?.apiKey) {
          llmApiKey = settings.apiKey
          llmBaseUrl = settings.baseUrl || llmBaseUrl
          model = settings.model || model
        }
      }
    }

    const adapter = new MekongEngineAdapter({ AI: c.env.AI, LLM_API_KEY: llmApiKey, LLM_BASE_URL: llmBaseUrl, DEFAULT_LLM_MODEL: model })
    await adapter.init()
    const result = await adapter.run(body.goal)
    return c.json(result)
  })

  app.get('/ai/test', async (c) => {
    if (!c.env.AI) return c.json({ error: 'AI binding not available' }, 503)
    try {
      const result = await c.env.AI.run('@cf/meta/llama-3.1-8b-instruct' as keyof AiModels, {
        messages: [{ role: 'user', content: 'Say hello in Vietnamese in one sentence' }],
        max_tokens: 100,
      })
      return c.json({ ok: true, result })
    } catch (err) {
      return c.json({ ok: false, error: String(err) }, 500)
    }
  })

  app.get('/metrics', handleAsync(async (c) => {
    const authHeader = c.req.header('Authorization')
    if (!authHeader?.startsWith('Bearer ') || authHeader.slice(7) !== c.env.SERVICE_TOKEN) {
      return c.json({ error: 'Unauthorized - SERVICE_TOKEN required' }, 401)
    }
    const obsMetrics = getObservabilityMetrics()
    return c.body(formatObservabilityMetrics(obsMetrics), 200, { 'Content-Type': 'text/plain; version=0.0.4' })
  }))

  app.get('/v1/observability/alerts', handleAsync(async (c) => {
    const authHeader = c.req.header('Authorization')
    if (!authHeader?.startsWith('Bearer ')) return c.json({ error: 'Unauthorized' }, 401)
    return c.json(getAlertStatus())
  }))

  app.post('/v1/observability/alerts/check', handleAsync(async (c) => {
    const authHeader = c.req.header('Authorization')
    if (!authHeader?.startsWith('Bearer ') || authHeader.slice(7) !== c.env.SERVICE_TOKEN) {
      return c.json({ error: 'Unauthorized - SERVICE_TOKEN required' }, 401)
    }
    const { checkAlerts, sendAlertsToSlack } = await import('../observability/alerts')
    const metrics = getObservabilityMetrics()
    const triggered = checkAlerts(metrics)
    if (triggered.length > 0 && c.env.SLACK_WEBHOOK_URL) {
      c.executionCtx.waitUntil(sendAlertsToSlack([c.env.SLACK_WEBHOOK_URL], triggered))
    }
    return c.json({ metrics_timestamp: metrics.timestamp, alerts_triggered: triggered })
  }))
}
