/**
 * Command Router - Routes commands to appropriate persona handlers
 * Supports /mk:* and /ak:* prefixes for explicit persona selection
 */

import { CommandDef, CommandRoute, RouteResult, Persona, HarnessConfig } from './types';
import * as fs from 'fs';
import * as path from 'path';

export class CommandRouter {
  private commands: Map<string, CommandDef> = new Map();
  private personaPrefixes: Record<Persona, string[]> = {
    mekong: ['mk', 'mekong', 'strategy', 'finance', 'particle', 'studio', 'sales', 'marketing', 'outreach', 'ops', 'revenue', 'setup', 'bridge', 'workflow', 'content', 'finance', 'dashboard', 'activate', 'status', 'setup-vibe', 'analyze', 'plan', 'win3', 'cook', 'test', 'ship', 'scaffold', 'tui', 'agents'],
    agentkit: ['plan', 'cook', 'fix', 'review', 'scout', 'debug', 'brainstorm', 'code', 'test', 'ship', 'docs', 'simplify', 'preview', 'stitch', 'research', 'design', 'deploy', 'retro', 'watzup', 'ask', 'tech-graph', 'excalidraw', 'copywriting', 'marketing', 'find-skills', 'use-mcp', 'sequential-thinking', 'context-engineering', 'better-auth', 'payment-integration', 'databases', 'deploy', 'devops', 'security', 'cti-expert', 'web-testing', 'agent-browser', 'chrome-profile', 'media-processing', 'ai-artist', 'docx', 'pdf', 'pptx', 'xlsx', 'mintlify', 'mermaidjs-v11', 'markdown-novel-viewer', 'google-adk-python', 'tanstack', 'web-frameworks', 'mobile-development', 'shopify', 'threejs', 'shader', 'remotion', 'ai-multimodal'],
  };

  private commandAliases: Record<string, string> = {
    'ak': 'agentkit',
    'mk': 'mekong',
  };

  constructor(private config: HarnessConfig) {
    this.loadCommands();
  }

  private loadCommands(): void {
    const commandsDir = path.join(this.config.configRoot, '.claude', 'commands');
    if (!fs.existsSync(commandsDir)) return;

    const files = fs.readdirSync(commandsDir).filter(f => f.endsWith('.md'));

    for (const file of files) {
      const cmdPath = path.join(commandsDir, file);
      try {
        const content = fs.readFileSync(cmdPath, 'utf-8');
        const command = this.parseCommand(file, content);
        if (command) {
          this.commands.set(command.name, command);
          // Also register aliases
          for (const alias of command.aliases) {
            this.commands.set(alias, command);
          }
        }
      } catch {
        // Skip invalid commands
      }
    }
  }

  private parseCommand(file: string, content: string): CommandDef | null {
    const name = file.replace('.md', '');
    const lines = content.split('\n');
    let description = '';
    let persona: Persona | 'both' = 'both';
    let args: any[] = [];
    let handler = '';

    // Parse frontmatter
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (frontmatterMatch) {
      try {
        const meta = JSON.parse(frontmatterMatch[1].replace(/:\s*(\w+)/g, ': "$1"'));
        description = meta.description || description;
        persona = meta.persona || persona;
        args = meta.args || args;
        handler = meta.handler || handler;
      } catch {
        // Not JSON, try YAML-like
      }
    }

    // Determine persona from command name / category
    const inferredPersona = this.inferPersona(name);
    const finalPersona = persona === 'both' ? inferredPersona : persona;

    return {
      name,
      description: description || `Command: ${name}`,
      persona: finalPersona,
      aliases: [name],
      args,
      handler: handler || `commands/${name}:execute`,
    };
  }

  private inferPersona(name: string): Persona {
    // Check mekong prefixes
    for (const prefix of this.personaPrefixes.mekong) {
      if (name.startsWith(`${prefix}-`) || name === prefix) {
        return 'mekong';
      }
    }
    for (const prefix of this.personaPrefixes.agentkit) {
      if (name.startsWith(`${prefix}-`) || name === prefix) {
        return 'agentkit';
      }
    }

    // Default based on config persona
    return this.config.persona;
  }

  route(input: string, currentPersona: Persona): RouteResult {
    // Parse input
    const parts = input.trim().split(/\s+/);
    if (parts.length === 0) {
      return { matched: null, args: {}, targetPersona: currentPersona, needsPersonaSwitch: false };
    }

    let commandName = parts[0];
    const args: Record<string, any> = {};
    const rawArgs = parts.slice(1);

    // Check for explicit persona prefix (/mk: or /ak:)
    let targetPersona = currentPersona;
    let isExplicitPersona = false;

    if (commandName.startsWith('/')) {
      commandName = commandName.slice(1); // Remove leading /

      // Check for /mk:command or /ak:command
      const personaPrefixMatch = commandName.match(/^(mk|mekong|ak|agentkit):(.+)$/);
      if (personaPrefixMatch) {
        const prefix = personaPrefixMatch[1];
        commandName = personaPrefixMatch[2];
        targetPersona = prefix.startsWith('m') ? 'mekong' : 'agentkit';
        isExplicitPersona = true;
      }
    }

    // Normalize command name (remove parent command prefix if present)
    // e.g., "mekong cook" -> "cook" when in mekong persona
    const mekongPrefixes = ['mekong', 'mk'];
    const agentkitPrefixes = ['agentkit', 'ak'];

    if (mekongPrefixes.includes(commandName) && rawArgs.length > 0) {
      commandName = rawArgs.shift() || '';
    }
    if (agentkitPrefixes.includes(commandName) && rawArgs.length > 0) {
      commandName = rawArgs.shift() || '';
    }

    // Look up command
    const command = this.commands.get(commandName);

    if (!command) {
      // Try fuzzy matching / suggestions
      const suggestions = this.findSimilarCommands(commandName);
      return {
        matched: null,
        args: {},
        targetPersona: currentPersona,
        needsPersonaSwitch: false,
        suggestions,
      };
    }

    // Parse args (simple key=value or positional)
    for (let i = 0; i < rawArgs.length; i++) {
      const arg = rawArgs[i];
      if (arg.startsWith('--')) {
        const key = arg.slice(2);
        const next = rawArgs[i + 1];
        if (next && !next.startsWith('--')) {
          args[key] = next;
          i++;
        } else {
          args[key] = true;
        }
      } else if (arg.startsWith('-')) {
        const key = arg.slice(1);
        const next = rawArgs[i + 1];
        if (next && !next.startsWith('-')) {
          args[key] = next;
          i++;
        } else {
          args[key] = true;
        }
      } else {
        // Positional - use first available arg name from command definition
        const positionalArgs = command.args.filter(a => !args[a.name]);
        if (positionalArgs.length > 0) {
          args[positionalArgs[0].name] = arg;
        }
      }
    }

    const needsPersonaSwitch = targetPersona !== currentPersona && isExplicitPersona;

    return {
      matched: command,
      args,
      targetPersona,
      needsPersonaSwitch,
      suggestions: [],
    };
  }

  private findSimilarCommands(name: string): string[] {
    const allCommands = Array.from(this.commands.keys());
    const scored = allCommands.map(cmd => ({
      cmd,
      score: this.levenshteinDistance(name, cmd),
    }));
    scored.sort((a, b) => a.score - b.score);
    return scored.slice(0, 5).map(s => s.cmd);
  }

  private levenshteinDistance(a: string, b: string): number {
    const matrix = Array(b.length + 1).fill(null).map(() => Array(a.length + 1).fill(null));
    for (let i = 0; i <= a.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= b.length; j++) matrix[j][0] = j;

    for (let j = 1; j <= b.length; j++) {
      for (let i = 1; i <= a.length; i++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,
          matrix[j - 1][i] + 1,
          matrix[j - 1][i - 1] + cost,
        );
      }
    }
    return matrix[b.length][a.length];
  }

  getCommand(name: string): CommandDef | undefined {
    return this.commands.get(name);
  }

  getAllCommands(): CommandDef[] {
    return Array.from(this.commands.values());
  }

  getCommandsForPersona(persona: Persona): CommandDef[] {
    return this.getAllCommands().filter(c => c.persona === persona || c.persona === 'both');
  }
}