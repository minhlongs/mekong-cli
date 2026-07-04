import { Hono } from 'hono'
import type { Bindings } from '../index'
import {
  createExecutionPlan,
  findCommand,
  parseAdapterBundle,
  parseAdapterManifest,
  parseCommandFabricCatalog,
} from '../command-fabric/catalog'

export const commandFabricRoutes = new Hono<{ Bindings: Bindings }>()

function loadCatalog(raw: string | undefined) {
  if (!raw) return { error: 'COMMAND_FABRIC_CANONICAL not configured' }
  try {
    return { catalog: parseCommandFabricCatalog(raw) }
  } catch (error) {
    return { error: String(error) }
  }
}

function loadAdapters(env: Bindings) {
  try {
    const adapters = env.COMMAND_FABRIC_ADAPTERS
      ? parseAdapterBundle(env.COMMAND_FABRIC_ADAPTERS)
      : {}
    if (env.COMMAND_FABRIC_MCP && !adapters.mcp) {
      adapters.mcp = parseAdapterManifest(env.COMMAND_FABRIC_MCP)
    }
    return { adapters }
  } catch (error) {
    return { error: String(error) }
  }
}

commandFabricRoutes.get('/', (c) => {
  const loaded = loadCatalog(c.env.COMMAND_FABRIC_CANONICAL)
  if (loaded.error) return c.json({ error: loaded.error }, 503)
  return c.json(loaded.catalog)
})

commandFabricRoutes.get('/commands/:name', (c) => {
  const loaded = loadCatalog(c.env.COMMAND_FABRIC_CANONICAL)
  if (loaded.error || !loaded.catalog) return c.json({ error: loaded.error }, 503)
  const command = findCommand(loaded.catalog, c.req.param('name'))
  if (!command) return c.json({ error: 'Command not found' }, 404)
  return c.json(command)
})

commandFabricRoutes.get('/adapters', (c) => {
  const loaded = loadAdapters(c.env)
  if (loaded.error || !loaded.adapters) return c.json({ error: loaded.error }, 503)
  return c.json({
    schema: 'mekong.command_fabric.adapters.index.v1',
    count: Object.keys(loaded.adapters).length,
    adapters: Object.keys(loaded.adapters).sort(),
  })
})

commandFabricRoutes.get('/adapters/:adapter', (c) => {
  const loaded = loadAdapters(c.env)
  if (loaded.error || !loaded.adapters) return c.json({ error: loaded.error }, 503)
  const adapter = c.req.param('adapter')
  const manifest = loaded.adapters[adapter]
  if (!manifest) return c.json({ error: 'Adapter manifest not found' }, 404)
  return c.json(manifest)
})

commandFabricRoutes.post('/invoke', async (c) => {
  const loaded = loadCatalog(c.env.COMMAND_FABRIC_CANONICAL)
  if (loaded.error || !loaded.catalog) return c.json({ error: loaded.error }, 503)

  let body: { command?: string; arguments?: string }
  try {
    body = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }
  if (!body.command) return c.json({ error: 'command is required' }, 400)

  const command = findCommand(loaded.catalog, body.command)
  if (!command) return c.json({ error: 'Command not found' }, 404)
  return c.json(createExecutionPlan(command, body.arguments ?? ''))
})
