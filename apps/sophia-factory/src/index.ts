import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import type { Bindings } from './bindings'

const app = new Hono<{ Bindings: Bindings }>()

// Middleware
app.use('*', logger())
app.use('*', cors())

// Health check
app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    version: '0.1.0',
    database: 'd1',
    auth: 'supabase'
  })
})

// Auth webhook handler (from Supabase)
app.post('/webhooks/auth', async (c) => {
  const body = await c.req.json()
  const { user_id, email, org_id } = body
  
  // Link Supabase Auth user to D1 users table
  await c.env.DB
    .prepare('INSERT OR REPLACE INTO users (id, email, org_id, role) VALUES (?, ?, ?, ?)')
    .bind(user_id, email, org_id, 'member')
    .run()
  
  return c.json({ received: true })
})

// Organizations API
app.post('/api/organizations', async (c) => {
  const { name, slug } = await c.req.json()
  
  const org = await c.env.DB
    .prepare('INSERT INTO organizations (id, name, slug) VALUES (?, ?, ?) RETURNING *')
    .bind(crypto.randomUUID(), name, slug)
    .first()
  
  return c.json({ data: org })
})

app.get('/api/organizations/:slug', async (c) => {
  const slug = c.req.param('slug')
  
  const org = await c.env.DB
    .prepare('SELECT * FROM organizations WHERE slug = ?')
    .bind(slug)
    .first()
  
  if (!org) {
    return c.json({ error: 'Organization not found' }, 404)
  }
  
  return c.json({ data: org })
})

// Proposals API
app.get('/api/organizations/:orgId/proposals', async (c) => {
  const orgId = c.req.param('orgId')
  
  const { results } = await c.env.DB
    .prepare('SELECT * FROM proposals WHERE org_id = ? ORDER BY created_at DESC')
    .bind(orgId)
    .all()
  
  return c.json({ data: results })
})

app.post('/api/organizations/:orgId/proposals', async (c) => {
  const orgId = c.req.param('orgId')
  const { title, client_name } = await c.req.json()
  
  const proposal = await c.env.DB
    .prepare('INSERT INTO proposals (id, org_id, title, client_name) VALUES (?, ?, ?, ?) RETURNING *')
    .bind(crypto.randomUUID(), orgId, title, client_name)
    .first()
  
  return c.json({ data: proposal })
})

// Brand Voice API
app.get('/api/organizations/:orgId/brand-voice', async (c) => {
  const orgId = c.req.param('orgId')
  
  const brandVoice = await c.env.DB
    .prepare('SELECT * FROM brand_voices WHERE org_id = ?')
    .bind(orgId)
    .first()
  
  return c.json({ data: brandVoice })
})

// Training Documents API
app.post('/api/organizations/:orgId/training-documents', async (c) => {
  const orgId = c.req.param('orgId')
  const { file_url, file_name, file_type, content_text, embedding } = await c.req.json()
  
  const doc = await c.env.DB
    .prepare(`INSERT INTO training_documents 
      (id, org_id, file_url, file_name, file_type, content_text, embedding) 
      VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`)
    .bind(crypto.randomUUID(), orgId, file_url, file_name, file_type, content_text, JSON.stringify(embedding))
    .first()
  
  return c.json({ data: doc })
})

export default app
export type Bindings = {
  DB: D1Database
  CACHE: KVNamespace
  AI: Ai
  SUPABASE_URL: string
  SUPABASE_ANON_KEY: string
  OPENAI_API_KEY: string
}
