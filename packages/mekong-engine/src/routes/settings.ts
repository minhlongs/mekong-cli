import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { saveLLMSettings, getLLMSettings, deleteLLMSettings, maskApiKey, PROVIDER_PRESETS } from '../raas/tenant-settings'
import { z } from 'zod'
import { createError, handleAsync, handleDb } from '../types/error'

type Variables = { tenant: Tenant }

const settingsRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

// Zod schema for LLM settings
const llmSettingsSchema = z.object({
  provider: z.enum(['openai', 'google', 'anthropic', 'custom']),
  api_key: z.string().min(1, 'API key is required'),
  base_url: z.string().url().optional().or(z.literal('')),
  model: z.string().optional(),
})

settingsRoutes.use('*', async (c, next) => {
  if (!c.env.DB) return c.json(createError('SERVICE_UNAVAILABLE', 'D1 database not configured'), 503)
  if (!c.env.SERVICE_TOKEN) return c.json(createError('SERVICE_UNAVAILABLE', 'SERVICE_TOKEN not configured'), 503)
  await next()
})
settingsRoutes.use('*', authMiddleware)

// POST /v1/settings/llm — save LLM config
settingsRoutes.post('/llm', payloadSizeLimit(), handleAsync(async (c) => {
  const body = await c.req.json()
  const parsed = llmSettingsSchema.safeParse(body)
  if (!parsed.success) {
    return c.json(createError('VALIDATION_ERROR', parsed.error.errors[0]?.message || 'Invalid request'), 400)
  }
  if (parsed.data.provider === 'custom' && !parsed.data.base_url?.trim()) {
    return c.json(createError('VALIDATION_ERROR', 'base_url required for custom provider'), 400)
  }

  const tenant = c.get('tenant')
  await handleDb(
    () => saveLLMSettings(c.env.DB!, tenant.id, {
      provider: parsed.data.provider,
      apiKey: parsed.data.api_key,
      baseUrl: parsed.data.base_url,
      model: parsed.data.model,
    }, c.env.SERVICE_TOKEN!),
    'DATABASE_ERROR',
    'Failed to save LLM settings'
  )

  return c.json({ ok: true, provider: parsed.data.provider, message: 'LLM settings saved' })
}))

// GET /v1/settings/llm — get current config (masked key)
settingsRoutes.get('/llm', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const settings = await handleDb(
    () => getLLMSettings(c.env.DB!, tenant.id, c.env.SERVICE_TOKEN!),
    'DATABASE_ERROR',
    'Failed to fetch LLM settings'
  )

  if (!settings) {
    return c.json({ provider: 'workers-ai', api_key: null, base_url: null, model: null, message: 'Using default Workers AI' })
  }

  return c.json({
    provider: settings.provider,
    api_key: settings.apiKey ? maskApiKey(settings.apiKey) : null,
    base_url: settings.baseUrl || null,
    model: settings.model || null,
    available_providers: Object.keys(PROVIDER_PRESETS),
  })
}))

// DELETE /v1/settings/llm — remove custom config, fallback to Workers AI
settingsRoutes.delete('/llm', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const deleted = await handleDb(
    () => deleteLLMSettings(c.env.DB!, tenant.id),
    'DATABASE_ERROR',
    'Failed to delete LLM settings'
  )
  return c.json({ ok: true, deleted, message: deleted ? 'LLM settings removed, falling back to Workers AI' : 'No custom settings found' })
}))

export { settingsRoutes }
