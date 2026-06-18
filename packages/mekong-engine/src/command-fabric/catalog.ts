export type CommandFabricCommand = {
  name: string
  source: string
  description: string
  argument_hint: string
  allowed_tools: string[]
  execution: string
  contract: string | null
  layer: string | null
  portability_targets: string[]
}

export type CommandFabricCatalog = {
  schema: 'mekong.command_fabric.v1'
  version: string
  source: string
  count: number
  commands: CommandFabricCommand[]
}

export type CommandFabricAdapterManifest = {
  schema: string
  adapter: string
  command_count?: number
  tool_count?: number
  commands?: unknown[]
  tools?: unknown[]
}

export type CommandFabricAdapterBundlePayload = {
  schema: 'mekong.command_fabric.adapter_bundle.v1'
  adapter_count: number
  adapters: Record<string, string | CommandFabricAdapterManifest>
}

export type CommandFabricAdapterBundle = Record<string, string | CommandFabricAdapterManifest> | CommandFabricAdapterBundlePayload

export type CommandExecutionPlan = {
  command: string
  arguments: string
  execution: string
  source: string
  local_only: true
  reason: string
}

export function parseCommandFabricCatalog(raw: string): CommandFabricCatalog {
  const parsed = JSON.parse(raw) as Partial<CommandFabricCatalog>
  if (parsed.schema !== 'mekong.command_fabric.v1') {
    throw new Error(`Unsupported command fabric schema: ${String(parsed.schema)}`)
  }
  if (!Array.isArray(parsed.commands)) {
    throw new Error('Command fabric catalog missing commands array')
  }
  if (parsed.count !== parsed.commands.length) {
    throw new Error('Command fabric catalog count does not match commands length')
  }
  return parsed as CommandFabricCatalog
}

export function parseAdapterManifest(raw: string): CommandFabricAdapterManifest {
  const parsed = JSON.parse(raw) as Partial<CommandFabricAdapterManifest>
  if (!parsed.schema?.startsWith('mekong.command_fabric.adapter.')) {
    throw new Error(`Unsupported command fabric adapter schema: ${String(parsed.schema)}`)
  }
  if (!parsed.adapter) {
    throw new Error('Command fabric adapter manifest missing adapter')
  }
  return parsed as CommandFabricAdapterManifest
}

export function parseAdapterBundle(raw: string): Record<string, CommandFabricAdapterManifest> {
  const parsed = JSON.parse(raw) as CommandFabricAdapterBundle
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error('Command fabric adapter bundle must be an object')
  }

  const entries = 'schema' in parsed
    ? parsed.adapters
    : parsed
  if (!entries || Array.isArray(entries) || typeof entries !== 'object') {
    throw new Error('Command fabric adapter bundle missing adapters object')
  }

  const adapters: Record<string, CommandFabricAdapterManifest> = {}
  for (const [name, value] of Object.entries(entries)) {
    const manifest = typeof value === 'string'
      ? parseAdapterManifest(value)
      : parseAdapterManifest(JSON.stringify(value))
    if (manifest.adapter !== name) {
      throw new Error(`Adapter bundle key '${name}' does not match manifest adapter '${manifest.adapter}'`)
    }
    adapters[name] = manifest
  }
  if ('schema' in parsed && parsed.adapter_count !== Object.keys(adapters).length) {
    throw new Error('Command fabric adapter bundle count does not match adapters length')
  }
  return adapters
}

export function findCommand(
  catalog: CommandFabricCatalog,
  name: string,
): CommandFabricCommand | undefined {
  return catalog.commands.find((command) => command.name === name)
}

export function createExecutionPlan(
  command: CommandFabricCommand,
  args: string,
): CommandExecutionPlan {
  const execution = command.execution.includes('$ARGUMENTS')
    ? command.execution.replace('$ARGUMENTS', args)
    : [command.execution, args].filter(Boolean).join(' ')
  return {
    command: command.name,
    arguments: args,
    execution,
    source: command.source,
    local_only: true,
    reason: 'Cloudflare Workers cannot execute local CLI commands; IDE/CLI clients run this plan locally.',
  }
}
