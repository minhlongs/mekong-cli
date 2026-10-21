import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { payloadSizeLimit } from './raas/payload-limiter'
import { authRoutes } from './routes/auth'
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
import { analyticsRoutes } from './routes/analytics'
import { commandFabricRoutes } from './routes/command-fabric'
import { registerSystemRoutes } from './routes/system-routes'
import { requestLoggingMiddleware, metricsMiddleware } from './lib/monitoring'
import { rateLimitMiddleware } from './middleware/rate-limit'
import { apiSecurityHeaders } from './middleware/security'
import { auditMiddleware } from './security/audit-log'
import { initAlerts } from './observability/alerts'
import { isPilotModeEnabled } from './raas/invite-codes'
import { handleMissionQueueBatch, republishPendingOutbox, type MissionQueuePayload } from './raas/mission-outbox-queue'
import type { D1Database, KVNamespace, R2Bucket, Ai, ScheduledEvent, ExecutionContext, Queue, MessageBatch } from '@cloudflare/workers-types'

export type Bindings = {
  DB?: D1Database
  RATE_LIMIT_KV?: KVNamespace
  RECIPES?: R2Bucket
  AI?: Ai
  MISSION_QUEUE?: Queue<MissionQueuePayload>
  PILOT_MODE?: string
  PILOT_INVITE_ONLY?: string
  PILOT_LLM_ONLY?: string
  PILOT_MAX_INVITES?: string
  LLM_API_KEY?: string
  LLM_BASE_URL?: string
  SERVICE_TOKEN?: string
  NOWPAYMENTS_WEBHOOK_SECRET?: string
  POLAR_WEBHOOK_SECRET?: string
  JWT_SECRET?: string
  ENVIRONMENT?: string
  DEFAULT_LLM_MODEL?: string
  FB_VERIFY_TOKEN?: string
  FB_APP_SECRET?: string
  ZALO_APP_SECRET?: string
  ZALO_SECRET?: string
  MOMO_SECRET_KEY?: string
  MOMO_ACCESS_KEY?: string
  VNPAY_HASH_SECRET?: string
  PAYMENT_METADATA_SECRET?: string
  SLACK_WEBHOOK_URL?: string
  COMMAND_FABRIC_CANONICAL?: string
  COMMAND_FABRIC_ADAPTERS?: string
  COMMAND_FABRIC_MCP?: string
}

const app = new Hono<{ Bindings: Bindings }>()

app.onError((err, c) => {
  if (err instanceof SyntaxError) {
    return c.json({ error: 'Invalid JSON in request body' }, 400)
  }
  return c.json({ error: 'Internal server error' }, 500)
})

app.use('*', payloadSizeLimit())
app.use('*', cors({
  origin: [
    'https://mekongmind.com',
    'https://www.mekongmind.com',
    'https://ide.mekongmind.com',
    'https://docs.mekongmind.com',
    'https://api.cashclaw.cc',
    'http://localhost:4321',
    'http://localhost:3001',
  ],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
  maxAge: 86400,
}))
app.use('*', metricsMiddleware)
app.use('*', requestLoggingMiddleware)
app.use('*', rateLimitMiddleware())
app.use('*', apiSecurityHeaders)
app.use('/v1/*', auditMiddleware())
app.use('/billing/*', auditMiddleware())

initAlerts()
registerSystemRoutes(app)

app.route('/auth', authRoutes)
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
app.route('/v1/analytics', analyticsRoutes)
app.route('/v1/command-fabric', commandFabricRoutes)
app.route('/', webhookRoutes)

export default {
  fetch: app.fetch,
  async queue(batch: MessageBatch<MissionQueuePayload>, env: Bindings, _ctx: ExecutionContext) {
    await handleMissionQueueBatch(batch, env)
  },
  async scheduled(_event: ScheduledEvent, env: Bindings, _ctx: ExecutionContext) {
    if (!env.DB) return
    await republishPendingOutbox(env.DB, env.MISSION_QUEUE)
    if (isPilotModeEnabled(env.PILOT_MODE)) return

    const now = new Date().toISOString()
    const posts = await env.DB.prepare(
      'SELECT * FROM content_posts WHERE status = ? AND scheduled_at <= ? LIMIT 5',
    ).bind('approved', now).all()
    for (const post of posts.results || []) {
      const channel = await env.DB.prepare(
        'SELECT * FROM channels WHERE tenant_id = ? AND type = ? AND active = 1 LIMIT 1',
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
        } catch {
          // Ignore transient Facebook Graph errors
        }
      }
    }
  },
}
