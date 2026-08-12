#!/usr/bin/env node
/**
 * Mekong (mk) Binary Entry Point
 * Loads harness core with Mekong persona
 */

import { ConfigManager } from '../src/core/config-manager.js';
import { SessionManager } from '../src/core/session-manager.js';
import { HookEngine } from '../src/core/hook-engine.js';
import { CommandRouter } from '../src/core/command-router.js';
import { LLMRouter } from '../src/providers/llm-router.js';
import { MemoryLayerImpl } from '../src/memory/memory-layer.js';
import { getPersonaConfig } from '../src/personas/personas.js';
import { HarnessConfig, Persona, HookContext } from '../src/core/types.js';
import * as fs from 'fs';
import * as path from 'path';

class MekongBinary {
  private configManager: ConfigManager;
  private sessionManager!: SessionManager;
  private hookEngine!: HookEngine;
  private commandRouter!: CommandRouter;
  private llmRouter!: LLMRouter;
  private memoryLayer!: MemoryLayerImpl;
  private config!: HarnessConfig;
  private persona = getPersonaConfig('mekong');

  constructor(configRoot: string) {
    this.configManager = new ConfigManager(configRoot, 'mekong');
  }

  async initialize(): Promise<void> {
    process.stdout.write('🏯 Initializing Mekong Harness...\n');

    this.config = await this.configManager.load();

    this.sessionManager = new SessionManager(this.configManager);
    this.hookEngine = new HookEngine(this.config);
    this.commandRouter = new CommandRouter(this.config);
    this.llmRouter = new LLMRouter(this.config.llmEndpoint || null);
    this.memoryLayer = new MemoryLayerImpl(this.config.memory, this.configManager.getConfigRoot());

    let session = await this.sessionManager.loadLatestSession('mekong');
    if (!session) {
      session = await this.sessionManager.createSession('mekong', process.cwd());
    }

    process.stdout.write(`✅ Mekong ready — session: ${session.id}\n`);
    process.stdout.write(`   Model: ${this.config.model}\n`);
    process.stdout.write(`   Commands: ${this.persona.availableCommands.length} loaded\n`);
    process.stdout.write(`   Skills: ${this.config.skills.length} loaded\n`);
    process.stdout.write(`   Agents: ${this.config.agents.length} loaded\n`);
  }

  async run(args: string[]): Promise<number> {
    if (args.length === 0) {
      this.showHelp();
      return 0;
    }

    const input = args.join(' ');

    // Built-in commands
    if (input === 'help' || input === '--help' || input === '-h') {
      this.showHelp();
      return 0;
    }
    if (input === 'version' || input === '--version') {
      console.log('mekong 1.0.0 (harness-core)');
      return 0;
    }
    if (input === 'status') {
      this.showStatus();
      return 0;
    }
    if (input === 'session') {
      this.showSessionInfo();
      return 0;
    }

 // Route command

 if (this.config.modelRouting?.rules) {
  const routePreview = this.commandRouter.route(input, 'mekong');
  for (const rule of this.config.modelRouting.rules) {
   if (routePreview.matched && rule.match.includes(routePreview.matched.name)) {
    process.env.MEKONG_MODEL = rule.model;
    process.env.LLM_MODEL = rule.model;
    process.stdout.write(` Model: ${rule.model} (routed)\n`);
    break;
   }
  }
 }

 const route = this.commandRouter.route(input, 'mekong');

 if (!route.matched) {
  console.error(`❌ Unknown command: ${input.split(' ')[0]}`);
  if (route.suggestions?.length) {
   console.log(` Did you mean: ${route.suggestions.join(', ')}?`);
  }
  return 1;
 }

 // Explicit persona switch: /ak:command
 if (input.startsWith('/ak:')) {
  const akCommand = input.slice(4).trim();
  const newArgs = akCommand.split(' ');
  return this.run(newArgs);
 }

 // Handle persona switch via router
 if (route.needsPersonaSwitch && route.targetPersona === 'agentkit') {
  return await this.executeViaAkCommand(route.matched.name, route.args);
 }


    // Execute via hook engine
    try {
      const context = this.sessionManager.getCurrentContext();
      if (context) {
        const hookContext = {
          ...context,
          event: 'PreToolUse' as const,
          toolName: 'command',
          toolInput: { command: input },
          cwd: context.workingDir,
          env: process.env as Record<string, string>,
        };
        await this.hookEngine.fire('PreToolUse', hookContext);
      }

      // For now, delegate to existing mekong CLI via subprocess
      // TODO: Load handler modules directly
      const result = await this.executeViaSubprocess(route.matched, route.args);

      if (context) {
        const hookContext = {
          ...context,
          event: 'PostToolUse' as const,
          toolName: 'command',
          toolInput: { command: input },
          cwd: context.workingDir,
          env: process.env as Record<string, string>,
        };
        await this.hookEngine.fire('PostToolUse', hookContext);
      }

      return result;
    } catch (error: any) {
      console.error(`❌ Error: ${error.message}`);
      return 1;
    }
  }

  private async executeViaSubprocess(command: any, args: Record<string, any>): Promise<number> {
    const { spawn } = await import('child_process');
    const argStr = Object.entries(args).map(([k, v]) => `--${k} ${v}`).join(' ');
    // Propagate model config: MEKONG_MODEL -> ANTHROPIC_MODEL for subprocesses that read Claude env vars
    const modelEnv = process.env.MEKONG_MODEL ? `export ANTHROPIC_MODEL="${process.env.MEKONG_MODEL}"; ` : '';

    return new Promise((resolve) => {
      const proc = spawn('bash', ['-c', `cd "${process.cwd()}" && ${modelEnv}mekong ${command.name} ${argStr}`], {
        stdio: 'inherit',
        shell: true,
      });

      proc.on('close', (code) => resolve(code || 0));
      proc.on('error', () => resolve(1));
    });
  }

  private async executeViaAkCommand(commandName: string, args: Record<string, any>): Promise<number> {
    const { spawn } = await import('child_process');
    const argStr = Object.entries(args).map(([k, v]) => `--${k} ${v}`).join(' ');
    // Propagate model config: MEKONG_MODEL -> ANTHROPIC_MODEL for Claude Code subprocess
    const modelEnv = process.env.MEKONG_MODEL ? `export ANTHROPIC_MODEL="${process.env.MEKONG_MODEL}"; ` : '';

    // Map command name to ak/claude command
    const mapping: Record<string, string> = {
      'status': 'status',
      'plan': '/plan',
      'cook': '/cook',
      'fix': '/fix',
      'review': '/review',
      'scout': '/scout',
      'debug': '/debug',
      'brainstorm': '/brainstorm',
      'code': '/code',
      'test': '/test',
      'ship': '/ship',
      'simplify': '/simplify',
      'preview': '/preview',
      'research': '/research',
    };

    const claudeCmd = mapping[commandName] || commandName;

    return new Promise((resolve) => {
      const proc = spawn('bash', ['-c', `cd "${process.cwd()}" && ${modelEnv}npx tsx "${process.env.MEKONG_ROOT || process.env.HOME}/mekong-cli/harness/bin/ak.ts" ${claudeCmd} ${argStr}`], {
        stdio: 'inherit',
        shell: true,
      });

      proc.on('close', (code) => resolve(code || 0));
      proc.on('error', () => resolve(1));
    });
  }

  private showHelp(): void {
    console.log(`
🏯 Mekong CLI (mk) — Agency OS

USAGE
  mk <command> [options]

CORE
  cook <feature>       Build feature (plan → code → test → ship)
  fix <issue>          Fix bug / error / test failure
  plan <task>          Create implementation plan
  review               Code review before merge
  deploy               Deploy to production
  audit                Security / compliance audit

STRATEGY
  mk strat:analyze <idea>  Binh Phap strategic analysis
  mk strat:plan <task>     Tactical plan
  mk strat:win3            WIN-WIN-WIN balance check

REVENUE
  mk sales <cmd>       Sales pipeline
  mk finance <cmd>     Financial ops
  mk marketing <cmd>   Marketing campaigns
  mk outreach <cmd>    Outreach automation

PARTICLES
  mk particle init <name>   Create new particle
  mk particle graph <cmd>   Behavior graph
  mk particle cell <cmd>    AI cell runtime
  mk particle zenpay <cmd>  Constitutional treasury

SYSTEM
  mk status         Show harness status
  mk session        Session info
  mk help           This help

PERSONA SWITCH
  /ak:<cmd>         Run Agent Kit command
  /mk:<cmd>         Explicit Mekong command
`);
  }

  private showStatus(): void {
    const session = this.sessionManager.getCurrentSession();
    console.log(`
🏯 Mekong Harness Status
════════════════════════
Session: ${session?.id || 'none'}
Persona: ${this.persona.name}
Model:   ${this.config.model}
CWD:     ${process.cwd()}
Commands: ${this.persona.availableCommands.length}
Skills:   ${this.config.skills.length}
Agents:   ${this.config.agents.length}
`);
  }

  private showSessionInfo(): void {
    const session = this.sessionManager.getCurrentSession();
    if (!session) {
      console.log('No active session');
      return;
    }
    console.log(`
📋 Session Info
════════════════
ID:     ${session.id}
Persona: ${session.persona}
CWD:    ${session.workingDir}
History: ${session.history.length} entries
Context: ~${session.contextTokens || 0} tokens
Agents:  ${session.agentInvocations?.length || 0} invocations
`);
  }
}

// Main
async function main(): Promise<void> {
  const configRoot = process.env.MEKONG_ROOT || path.join(process.env.HOME || '', 'mekong-cli');
  const binary = new MekongBinary(configRoot);

  try {
    await binary.initialize();
    const exitCode = await binary.run(process.argv.slice(2));
    process.exit(exitCode);
  } catch (error: any) {
    console.error(`❌ Fatal: ${error.message}`);
    process.exit(1);
  }
}

main();