/**
 * Config Manager - Unified configuration for both personas
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as yaml from 'yaml';
import { HarnessConfig, Persona, Hook, Skill, AgentDef, MCPServerConfig, LLMEndpoint, SessionConfig, MemoryConfig } from './types';

export class ConfigManager {
  private configRoot: string;
  private config: HarnessConfig | null = null;
  private persona: Persona;

  constructor(configRoot: string, persona: Persona = 'mekong') {
    this.configRoot = configRoot;
    this.persona = persona;
  }

  getConfigRoot(): string {
    return this.configRoot;
  }

  getPersona(): Persona {
    return this.persona;
  }

  setPersona(persona: Persona): void {
    this.persona = persona;
  }

  async load(): Promise<HarnessConfig> {
    if (this.config) return this.config;

    const config = await this.mergeConfigs();
    this.config = config;
    return config;
  }

  private async mergeConfigs(): Promise<HarnessConfig> {
    // 1. Load global ~/.claude/settings.json (legacy)
    const globalSettings = this.loadGlobalSettings();

    // 2. Load project .claude/settings.json (source of truth)
    const projectSettings = this.loadProjectSettings();

    // 3. Load .ck.json (kit config)
  const ckConfig = this._ckConfig = this.loadCKConfig();

    // 4. Load MCP config
    const mcpConfig = this.loadMCPConfig();

    // 5. Load skills
    const skills = this.loadSkills();

    // 6. Load agents
    const agents = this.loadAgents();

    // 7. Determine LLM endpoint (3 vars: base_url, api_key, model)
    const llmEndpoint = this.resolveLLMEndpoint();

    // Build merged config
    return {
      configRoot: this.configRoot,
      persona: this.persona,
      model: ckConfig.modelOverrides?.[this.persona] || ckConfig.defaultModel || 'claude-fable-5',
      llmEndpoint,
  modelRouting: projectSettings.modelRouting,
      hooks: this.mergeHooks(globalSettings.hooks, projectSettings.hooks),
      mcpServers: [...(Array.isArray(globalSettings.mcpServers) ? globalSettings.mcpServers : []), ...(Array.isArray(projectSettings.mcpServers) ? projectSettings.mcpServers : []), ...(mcpConfig || [])],
      skills,
      agents,
      session: this.buildSessionConfig(ckConfig),
      memory: this.buildMemoryConfig(ckConfig),
    };
  }

  private loadGlobalSettings(): any {
    const globalPath = path.join(os.homedir(), '.claude', 'settings.json');
    if (fs.existsSync(globalPath)) {
      try {
        return JSON.parse(fs.readFileSync(globalPath, 'utf-8'));
      } catch {
        return {};
      }
    }
    return {};
  }

  private loadProjectSettings(): any {
    const projectPath = path.join(this.configRoot, '.claude', 'settings.json');
    if (fs.existsSync(projectPath)) {
      try {
        return JSON.parse(fs.readFileSync(projectPath, 'utf-8'));
      } catch {
        return {};
      }
    }
    return {};
  }

  private loadCKConfig(): any {
    const ckPath = path.join(this.configRoot, '.ck.json');
    if (fs.existsSync(ckPath)) {
      try {
        return JSON.parse(fs.readFileSync(ckPath, 'utf-8'));
      } catch {
        return {};
      }
    }
    return {};
  }

  private loadMCPConfig(): MCPServerConfig[] | null {
    const mcpPath = path.join(this.configRoot, '.claude', 'mcp.json');
    if (fs.existsSync(mcpPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(mcpPath, 'utf-8'));
        return data.mcpServers || [];
      } catch {
        return null;
      }
    }
    return null;
  }

  private loadSkills(): Skill[] {
    const skillsDir = path.join(this.configRoot, '.claude', 'skills');
    if (!fs.existsSync(skillsDir)) return [];

    const skills: Skill[] = [];
    const skillDirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const skillName of skillDirs) {
      const skillPath = path.join(skillsDir, skillName);
      const skillFile = path.join(skillPath, 'SKILL.md');
      if (fs.existsSync(skillFile)) {
        try {
          const content = fs.readFileSync(skillFile, 'utf-8');
          const meta = this.parseSkillMeta(content);
          skills.push({
            name: skillName,
            path: skillPath,
            description: meta.description || '',
            capabilities: meta.capabilities || [],
            version: meta.version || '1.0.0',
          });
        } catch {
          // Skip invalid skills
        }
      }
    }
    return skills;
  }

  private parseSkillMeta(content: string): any {
    const frontmatter = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatter) return {};
    try {
      const meta = yaml.parse(frontmatter[1]);
      return meta;
    } catch {
      return {};
    }
  }

  private loadAgents(): AgentDef[] {
    const agentsDir = path.join(this.configRoot, '.claude', 'agents');
    if (!fs.existsSync(agentsDir)) return [];

    const agents: AgentDef[] = [];
    const agentFiles = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md'));

    for (const file of agentFiles) {
      const agentPath = path.join(agentsDir, file);
      try {
        const content = fs.readFileSync(agentPath, 'utf-8');
        const meta = this.parseAgentMeta(content);
        agents.push({
          name: meta.name || file.replace('.md', ''),
          type: meta.type || 'stock',
          description: meta.description || '',
          allowedPaths: meta.allowedPaths,
          model: meta.model,
        });
      } catch {
        // Skip invalid agents
      }
    }
    return agents;
  }

  private parseAgentMeta(content: string): any {
    const frontmatter = content.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatter) return {};
    try {
      return yaml.parse(frontmatter[1]);
    } catch {
      return {};
    }
  }

  private resolveLLMEndpoint(): LLMEndpoint {
    // Priority: env > ck.json > global settings > .env > defaults
    const baseUrl = process.env.LLM_BASE_URL ||
      process.env.ANTHROPIC_BASE_URL ||
      process.env.OPENROUTER_BASE_URL ||
      'https://api.anthropic.com';

    const apiKey = process.env.LLM_API_KEY ||
      process.env.ANTHROPIC_API_KEY ||
      process.env.OPENROUTER_API_KEY ||
      process.env.DASHSCOPE_API_KEY ||
      process.env.GOOGLE_API_KEY ||
      process.env.OPENAI_API_KEY;

    const model = process.env.LLM_MODEL ||
      process.env.ANTHROPIC_MODEL ||
 process.env.MEKONG_MODEL ||
(this as any).ckConfig?.modelOverrides?.[this.persona] ||
      'claude-fable-5';

    let provider: LLMEndpoint['provider'] = 'anthropic';
    if (baseUrl.includes('openrouter')) provider = 'openrouter';
    else if (baseUrl.includes('dashscope')) provider = 'dashscope';
    else if (baseUrl.includes('googleapis') || baseUrl.includes('google')) provider = 'google';
    else if (baseUrl.includes('openai')) provider = 'openai';
    else if (baseUrl.includes('ollama') || baseUrl.includes('11434')) provider = 'ollama';
    else if (!apiKey) provider = 'offline';

    return { baseUrl, apiKey: apiKey || '', model, provider };
  }

  private get ckConfig(): any {
    if (!this._ckConfig) {
      this._ckConfig = this.loadCKConfig();
    }
    return this._ckConfig;
  }
  private _ckConfig: any = null;

  private mergeHooks(global: any, project: any): Hook[] {
    const hooks: Hook[] = [];

    // Global hooks
    if (global) {
      for (const [event, matchers] of Object.entries(global)) {
        if (Array.isArray(matchers)) {
          for (const matcher of matchers) {
            if (matcher.command) {
              hooks.push({
                event: event as any,
                matcher: matcher.matcher || '*',
                command: typeof matcher.command === 'string' ? matcher.command : matcher.command.join(' '),
                persona: 'both',
                timeout: matcher.timeout,
              });
            }
          }
        }
      }
    }

    // Project hooks override
    if (project) {
      for (const [event, matchers] of Object.entries(project)) {
        if (Array.isArray(matchers)) {
          for (const matcher of matchers) {
            if (matcher.command) {
              const idx = hooks.findIndex(h =>
                h.event === event && h.matcher === (matcher.matcher || '*')
              );
              if (idx >= 0) {
                hooks[idx] = {
                  ...hooks[idx],
                  command: typeof matcher.command === 'string' ? matcher.command : matcher.command.join(' '),
                  timeout: matcher.timeout,
                };
              } else {
                hooks.push({
                  event: event as any,
                  matcher: matcher.matcher || '*',
                  command: typeof matcher.command === 'string' ? matcher.command : matcher.command.join(' '),
                  persona: 'both',
                  timeout: matcher.timeout,
                });
              }
            }
          }
        }
      }
    }

    return hooks;
  }

  private buildSessionConfig(ckConfig: any): SessionConfig {
    return {
      id: `sess_${Date.now()}`,
      workingDir: process.cwd(),
      maxHistoryTokens: ckConfig.maxHistoryTokens || 200000,
      persistMemory: ckConfig.persistMemory !== false,
    };
  }

  private buildMemoryConfig(ckConfig: any): MemoryConfig {
    return {
      codebaseMemoryEnabled: ckConfig.codebaseMemory !== false,
      graphEnabled: ckConfig.graphMemory !== false,
      searchEnabled: ckConfig.searchMemory !== false,
      indexPath: path.join(this.configRoot, '.claude', 'codebase-memory'),
    };
  }

  getConfig(): HarnessConfig | null {
    return this.config;
  }

  getModel(): string {
    return this.config?.model || 'claude-opus-4-8';
  }

  getLLMEndpoint(): LLMEndpoint | undefined {
    return this.config?.llmEndpoint;
  }

  getHooks(): Hook[] {
    return this.config?.hooks || [];
  }

  getMCPServers(): MCPServerConfig[] {
    return this.config?.mcpServers || [];
  }

  getSkills(): Skill[] {
    return this.config?.skills || [];
  }

  getAgents(): AgentDef[] {
    return this.config?.agents || [];
  }

  getSessionConfig(): SessionConfig {
    return this.config?.session || { id: '', workingDir: process.cwd(), maxHistoryTokens: 200000, persistMemory: true };
  }

  getMemoryConfig(): MemoryConfig {
    return this.config?.memory || { codebaseMemoryEnabled: true, graphEnabled: true, searchEnabled: true };
  }
}