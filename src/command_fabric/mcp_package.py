"""Generate an MCP stdio package for command fabric consumers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import CommandRecord, build_command_catalog, export_command_catalog


@dataclass(frozen=True)
class McpPackageArtifact:
    """One generated MCP package artifact."""

    name: str
    path: str


def package_json() -> dict[str, object]:
    """Return package metadata for the generated MCP stdio server."""
    return {
        "name": "@mekongcli/command-fabric-mcp",
        "version": "0.0.0",
        "description": "MCP stdio server for Mekong command fabric.",
        "type": "module",
        "private": True,
        "bin": {"mekong-command-fabric-mcp": "./dist/server.js"},
        "main": "./dist/server.js",
        "types": "./dist/server.d.ts",
        "files": ["dist", "data", "README.md"],
        "scripts": {"build": "tsc -p tsconfig.json", "pack:dry-run": "npm pack --dry-run"},
        "devDependencies": {"typescript": "^5.0.0"},
    }


def server_ts() -> str:
    """Return dependency-free JSON-RPC stdio MCP server source."""
    return """import { readFileSync } from 'node:fs'
import { createInterface } from 'node:readline'

type JsonRpcRequest = { id?: string | number; method?: string; params?: Record<string, unknown> }

const catalog = JSON.parse(readFileSync(new URL('../data/canonical.json', import.meta.url), 'utf8'))
const mcp = JSON.parse(readFileSync(new URL('../data/mcp.json', import.meta.url), 'utf8'))

function respond(id: JsonRpcRequest['id'], result: unknown) {
  process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, result }) + '\\n')
}

function error(id: JsonRpcRequest['id'], message: string) {
  process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, error: { code: -32000, message } }) + '\\n')
}

function executionPlan(commandName: string, args: string) {
  const command = catalog.commands.find((item: { name: string }) => item.name === commandName)
  if (!command) throw new Error(`Unknown Mekong command: ${commandName}`)
  const execution = command.execution.includes('$ARGUMENTS')
    ? command.execution.replace('$ARGUMENTS', args)
    : [command.execution, args].filter(Boolean).join(' ')
  return { command: command.name, arguments: args, execution, source: command.source, local_only: true }
}

function handle(request: JsonRpcRequest) {
  if (request.method === 'initialize') return respond(request.id, { protocolVersion: '2024-11-05', serverInfo: { name: 'mekong-command-fabric', version: '0.0.0' }, capabilities: { tools: {} } })
  if (request.method === 'tools/list') return respond(request.id, { tools: mcp.tools })
  if (request.method === 'tools/call') {
    const name = String(request.params?.name ?? '')
    const args = request.params?.arguments as { arguments?: string } | undefined
    const tool = mcp.tools.find((item: { name: string }) => item.name === name)
    if (!tool) return error(request.id, `Unknown tool: ${name}`)
    const commandName = tool.metadata?.command as string
    return respond(request.id, { content: [{ type: 'text', text: JSON.stringify(executionPlan(commandName, args?.arguments ?? ''), null, 2) }] })
  }
  return error(request.id, `Unsupported method: ${String(request.method)}`)
}

createInterface({ input: process.stdin }).on('line', (line) => {
  try { handle(JSON.parse(line) as JsonRpcRequest) } catch (err) { error(undefined, String(err)) }
})
"""


def _write(path: Path, content: str) -> McpPackageArtifact:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return McpPackageArtifact(path.name, path.as_posix())


def materialize_mcp_package(
    output_dir: Path,
    records: list[CommandRecord] | None = None,
) -> dict[str, object]:
    """Write MCP stdio server package scaffold."""
    command_records = records if records is not None else build_command_catalog()
    artifacts = [
        _write(output_dir / "package.json", json.dumps(package_json(), indent=2) + "\n"),
        _write(output_dir / "src" / "server.ts", server_ts()),
        _write(output_dir / "data" / "canonical.json", json.dumps(export_command_catalog(command_records), indent=2) + "\n"),
        _write(output_dir / "data" / "mcp.json", json.dumps(export_adapter_manifest("mcp", command_records), indent=2) + "\n"),
        _write(output_dir / "README.md", "# Mekong Command Fabric MCP\n\nMCP stdio server for Mekong command fabric.\n"),
        _write(output_dir / "tsconfig.json", json.dumps({
            "compilerOptions": {
                "target": "ES2022",
                "module": "NodeNext",
                "moduleResolution": "NodeNext",
                "declaration": True,
                "outDir": "dist",
                "rootDir": "src",
                "strict": True,
                "skipLibCheck": True,
            },
            "include": ["src/**/*.ts"],
        }, indent=2) + "\n"),
    ]
    return {
        "schema": "mekong.command_fabric.mcp_package.v1",
        "output_dir": output_dir.as_posix(),
        "command_count": len(command_records),
        "artifact_count": len(artifacts),
        "artifacts": [artifact.__dict__ for artifact in artifacts],
    }


__all__ = ["McpPackageArtifact", "materialize_mcp_package", "package_json", "server_ts"]
