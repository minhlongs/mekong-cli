import { describe, expect, it } from 'vitest'
import server from '../src/index'
import {
  createExecutionPlan,
  parseAdapterBundle,
  parseCommandFabricCatalog,
} from '../src/command-fabric/catalog'

const canonical = JSON.stringify({
  schema: 'mekong.command_fabric.v1',
  version: 'test',
  source: 'fixture',
  count: 2,
  commands: [
    {
      name: 'cook',
      source: '.claude/commands/cook.md',
      description: 'Cook workflow',
      argument_hint: '[goal]',
      allowed_tools: ['bash'],
      execution: 'mekong cook $ARGUMENTS',
      contract: null,
      layer: 'engineering',
      portability_targets: ['mcp', 'vscode', 'shell'],
    },
    {
      name: 'harness-eval',
      source: 'native',
      description: 'Run harness evals',
      argument_hint: '--json',
      allowed_tools: [],
      execution: 'python3 -m src.main harness-eval $ARGUMENTS',
      contract: null,
      layer: 'ops',
      portability_targets: ['mcp'],
    },
  ],
})

const mcp = JSON.stringify({
  schema: 'mekong.command_fabric.adapter.mcp.v1',
  adapter: 'mcp',
  tool_count: 1,
  tools: [{ name: 'mekong_cook', metadata: { command: 'cook' } }],
})

const vscode = {
  schema: 'mekong.command_fabric.adapter.vscode.v1',
  adapter: 'vscode',
  command_count: 2,
  commands: [{ command: 'mekong.cook', title: 'Mekong: cook' }],
}

const env = {
  COMMAND_FABRIC_CANONICAL: canonical,
  COMMAND_FABRIC_MCP: mcp,
  COMMAND_FABRIC_ADAPTERS: JSON.stringify({
    schema: 'mekong.command_fabric.adapter_bundle.v1',
    adapter_count: 2,
    adapters: {
      mcp: JSON.parse(mcp),
      vscode,
    },
  }),
}

describe('command fabric catalog loader', () => {
  it('validates canonical artifact shape', () => {
    const catalog = parseCommandFabricCatalog(canonical)
    expect(catalog.count).toBe(2)
    expect(catalog.commands[0]?.name).toBe('cook')
  })

  it('builds local execution plan for IDE/CLI clients', () => {
    const catalog = parseCommandFabricCatalog(canonical)
    const plan = createExecutionPlan(catalog.commands[0]!, 'build api')
    expect(plan.execution).toBe('mekong cook build api')
    expect(plan.local_only).toBe(true)
  })

  it('validates multi-adapter manifest bundles', () => {
    const bundle = parseAdapterBundle(env.COMMAND_FABRIC_ADAPTERS)
    expect(Object.keys(bundle).sort()).toEqual(['mcp', 'vscode'])
    expect(bundle.vscode?.command_count).toBe(2)
  })
})

describe('command fabric routes', () => {
  it('GET /v1/command-fabric returns canonical catalog from binding', async () => {
    const res = await server.fetch(new Request('http://localhost/v1/command-fabric'), env)
    expect(res.status).toBe(200)
    const body = (await res.json()) as { schema: string; count: number }
    expect(body.schema).toBe('mekong.command_fabric.v1')
    expect(body.count).toBe(2)
  })

  it('GET /v1/command-fabric/commands/:name returns one command', async () => {
    const res = await server.fetch(new Request('http://localhost/v1/command-fabric/commands/cook'), env)
    expect(res.status).toBe(200)
    const body = (await res.json()) as { name: string; execution: string }
    expect(body.name).toBe('cook')
    expect(body.execution).toContain('$ARGUMENTS')
  })

  it('GET /v1/command-fabric/adapters/mcp returns MCP adapter manifest', async () => {
    const res = await server.fetch(new Request('http://localhost/v1/command-fabric/adapters/mcp'), env)
    expect(res.status).toBe(200)
    const body = (await res.json()) as { schema: string; tool_count: number }
    expect(body.schema).toBe('mekong.command_fabric.adapter.mcp.v1')
    expect(body.tool_count).toBe(1)
  })

  it('GET /v1/command-fabric/adapters returns all configured adapter names', async () => {
    const res = await server.fetch(new Request('http://localhost/v1/command-fabric/adapters'), env)
    expect(res.status).toBe(200)
    const body = (await res.json()) as { schema: string; count: number; adapters: string[] }
    expect(body.schema).toBe('mekong.command_fabric.adapters.index.v1')
    expect(body.count).toBe(2)
    expect(body.adapters).toEqual(['mcp', 'vscode'])
  })

  it('GET /v1/command-fabric/adapters/:adapter returns non-MCP manifests from adapter bundle', async () => {
    const res = await server.fetch(new Request('http://localhost/v1/command-fabric/adapters/vscode'), env)
    expect(res.status).toBe(200)
    const body = (await res.json()) as { schema: string; adapter: string; command_count: number }
    expect(body.schema).toBe('mekong.command_fabric.adapter.vscode.v1')
    expect(body.adapter).toBe('vscode')
    expect(body.command_count).toBe(2)
  })

  it('POST /v1/command-fabric/invoke returns local execution plan', async () => {
    const res = await server.fetch(
      new Request('http://localhost/v1/command-fabric/invoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'harness-eval', arguments: '--json' }),
      }),
      env,
    )
    expect(res.status).toBe(200)
    const body = (await res.json()) as { execution: string; local_only: boolean }
    expect(body.execution).toBe('python3 -m src.main harness-eval --json')
    expect(body.local_only).toBe(true)
  })

  it('returns 503 when canonical binding is absent', async () => {
    const res = await server.fetch(new Request('http://localhost/v1/command-fabric'), {})
    expect(res.status).toBe(503)
  })
})
