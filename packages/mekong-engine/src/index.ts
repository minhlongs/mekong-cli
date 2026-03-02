import { Hono } from 'hono'
import { cors } from 'hono/cors'

// Cloudflare bindings type
export type Bindings = {
  DB: D1Database
  RATE_LIMIT_KV: KVNamespace
  RECIPES: R2Bucket
  LLM_API_KEY: string
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

// Placeholder routes — implemented in Phase 2-5
app.post('/cmd', (c) => c.json({ error: 'Not implemented' }, 501))
app.get('/v1/agents', (c) => c.json({ agents: [] }))
app.post('/v1/tasks', (c) => c.json({ error: 'Not implemented' }, 501))
app.get('/v1/tasks/:id', (c) => c.json({ error: 'Not implemented' }, 501))

export default app
