import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { handleAsync, handleDb, requireResource, createError, ERROR_CODES } from '../types/error'

type Variables = { tenant: Tenant }

// Zod schema for agent execution
const runAgentSchema = z.object({
  command: z.string().min(1, 'command is required'),
  params: z.record(z.unknown()).optional(),
})

type RunAgentBody = z.infer<typeof runAgentSchema>

const AVAILABLE_AGENTS = [
  { name: 'git', description: 'Git operations: status, diff, log, commit, branch' },
  { name: 'file', description: 'File operations: find, read, tree, stats, grep' },
  { name: 'shell', description: 'Shell command execution' },
  { name: 'lead-hunter', description: 'Company and CEO lead discovery' },
  { name: 'content-writer', description: 'Content generation' },
  { name: 'recipe-crawler', description: 'Recipe file discovery' },
]

const agentRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

agentRoutes.get('/', (c) => c.json({ agents: AVAILABLE_AGENTS }))

agentRoutes.post('/:name/run', authMiddleware, payloadSizeLimit(), handleAsync(async (c) => {
  const name = c.req.param('name')
  const agent = AVAILABLE_AGENTS.find((a) => a.name === name)
  if (!agent) return c.json(createError('NOT_FOUND', `Agent '${name}' not found`), 404)

  let body: RunAgentBody
  try {
    body = runAgentSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  // Agents are executed via the PEV orchestrator in the core engine
  return c.json({
    agent: name,
    command: body.command,
    status: 'accepted',
    message: 'Agent execution queued — use /v1/tasks to track progress',
  }, 202)
}))

export { agentRoutes }
