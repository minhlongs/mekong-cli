import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { taskRoutes } from './routes/tasks'
import { agentRoutes } from './routes/agents'
import { billingRoutes } from './routes/billing'

// Cloudflare bindings type
export type Bindings = {
  DB: D1Database
  RATE_LIMIT_KV: KVNamespace
  RECIPES: R2Bucket
  LLM_API_KEY: string
  LLM_BASE_URL: string
  SERVICE_TOKEN: string
  POLAR_WEBHOOK_SECRET: string
  ENVIRONMENT: string
  DEFAULT_LLM_MODEL: string
}

const app = new Hono<{ Bindings: Bindings }>()

// Middleware
app.use('*', cors())

// Health check
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    version: '3.0.0',
    engine: 'mekong-pev',
    runtime: 'cloudflare-workers',
  })
})

// PEV Engine routes
app.post('/cmd', async (c) => {
  const { RecipeOrchestrator } = await import('./core/recipe-orchestrator')
  const body = await c.req.json<{ goal: string }>()
  if (!body.goal) return c.json({ error: 'Missing goal' }, 400)

  const orchestrator = new RecipeOrchestrator({
    llmApiKey: c.env.LLM_API_KEY,
    llmBaseUrl: c.env.LLM_BASE_URL,
    model: c.env.DEFAULT_LLM_MODEL,
  })

  const result = await orchestrator.runFromGoal(body.goal)
  return c.json(result)
})

// RaaS routes — Phase 3-5
app.route('/v1/tasks', taskRoutes)
app.route('/v1/agents', agentRoutes)
app.route('/billing', billingRoutes)

export default app
