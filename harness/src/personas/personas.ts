/**
 * Persona Definitions - Mekong (mk) and Agent Kit (ak)
 * Each persona has its own command set, model preferences, and behavior
 */

import { PersonaConfig, Persona, CommandDef, Hook } from '../core/types';

/**
 * Mekong Persona - The Agency OS persona
 * Commands: cook, fix, plan, deploy, strategy, finance, sales, particle, zenos, etc.
 */
export class MekongPersona implements PersonaConfig {
  name = 'mekong' as const;
  displayName = 'Mekong CLI';
  commandPrefixes = ['mk:', 'mekong:', 'strategy:', 'finance:', 'sales:', 'particle:', 'zenos:', 'studio:', 'revenue:'];
  defaultModel = 'claude-opus-4-8';
  availableCommands = [
    // Core commands
    'cook', 'fix', 'plan', 'code', 'test', 'deploy', 'review', 'ship', 'brainstorm', 'scout', 'journal',
    // Strategy & planning
    'strategy:analyze', 'strategy:plan', 'strategy:win3', 'annual', 'okr', 'swot', 'fundraise', 'pitch',
    // Business
    'sales', 'marketing', 'finance', 'hr', 'pricing', 'brand', 'outreach', 'content',
    // Product
    'roadmap', 'scope', 'sprint', 'idea:validate', 'idea:bmc', 'idea:prd',
    // Engineering
    'cook:fast', 'cook:deep', 'fix:auto', 'test:e2e', 'code:scaffold', 'deploy:cf', 'deploy:verify',
    // Ops
    'audit', 'health', 'security', 'status', 'clean',
    // Particles
    'particle:init', 'particle:graph', 'particle:cell', 'particle:zenpay',
    // ZenOS
    'binh-phap', 'zenos:constitution', 'zenos:audit', 'zenos:patrol',
  ];

  hooks: Hook[] = [
    {
      event: 'PreToolUse',
      matcher: 'Bash|Read|Write|Edit',
      command: '~/.claude/hooks/cbm-code-discovery-gate',
      persona: 'mekong',
    },
    {
      event: 'PreToolUse',
      matcher: 'Bash|Read|Glob',
      command: '~/.claude/hooks/scout-block.cjs',
      persona: 'mekong',
    },
    {
      event: 'PreToolUse',
      matcher: 'Read|Write|Edit|Bash',
      command: '~/.claude/hooks/privacy-block.cjs',
      persona: 'mekong',
    },
  ];

  getCommands(): CommandDef[] {
    return this.availableCommands.map(cmd => ({
      name: cmd,
      description: `Mekong command: ${cmd}`,
      persona: 'mekong' as const,
      aliases: this.getAliases(cmd),
      args: [],
      handler: `mekong-commands:${cmd}`,
    }));
  }

  private getAliases(cmd: string): string[] {
    const aliasMap: Record<string, string[]> = {
      'cook': ['c', 'build'],
      'fix': ['f', 'debug'],
      'plan': ['p', 'design'],
      'test': ['t'],
      'deploy': ['d', 'ship'],
      'review': ['r', 'code-review'],
      'brainstorm': ['bs', 'ideate'],
      'scout': ['s', 'search'],
      'journal': ['j', 'log'],
    };
    return aliasMap[cmd] || [];
  }
}

/**
 * Agent Kit Persona - The Claude Code / Agent Kit persona
 * Commands: plan, cook, fix, review, scout, brainstorm, code, test, ship, docs, simplify, preview, etc.
 */
export class AgentKitPersona implements PersonaConfig {
  name = 'agentkit' as const;
  displayName = 'Agent Kit (ak)';
  commandPrefixes = ['ak:', 'agentkit:', 'plan:', 'cook:', 'fix:', 'review:', 'scout:', 'debug:', 'brainstorm:'];
  defaultModel = 'claude-opus-4-8';
  availableCommands = [
    // Core workflow
    'plan', 'cook', 'fix', 'review', 'scout', 'debug', 'brainstorm', 'code', 'test', 'ship',
    // Quality
    'simplify', 'typecheck', 'lint',
    // Testing
    'test:watch', 'test:coverage', 'test:e2e',
    // Visualization
    'preview', 'preview:explain', 'preview:diagram', 'preview:slides',
    // Design & UI
    'design', 'stitch', 'excalidraw', 'threejs', 'shader', 'remotion',
    // Research
    'research', 'ask', 'find-skills',
    // AI/ML
    'context-engineering', 'google-adk-python', 'ai-multimodal',
    // Documentation
    'docs', 'docs:update', 'markdown-novel-viewer', 'mintlify', 'mermaidjs-v11',
    // Frameworks
    'web-frameworks', 'tanstack', 'mobile-development', 'shopify',
    // Backend
    'backend-development', 'better-auth', 'payment-integration', 'databases', 'devops', 'deploy',
    // Security
    'security', 'cti-expert',
    // Browser
    'web-testing', 'agent-browser', 'chrome-profile',
    // Media
    'media-processing', 'ai-artist',
    // Office
    'docx', 'pdf', 'pptx', 'xlsx',
  ];

  hooks: Hook[] = [
    {
      event: 'PreToolUse',
      matcher: 'Bash|Read|Write|Edit',
      command: '~/.claude/hooks/cbm-code-discovery-gate',
      persona: 'agentkit',
    },
    {
      event: 'PreToolUse',
      matcher: 'Bash|Read|Glob',
      command: '~/.claude/hooks/scout-block.cjs',
      persona: 'agentkit',
    },
    {
      event: 'PreToolUse',
      matcher: 'Read|Write|Edit|Bash',
      command: '~/.claude/hooks/privacy-block.cjs',
      persona: 'agentkit',
    },
    {
      event: 'SubagentStart',
      matcher: '*',
      command: '~/.claude/hooks/subagent-init.cjs',
      persona: 'agentkit',
    },
    {
      event: 'SessionStart',
      matcher: '*',
      command: '~/.claude/hooks/session-init.cjs',
      persona: 'agentkit',
    },
  ];

  getCommands(): CommandDef[] {
    return this.availableCommands.map(cmd => ({
      name: cmd,
      description: `Agent Kit command: ${cmd}`,
      persona: 'agentkit' as const,
      aliases: this.getAliases(cmd),
      args: [],
      handler: `agentkit-commands:${cmd}`,
    }));
  }

  private getAliases(cmd: string): string[] {
    const aliasMap: Record<string, string[]> = {
      'cook': ['c', 'implement'],
      'fix': ['f', 'debug'],
      'plan': ['p', 'design'],
      'test': ['t'],
      'review': ['r', 'cr'],
      'scout': ['s', 'search'],
      'debug': ['dbg'],
      'brainstorm': ['bs', 'ideate'],
      'simplify': ['simp', 'refactor'],
      'preview': ['prev'],
      'research': ['rsch'],
      'docs': ['doc'],
      'design': ['ui'],
    };
    return aliasMap[cmd] || [];
  }
}

/**
 * Get persona instance by name
 */
export function getPersonaConfig(persona: Persona): PersonaConfig {
  switch (persona) {
    case 'mekong':
      return new MekongPersona();
    case 'agentkit':
      return new AgentKitPersona();
    default:
      throw new Error(`Unknown persona: ${persona}`);
  }
}

/**
 * Alias for backward compatibility
 */
export function getPersona(persona: Persona): PersonaConfig {
  return getPersonaConfig(persona);
}

/**
 * Detect persona from command input
 */
export function detectPersona(input: string): Persona | null {
  // Explicit persona prefixes
  if (/^(mk|mekong|strategy|finance|sales|particle|zenos|studio|revenue):/.test(input.trim())) {
    return 'mekong';
  }
  if (/^ak:/.test(input.trim())) {
    return 'agentkit';
  }

  // Command-based detection
  const mekongCommands = ['binh-phap', 'strategy:', 'finance:', 'sales:', 'particle:', 'zenos:', 'studio:', 'revenue:', 'outreach', 'content', 'crm', 'billing', 'payouts', 'affiliates', 'promo', 'refunds', 'venture', 'dealflow', 'expert'];
  const agentkitCommands = ['simplify', 'preview:', 'stitch', 'excalidraw', 'mermaidjs-v11', 'tech-graph', 'markdown-novel-viewer', 'watzup', 'retro', 'docs-seeker', 'cti-expert', 'google-adk-python', 'context-engineering', 'use-mcp', 'agentize', 'team', 'worktree', 'find-skills'];

  const firstWord = input.trim().split(/\s+/)[0].toLowerCase();

  if (mekongCommands.some(c => firstWord.startsWith(c))) return 'mekong';
  if (agentkitCommands.some(c => firstWord.startsWith(c))) return 'agentkit';

  return null;
}

/**
 * Command router - routes command to appropriate persona
 */
export function routeCommand(input: string, currentPersona: Persona): {
  targetPersona: Persona;
  command: string;
  needsSwitch: boolean;
} {
  // Check for explicit prefix
  if (/^(mk|mekong|strategy|finance|sales|particle|zenos|studio|revenue):/.test(input.trim())) {
    return { targetPersona: 'mekong', command: input.replace(/^(mk|mekong|strategy|finance|sales|particle|zenos|studio|revenue):\s*/, ''), needsSwitch: currentPersona !== 'mekong' };
  }
  if (/^ak:/.test(input.trim())) {
    return { targetPersona: 'agentkit', command: input.replace(/^ak:\s*/, ''), needsSwitch: currentPersona !== 'agentkit' };
  }

  // Detect from command
  const detected = detectPersona(input);
  if (detected && detected !== currentPersona) {
    return { targetPersona: detected, command: input, needsSwitch: true };
  }

  return { targetPersona: currentPersona, command: input, needsSwitch: false };
}