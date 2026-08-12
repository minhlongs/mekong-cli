/**
 * Main Harness Class - Entry point for both personas
 */

import { EventEmitter } from 'events';
import * as path from 'path';
import { HookEngine, type HookContext } from './hook-engine';
import { SessionManager, type Persona } from './session-manager';
import { AgentRuntime } from './agent-runtime';
import { MCPHost } from './mcp-host';
import { SkillLoader } from './skill-loader';
import { CommandRouter } from './command-router';
import { MemoryLayer } from './memory-layer';
import { ConfigManager, type HarnessConfig } from './config-manager';
import { LLMRouter } from '../providers/llm-router';
import { MekongPersona } from '../personas/mekong-persona';
import { AgentKitPersona } from '../personas/agentkit-persona';

export interface HarnessOptions {
  configRoot: string;
  persona: Persona;
  model?: string;
  debug?: boolean;
}

export class Harness extends EventEmitter {
  public readonly configRoot: string;
  public readonly persona: Persona;
  public readonly model: string;
  public readonly debug: boolean;

  public readonly configManager: ConfigManager;
  public readonly hookEngine: HookEngine;
  public readonly sessionManager: SessionManager;
  public readonly agentRuntime: AgentRuntime;
  public readonly mcpHost: MCPHost;
  public readonly skillLoader: SkillLoader;
  public readonly commandRouter: CommandRouter;
  public readonly memoryLayer: MemoryLayer;
  public readonly llmRouter: LLMRouter;

  private initialized = false;

  constructor(options: HarnessOptions) {
    super();
    this.configRoot = path.resolve(options.configRoot);
    this.persona = options.persona;
    this.model = options.model || 'claude-opus-4-8';
    this.debug = options.debug || false;

    this.configManager = new ConfigManager(this.configRoot);
    this.hookEngine = new HookEngine(this.configManager);
    this.sessionManager = new SessionManager(this.configRoot, this.configManager, this.hookEngine);
    this.agentRuntime = new AgentRuntime(this.sessionManager, this.hookEngine);
    this.mcpHost = new MCPHost(this.configManager, this.hookEngine);
    this.skillLoader = new SkillLoader(this.configRoot, this.configManager);
    this.commandRouter = new CommandRouter(this.configRoot, this.skillLoader, this.configManager);
    this.memoryLayer = new MemoryLayer(this.configRoot, this.configManager);
    this.llmRouter = new LLMRouter(this.configManager, this.model);

    this.loadPersonaConfig();
  }

  private loadPersonaConfig(): void {
    if (this.persona === 'mekong') {
      const persona = new MekongPersona();
      persona.applyToHarness(this);
    } else {
      const persona = new AgentKitPersona();
      persona.applyToHarness(this);
    }
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    if (this.debug) console.log(`[Harness] Initializing ${this.persona} persona...`);

    await this.configManager.load();
    await this.mcpHost.start();
    await this.skillLoader.loadAll();
    await this.commandRouter.loadCommands();
    await this.sessionManager.initialize(this.persona);
    await this.hookEngine.loadHooks();

    this.initialized = true;
    this.emit('ready', { persona: this.persona });

    if (this.debug) console.log(`[Harness] ${this.persona} persona ready`);
  }

  async run(args: string[]): Promise<void> {
    await this.initialize();

    if (args.length === 0) {
      this.showHelp();
      return;
    }

    const command = args[0];
    const commandArgs = args.slice(1);

    const commandDef = this.commandRouter.route(command, this.persona);
    if (!commandDef) {
      console.error(`Unknown command: ${command}`);
      this.showHelp();
      process.exit(1);
    }

    const context: HookContext = {
      persona: this.persona,
      sessionId: this.sessionManager.currentSession?.id,
      workingDir: process.cwd(),
      command,
      args: commandArgs,
    };

    await this.hookEngine.fire('PreToolUse', context);

    try {
      await commandDef.handler(commandArgs, context);
      await this.hookEngine.fire('PostToolUse', { ...context, success: true });
    } catch (error) {
      await this.hookEngine.fire('PostToolUse', { ...context, success: false, error: error as Error });
      throw error;
    }
  }

  private showHelp(): void {
    console.log(`
${this.persona === 'mekong' ? '🌊 MEKONG-CLI' : '🏯 AGENT KIT'} - ${this.persona === 'mekong' ? 'The One-Person Unicorn OS' : 'Agent Kit on Mekong Harness'}

Usage: ${this.persona} <command> [args]

Available commands:
${this.commandRouter.getAvailableCommands(this.persona).map(c => `  ${c.name.padEnd(20)} ${c.description}`).join('\n')}

Global options:
  --model <model>     Override default model (current: ${this.model})
  --debug             Enable debug logging
  --help              Show this help
`);
  }

  async shutdown(): Promise<void> {
    if (this.debug) console.log(`[Harness] Shutting down ${this.persona}...`);
    
    await this.mcpHost.stop();
    await this.sessionManager.save();
    
    this.initialized = false;
    this.emit('shutdown', { persona: this.persona });
  }
}
