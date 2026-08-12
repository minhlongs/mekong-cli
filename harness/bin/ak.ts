#!/usr/bin/env node
/**
 * Agent Kit (ak) Binary Entry Point
 * Loads harness core with Agent Kit persona
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

class AgentKitBinary {
  private configManager: ConfigManager;
  private sessionManager!: SessionManager;
  private hookEngine!: HookEngine;
  private commandRouter!: CommandRouter;
  private llmRouter!: LLMRouter;
  private memoryLayer!: MemoryLayerImpl;
  private config!: HarnessConfig;
  private persona = getPersonaConfig('agentkit');

  constructor(configRoot: string) {
    this.configManager = new ConfigManager(configRoot, 'agentkit');
  }

  async initialize(): Promise<void> {
    process.stdout.write('🤖 Initializing Agent Kit Harness...\n');

    this.config = await this.configManager.load();

    this.sessionManager = new SessionManager(this.configManager);
    this.hookEngine = new HookEngine(this.config);
    this.commandRouter = new CommandRouter(this.config);
    this.llmRouter = new LLMRouter(this.config.llmEndpoint || null);
    this.memoryLayer = new MemoryLayerImpl(this.config.memory, this.configManager.getConfigRoot());

    let session = await this.sessionManager.loadLatestSession('agentkit');
    if (!session) {
      session = await this.sessionManager.createSession('agentkit', process.cwd());
    }

    process.stdout.write(`✅ Agent Kit ready — session: ${session.id}\n`);
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
      console.log('ak 1.0.0 (harness-core)');
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

  // Agent dispatch: @suntzu, @kongming, etc.
  const agentMatch = input.match(/^@(\w+)\s+(.+)/);
  if (agentMatch) {
    return this.executeAgent(agentMatch[1], agentMatch[2]);
  }

    // Handle explicit persona switch: /mk:command
    if (input.startsWith('/mk:')) {
      const mkCommand = input.slice(4).trim(); // Remove '/mk:'
      console.log(`🔄 Switching to Mekong persona for: ${mkCommand}`);
      return this.executeViaMkCommand(mkCommand);
    }
    if (input.startsWith('/ak:')) {
      // Already in ak persona, just run the command
      const akCommand = input.slice(4).trim();
      const newArgs = akCommand.split(' ');
      return this.run(newArgs);
    }

    // Route command
 // Apply model routing (settings.json rules)
 if (!process.env.MEKONG_MODEL && this.config.modelRouting?.rules) {
 const routePreview = this.commandRouter.route(input, 'agentkit');
 for (const rule of this.config.modelRouting.rules) {
 if (routePreview.matched && rule.match.includes(routePreview.matched.name)) {
 process.env.MEKONG_MODEL = rule.model;
 process.env.LLM_MODEL = rule.model;
 process.stdout.write(` Model: ${rule.model} (routed)\n`);
 break;
 }
 }
 }

 const route = this.commandRouter.route(input, 'agentkit');

 if (!route.matched) {
  console.error(`❌ Unknown command: ${input.split(' ')[0]}`);
  if (route.suggestions?.length) {
   console.log(` Did you mean: ${route.suggestions.join(', ')}?`);
  }
  return 1;
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

      // For now, delegate to existing claude CLI via subprocess
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

    // Map agentkit commands to claude-code commands
    const claudeCmd = this.mapToClaudeCommand(command.name);

    return new Promise((resolve) => {
      const proc = spawn('bash', ['-c', `cd "${process.cwd()}" && claude -p "${claudeCmd} ${argStr}" --dangerously-skip-permissions`], {
        stdio: 'inherit',
        shell: true,
      });

      proc.on('close', (code) => resolve(code || 0));
      proc.on('error', () => resolve(1));
    });
  }

  private async executeViaMkCommand(command: string): Promise<number> {
    const { spawn } = await import('child_process');

    const commandName = command.split(' ')[0];

    return new Promise((resolve) => {
      const proc = spawn('bash', ['-c', `cd "${process.cwd()}" && npx tsx "${process.env.MEKONG_ROOT || process.env.HOME}/mekong-cli/harness/bin/mk.ts" ${command}`], {
        stdio: 'inherit',
        shell: true,
      });

      proc.on('close', (code) => resolve(code || 0));
      proc.on('error', () => resolve(1));
    });
  }

  private mapToClaudeCommand(cmd: string): string {
    // Map agentkit commands to claude-code builtins
    const mapping: Record<string, string> = {
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
      'ask': '/ask',
    };
    return mapping[cmd] || cmd;
  }


private async executeAgent(agentName: string, task: string): Promise<number> {
  const { spawn } = await import('child_process');
  const agentDisplay = agentName.toUpperCase();
  process.stdout.write(` Dispatching @${agentDisplay}: ${task}\n`);
  process.env.LLM_MODEL = "strategist";
  process.env.ANTHROPIC_MODEL = "strategist";
  return new Promise((resolve) => {
    const proc = spawn('bash', ['-c', `cd "${process.cwd()}" && claude -p "as @${agentName}, ${task}" --dangerously-skip-permissions`], {
      stdio: 'inherit',
      shell: true,
    });
    proc.on('close', (code) => resolve(code || 0));
    proc.on('error', () => resolve(1));
  });
}
  private showHelp(): void {
    console.log(`
🤖 Agent Kit (ak) — Claude Code Enhanced

USAGE
  ak <command> [options]

CORE WORKFLOW
  plan <task>       Create implementation plan
  cook <feature>    Build feature (plan → code → test → ship)
  fix <issue>       Fix bug / error / test failure
  review            Code review before merge
  scout <query>     Search codebase
  brainstorm <topic> Ideate & explore options
  code <spec>       Implement from spec
  test              Run test suite
  ship              Deploy to production

QUALITY
  simplify          Refactor & simplify code
  typecheck         TypeScript check
  lint              ESLint

VISUALIZATION
  preview           Visual explanations
    preview:explain <topic>  Code walkthrough
    preview:diagram <topic>  Architecture diagram
    preview:slides <topic>   Step-by-step slides

DESIGN & UI
  design            UI/UX design
  stitch            AI design generation (Google Stitch)
  excalidraw        Diagrams
  threejs           3D/WebGL
  shader            GLSL shaders

RESEARCH & AI
  ask <question>    Technical Q&A
  research <topic>  Deep research
  deep-research     Multi-source fact-checked report
  context-engineering  Agent architecture
  google-adk-python Build AI agents

DOCUMENTATION
  docs:update       Update project docs
  markdown-novel-viewer  Read long docs in browser

FRAMEWORKS
  web-frameworks    Next.js, React, TanStack
  mobile-development React Native, Flutter, SwiftUI
  shopify           Shopify apps

BACKEND
  backend-development  NestJS, FastAPI, Django
  better-auth       Authentication
  payment-integration Stripe, Polar, SePay
  databases         Schema, queries, optimization
  devops            Docker, K8s, CI/CD

SECURITY
  security          STRIDE/OWASP audit
  cti-expert        Threat intelligence

TESTING & BROWSER
  web-testing       Playwright, Vitest, k6
  agent-browser     Browser automation
  chrome-profile    Drive real Chrome profile

MESSAGES
  media-processing  FFmpeg, ImageMagick
  ai-artist         Imagen, Nano Banana

DOCUMENTS
  docx / pdf / pptx / xlsx  Office files

SYSTEM
  ak status         Show harness status
  ak session        Session info
  ak help           This help

AGENTS
@suntzu <task>  Sun Tzu strategist - plan, delegate, synthesize
@kongming <task> Kongming advisor - hard design, debugging, trade-offs

PERSONA SWITCH
  /mk:<cmd>         Run Mekong command
  /ak:<cmd>         Explicit Agent Kit command
`);
  }

  private showStatus(): void {
    const session = this.sessionManager.getCurrentSession();
    console.log(`
🤖 Agent Kit Harness Status
═══════════════════════════
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
ID:      ${session.id}
Persona: ${session.persona}
CWD:     ${session.workingDir}
History: ${session.history.length} entries
Context: ~${session.contextTokens || 0} tokens
`);
  }
}

// Main
async function main(): Promise<void> {
  const configRoot = process.env.MEKONG_ROOT || path.join(process.env.HOME || '', 'mekong-cli');
  const binary = new AgentKitBinary(configRoot);

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