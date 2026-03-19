import { Hono } from 'hono'
import { cors } from 'hono/cors'
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
  MOMO_SECRET_KEY?: string
  MOMO_ACCESS_KEY?: string
  VNPAY_HASH_SECRET?: string
}

const app = new Hono<{ Bindings: Bindings }>()

// Global error handler — catch JSON parse errors, unexpected crashes
app.onError((err, c) => {
  if (err instanceof SyntaxError) {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }
  return c.json({ error: 'Internal server error' }, 500)
})

// Middleware
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
  if (c.env.DB) {
    await c.env.DB.exec(
      `CREATE TABLE IF NOT EXISTS tenant_settings (tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE, llm_provider TEXT NOT NULL DEFAULT 'workers-ai', llm_api_key_encrypted TEXT, llm_base_url TEXT, llm_model TEXT, updated_at TEXT NOT NULL DEFAULT (datetime('now')))`,
    ).catch(() => {})
  }
  return c.json({
    status: 'ok',
    version: '3.2.0',
    engine: 'mekong-pev',
    runtime: 'cloudflare-workers',
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

  const { MekongEngineAdapter } = await import('./core/mekong-engine-adapter')
  const body = await c.req.json<{ goal: string }>()
  if (!body.goal) return c.json({ error: 'Missing goal' }, 400)

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
