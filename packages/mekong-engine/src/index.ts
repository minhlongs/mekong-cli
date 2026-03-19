import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { z } from 'zod'
import { payloadSizeLimit } from './raas/payload-limiter'
import { createError } from './types/error'
import { taskRoutes } from './routes/tasks'
import { agentRoutes } from './routes/agents'
import { billingRoutes } from './routes/billing'
import { settingsRoutes } from './routes/settings'
import { chatRoutes } from './routes/chat'
import { contentRoutes } from './routes/content'
import { crmRoutes } from './routes/crm'
import { reportRoutes } from './routes/reports'
import { onboardingRoutes } from './routes/onboarding'
import { paymentVnRoutes } from './routes/payment-vn'
import { governanceRoutes } from './routes/governance'
import { ledgerRoutes } from './routes/ledger'
import { equityRoutes } from './routes/equity'
import { revenueRoutes } from './routes/revenue'
import { fundingRoutes } from './routes/funding'
import { matchingRoutes } from './routes/matching'
import { conflictRoutes } from './routes/conflicts'
import { decentralRoutes } from './routes/decentralization'
import { rbacRoutes } from './routes/rbac'
import { constitutionRoutes } from './routes/constitution'
import { marketplaceRoutes } from './routes/marketplace'
import { raasRoutes, webhookRoutes } from './routes/raas'
import { formatPrometheusMetrics, getMetrics, requestLoggingMiddleware, metricsMiddleware } from './lib/monitoring'
import { handleAsync } from './types/error'
import type { D1Database, KVNamespace, R2Bucket, Ai, AiModels, ScheduledEvent, ExecutionContext } from '@cloudflare/workers-types'

// Cloudflare bindings — all optional until resources created in dashboard
export type Bindings = {
  DB?: D1Database
  RATE_LIMIT_KV?: KVNamespace
  RECIPES?: R2Bucket
  AI?: Ai
  LLM_API_KEY?: string
  LLM_BASE_URL?: string
  SERVICE_TOKEN?: string
  POLAR_WEBHOOK_SECRET?: string
  ENVIRONMENT?: string
  DEFAULT_LLM_MODEL?: string
  FB_VERIFY_TOKEN?: string
  FB_APP_SECRET?: string
  ZALO_APP_SECRET?: string
  ZALO_SECRET?: string
  MOMO_SECRET_KEY?: string
  MOMO_ACCESS_KEY?: string
  VNPAY_HASH_SECRET?: string
}

// Track server start time for uptime calculation
const START_TIME = Date.now()

const app = new Hono<{ Bindings: Bindings }>()

// Zod schema for /cmd endpoint validation
const cmdSchema = z.object({
  goal: z.string()
    .min(1, 'Goal is required')
    .max(5000, 'Goal must be 5000 characters or less'),
  params: z.record(z.unknown())
    .optional()
    .describe('Optional parameters for the command'),
})

// Global error handler — catch JSON parse errors, unexpected crashes
app.onError((err, c) => {
  if (err instanceof SyntaxError) {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }
  return c.json({ error: 'Internal server error' }, 500)
})

// Middleware
app.use('*', payloadSizeLimit())
app.use('*', cors())

// Root — service info
app.get('/', (c) => c.json({
  service: 'mekong-engine',
  version: '3.2.0',
  docs: 'https://docs.agencyos.network',
  health: '/health',
  api: '/v1',
}))

// Health check + auto-migrate tenant_settings
app.get('/health', async (c) => {
  // Auto-migrate tenant_settings table
  if (c.env.DB) {
    await c.env.DB.exec(
      `CREATE TABLE IF NOT EXISTS tenant_settings (tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, llm_provider TEXT NOT NULL DEFAULT 'workers-ai', llm_api_key_encrypted TEXT, llm_base_url TEXT, llm_model TEXT, updated_at TEXT NOT NULL DEFAULT (datetime('now')))`,
    ).catch(() => {})
  }

  // Calculate uptime in seconds
  const uptime = Math.floor((Date.now() - START_TIME) / 1000)

  // Check database health with latency measurement
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

  // Count active workers (running missions)
  let activeWorkers = 0
  if (c.env.DB) {
    try {
      const result = await c.env.DB
        .prepare("SELECT COUNT(*) as count FROM missions WHERE status = 'running'")
        .first<{ count: number }>()
      activeWorkers = result?.count ?? 0
    } catch {
      activeWorkers = 0
    }
  }

  return c.json({
    status: 'ok',
    version: '3.2.0',
    uptime: uptime,
    database: {
      connected: databaseConnected,
      latency_ms: databaseLatencyMs,
    },
    active_workers: activeWorkers,
    bindings: {
      d1: !!c.env.DB,
      kv: !!c.env.RATE_LIMIT_KV,
      r2: !!c.env.RECIPES,
      ai: !!c.env.AI,
      llm: !!c.env.LLM_API_KEY,
    },
  })
})

// PEV Engine routes — BYOK: tenant key → global key → Workers AI
// Uses MekongEngineAdapter from @mekong/cli-core
app.post('/cmd', async (c) => {
  if (!c.env.AI && !c.env.LLM_API_KEY) return c.json({ error: 'No LLM provider configured (need AI binding or LLM_API_KEY)' }, 503)

  // Validate request body with Zod schema
  let body: z.infer<typeof cmdSchema>
  try {
    const json = await c.req.json()
    body = cmdSchema.parse(json)
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const { MekongEngineAdapter } = await import('./core/mekong-engine-adapter')

  // BYOK fallback chain: tenant settings → global env → Workers AI
  let llmApiKey = c.env.LLM_API_KEY
  let llmBaseUrl = c.env.LLM_BASE_URL ?? 'https://api.openai.com/v1'
  let model = c.env.DEFAULT_LLM_MODEL ?? '@cf/meta/llama-3.1-8b-instruct'

  const authHeader = c.req.header('Authorization')
  if (authHeader?.startsWith('Bearer ') && c.env.DB && c.env.SERVICE_TOKEN) {
    const { getLLMSettings } = await import('./raas/tenant-settings')
    const { getByApiKey } = await import('./raas/tenant')
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

  const adapter = new MekongEngineAdapter({
    AI: c.env.AI,
    LLM_API_KEY: llmApiKey,
    LLM_BASE_URL: llmBaseUrl,
    DEFAULT_LLM_MODEL: model,
  })

  await adapter.init()
  const result = await adapter.run(body.goal)
  return c.json(result)
})

// Direct Workers AI test
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

// RaaS routes — Phase 3-5
app.route('/v1/tasks', taskRoutes)
app.route('/v1/agents', agentRoutes)
app.route('/v1/settings', settingsRoutes)
app.route('/billing', billingRoutes)
app.route('/v1/chat', chatRoutes)
app.route('/v1/content', contentRoutes)
app.route('/v1/crm', crmRoutes)
app.route('/v1/reports', reportRoutes)
app.route('/v1/onboard', onboardingRoutes)
app.route('/payment', paymentVnRoutes)
app.route('/v1/governance', governanceRoutes)
app.route('/v1/ledger', ledgerRoutes)
app.route('/v1/equity', equityRoutes)
app.route('/v1/revenue', revenueRoutes)
app.route('/v1/funding', fundingRoutes)
app.route('/v1/matching', matchingRoutes)
app.route('/v1/conflicts', conflictRoutes)
app.route('/v1/decentralization', decentralRoutes)
app.route('/v1/rbac', rbacRoutes)
app.route('/v1/constitution', constitutionRoutes)
app.route('/v1/marketplace', marketplaceRoutes)
app.route('/v1/raas', raasRoutes)
app.route('/', webhookRoutes)

// Metrics endpoint for Prometheus scraping
app.get('/metrics', (c) => {
  const metrics = getMetrics()
  const prometheusFormat = formatPrometheusMetrics(metrics)
  return c.body(prometheusFormat, 200, {
    'Content-Type': 'text/plain; version=0.0.4',
  })
})

// Cron Trigger — auto-publish approved content
export default {
  fetch: app.fetch,
  async scheduled(event: ScheduledEvent, env: Bindings, ctx: ExecutionContext) {
    if (!env.DB) return
    const now = new Date().toISOString()
    const posts = await env.DB.prepare(
      'SELECT * FROM content_posts WHERE status = ? AND scheduled_at <= ? LIMIT 5'
    ).bind('approved', now).all()
    for (const post of posts.results || []) {
      const channel = await env.DB.prepare(
        'SELECT * FROM channels WHERE tenant_id = ? AND type = ? AND active = 1 LIMIT 1'
      ).bind(post.tenant_id, 'facebook').first()
      if (channel?.access_token_encrypted) {
        try {
          await fetch(`https://graph.facebook.com/v19.0/${channel.external_id}/feed`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: post.content_text, access_token: channel.access_token_encrypted }),
          })
          await env.DB.prepare('UPDATE content_posts SET status = ?, published_at = ? WHERE id = ?')
            .bind('published', now, post.id).run()
        } catch (e) { /* log error */ }
      }
    }
  },
}
