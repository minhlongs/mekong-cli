/**
 * MCP Host - Manages MCP servers for both personas
 */

import { EventEmitter } from 'events';
import * as fs from 'fs';
import * as path from 'path';
import { ConfigManager } from './config-manager';
import { HookEngine, type HookContext } from './hook-engine';

export interface MCPServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  disabled?: boolean;
  persona?: 'mekong' | 'agentkit' | 'both';
}

export interface MCPServerInstance {
  config: MCPServerConfig;
  process: any; // child_process
  status: 'starting' | 'running' | 'stopped' | 'error';
  startedAt: number;
}

export class MCPHost extends EventEmitter {
  private configManager: ConfigManager;
  private hookEngine: HookEngine;
  private servers: Map<string, MCPServerInstance> = new Map();
  private configRoot: string;

  constructor(configManager: ConfigManager, hookEngine: HookEngine) {
    super();
    this.configManager = configManager;
    this.hookEngine = hookEngine;
    this.configRoot = configManager.configRoot;
  }

  async start(): Promise<void> {
    const settings = this.configManager.getSettings();
    const mcpServers = settings.mcpServers || {};
    
    for (const [name, config] of Object.entries(mcpServers)) {
      const serverConfig: MCPServerConfig = {
        name,
        ...config as any,
        persona: (config as any).persona || 'both',
      };
      
      if (!serverConfig.disabled) {
        await this.startServer(serverConfig);
      }
    }

    // Also check .mcp.json (project-level)
    const mcpJsonPath = path.join(this.configRoot, '.mcp.json');
    if (fs.existsSync(mcpJsonPath)) {
      const mcpJson = JSON.parse(fs.readFileSync(mcpJsonPath, 'utf-8'));
      for (const [name, config] of Object.entries(mcpJson.mcpServers || {})) {
        if (!this.servers.has(name)) {
          const serverConfig: MCPServerConfig = {
            name,
            ...config as any,
            persona: (config as any).persona || 'both',
          };
          if (!serverConfig.disabled) {
            await this.startServer(serverConfig);
          }
        }
      }
    }

    console.log(`[MCPHost] Started ${this.servers.size} MCP servers`);
  }

  private async startServer(config: MCPServerConfig): Promise<void> {
    const { spawn } = await import('child_process');
    
    console.log(`[MCPHost] Starting MCP server: ${config.name}`);
    
    const instance: MCPServerInstance = {
      config,
      process: null,
      status: 'starting',
      startedAt: Date.now(),
    };

    this.servers.set(config.name, instance);

    try {
      const child = spawn(config.command, config.args, {
        env: { ...process.env, ...config.env },
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      instance.process = child;
      instance.status = 'running';

      child.on('error', (err) => {
        console.error(`[MCPHost] Server ${config.name} error:`, err);
        instance.status = 'error';
      });

      child.on('exit', (code) => {
        console.log(`[MCPHost] Server ${config.name} exited with code ${code}`);
        instance.status = 'stopped';
      });

      // Wait a bit for server to start
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log(`[MCPHost] Server ${config.name} running`);
    } catch (error) {
      instance.status = 'error';
      console.error(`[MCPHost] Failed to start ${config.name}:`, error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    console.log(`[MCPHost] Stopping ${this.servers.size} MCP servers`);
    
    for (const [name, instance] of this.servers) {
      if (instance.process) {
        instance.process.kill('SIGTERM');
        instance.status = 'stopped';
      }
    }
    
    this.servers.clear();
  }

  getServer(name: string): MCPServerInstance | undefined {
    return this.servers.get(name);
  }

  getAllServers(): MCPServerInstance[] {
    return Array.from(this.servers.values());
  }

  isRunning(name: string): boolean {
    const server = this.servers.get(name);
    return server?.status === 'running';
  }
}
