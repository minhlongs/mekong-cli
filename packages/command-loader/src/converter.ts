import type { CommandDefinition } from './scanner.js';

export interface UniversalCommand {
  name: string;
  description: string;
  trigger: string;
  content: string;
  provider?: string;
}

/**
 * Extract description from frontmatter `description:` field, falling back to
 * the first non-empty line of body content.
 */
function extractDescription(content: string): string {
  const fmMatch = content.match(/^---[\s\S]*?description:\s*["']?([^"'\n]+)["']?/m);
  if (fmMatch?.[1]) return fmMatch[1].trim();

  const lines = content.split('\n');
  for (const line of lines) {
    const trimmed = line.replace(/^#+\s*/, '').trim();
    if (trimmed && !trimmed.startsWith('---')) return trimmed;
  }
  return '';
}

/**
 * Convert a CommandDefinition (or SkillDefinition) to provider-neutral JSON.
 */
export function toUniversalFormat(def: CommandDefinition): UniversalCommand {
  const trigger = `/${def.name}`;
  return {
    name: def.name,
    description: extractDescription(def.content),
    trigger,
    content: def.content,
  };
}

/**
 * Format a UniversalCommand for CLAUDE.md injection as a list entry.
 */
export function toClaudeFormat(cmd: UniversalCommand): string {
  const desc = cmd.description ? ` - ${cmd.description}` : '';
  return `- \`${cmd.trigger}\`${desc}`;
}

/**
 * Format a UniversalCommand for .gemini config injection (YAML-style entry).
 */
export function toGeminiFormat(cmd: UniversalCommand): string {
  const safeDesc = cmd.description.replace(/"/g, '\\"');
  return [
    `name: "${cmd.name}"`,
    `trigger: "${cmd.trigger}"`,
    `description: "${safeDesc}"`,
  ].join('\n');
}
