/**
 * Agent Runtime - Spawns and manages subagents for both personas
 */

import { EventEmitter } from 'events';
import * as fs from 'fs';
import * as path from 'path';
import { SessionManager, type AgentInvocation } from './session-manager';
import { HookEngine, type HookContext } from './hook-engine';

export interface AgentConfig {
  name: string;
  description: string;
  prompt: string;
  tools?: string[];
  model?: string;
}

export interface AgentResult {
  success: boolean;
  output?: string;
  error?: string;
  duration: number;
}

export class AgentRuntime extends EventEmitter {
  private sessionManager: SessionManager;
  private hookEngine: HookEngine;
  private agentsDir: string;
  private agents: Map<string, AgentConfig> = new Map();

  constructor(sessionManager: SessionManager, hookEngine: HookEngine) {
    super();
    this.sessionManager = sessionManager;
    this.hookEngine = hookEngine;
    this.agentsDir = path.join(process.cwd(), '.claude', 'agents');
  }

  async loadAgents(): Promise<void> {
    if (fs.existsSync(this.agentsDir)) {
      const files = fs.readdirSync(this.agentsDir).filter(f => f.endsWith('.md'));
      for (const file of files) {
        const content = fs.readFileSync(path.join(this.agentsDir, file), 'utf-8');
        const agent = this.parseAgentFile(content, file);
        if (agent) {
          this.agents.set(agent.name, agent);
        }
      }
    }
    console.log(`[AgentRuntime] Loaded ${this.agents.size} agents`);
  }

  private parseAgentFile(content: string, filename: string): AgentConfig | null {
    const match = content.match(/^---\n([\s\S]*?)\n---/);
    if (!match) return null;

    const frontmatter = match[1] || '';
    const prompt = content.substring(match[0].length).trim();

    const nameMatch = frontmatter.match(/name:\s*(.+)/);
    const descMatch = frontmatter.match(/description:\s*(.+)/);
    const toolsMatch = frontmatter.match(/tools:\s*\[([\s\S]*?)\]/);
    const modelMatch = frontmatter.match(/model:\s*(.+)/);

    return {
      name: nameMatch ? nameMatch[1].trim() : filename.replace('.md', ''),
      description: descMatch ? descMatch[1].trim() : '',
      prompt,
      tools: toolsMatch ? toolsMatch[1].split(',').map(t => t.trim().replace(/['"]/g, '')) : [],
      model: modelMatch ? modelMatch[1].trim() : undefined,
    };
  }

  async spawnAgent(
    agentName: string, 
    prompt: string, 
    options: { sessionId?: string; persona?: 'mekong' | 'agentkit' } = {}
  ): Promise<AgentResult> {
    const agent = this.agents.get(agentName);
    if (!agent) {
      throw new Error(`Agent not found: ${agentName}`);
    }

    const invocation: AgentInvocation = {
      id: `agent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: agentName,
      prompt,
      status: 'running',
      startedAt: Date.now(),
    };

    this.sessionManager.addAgentInvocation(invocation);

    await this.hookEngine.fire('SubagentStart', {
      persona: options.persona || 'agentkit',
      sessionId: options.sessionId || this.sessionManager.currentSession?.id,
      workingDir: process.cwd(),
      command: agentName,
      args: [prompt],
    } as HookContext);

    const startTime = Date.now();

    try {
      const result = await this.executeAgent(agent, prompt);
      const duration = Date.now() - startTime;
      
      this.sessionManager.updateAgentInvocation(invocation.id, {
        status: 'completed',
        result,
        completedAt: Date.now(),
      });

      await this.hookEngine.fire('SubagentStop', {
        persona: options.persona || 'agentkit',
        sessionId: options.sessionId || this.sessionManager.currentSession?.id,
        workingDir: process.cwd(),
        command: agentName,
        args: [prompt],
      } as HookContext);

      return { success: true, output: result, duration };
    } catch (error) {
      const duration = Date.now() - startTime;
      
      this.sessionManager.updateAgentInvocation(invocation.id, {
        status: 'failed',
        result: error instanceof Error ? error.message : String(error),
        completedAt: Date.now(),
      });

      await this.hookEngine.fire('SubagentStop', {
        persona: options.persona || 'agentkit',
        sessionId: options.sessionId || this.sessionManager.currentSession?.id,
        workingDir: process.cwd(),
        command: agentName,
        args: [prompt],
      } as HookContext);

      return { success: false, error: error instanceof Error ? error.message : String(error), duration };
    }
  }

  private async executeAgent(agent: AgentConfig, prompt: string): Promise<string> {
    const { spawn } = await import('child_process');
    // Route the agent to its declared model (frontmatter `model:`) when set.
    // The model id flows to OmniRoute via ANTHROPIC_MODEL; unset agents keep
    // the harness default so the session model (claude-fable-5) applies.
    const agentModel = agent.model && agent.model !== 'default'
      ? agent.model
      : (process.env.ANTHROPIC_MODEL || 'claude-fable-5');
    const modelEnv = {
      ...process.env,
      ANTHROPIC_MODEL: agentModel,
      LLM_MODEL: agentModel,
      MEKONG_AGENT_MODEL: agentModel,
    };
    return new Promise<string>((resolve, reject) => {
      const proc = spawn('claude', ['-p', `You are ${agent.name}. ${agent.prompt}\n\nTask: ${prompt}`, '--dangerously-skip-permissions'], {
        cwd: process.cwd(),
        env: modelEnv,
        shell: false,
      });
      let stdout = '';
      let stderr = '';
      proc.stdout.on('data', (d) => { stdout += d.toString(); });
      proc.stderr.on('data', (d) => { stderr += d.toString(); });
      proc.on('close', (code) => {
        if (code === 0) resolve(stdout.trim());
        else reject(new Error(`Agent ${agent.name} exited ${code}: ${stderr.trim().slice(0, 300)}`));
      });
      proc.on('error', (err) => reject(err));
    });
  }

  getAvailableAgents(): AgentConfig[] {
    return Array.from(this.agents.values());
  }

  getAgent(name: string): AgentConfig | undefined {
    return this.agents.get(name);
  }
}
