import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { toClaudeFormat, toGeminiFormat } from './converter.js';
import type { UniversalCommand } from './converter.js';

export type InjectorFn = (
  commands: UniversalCommand[],
  projectPath: string
) => void;

const CLAUDE_MARKER_START = '<!-- openclaw:commands:start -->';
const CLAUDE_MARKER_END = '<!-- openclaw:commands:end -->';

/**
 * Append/replace openclaw command block in CLAUDE.md.
 * Idempotent: replaces existing block if markers are present.
 */
export function injectClaude(
  commands: UniversalCommand[],
  projectPath: string
): void {
  const claudePath = join(projectPath, 'CLAUDE.md');

  let existing = '';
  try {
    existing = readFileSync(claudePath, 'utf8');
  } catch {
    // file does not exist — start fresh
  }

  const lines = commands.map(toClaudeFormat).join('\n');
  const block = `${CLAUDE_MARKER_START}\n## Commands\n\n${lines}\n${CLAUDE_MARKER_END}`;

  let updated: string;
  if (
    existing.includes(CLAUDE_MARKER_START) &&
    existing.includes(CLAUDE_MARKER_END)
  ) {
    const re = new RegExp(
      `${escapeRe(CLAUDE_MARKER_START)}[\\s\\S]*?${escapeRe(CLAUDE_MARKER_END)}`
    );
    updated = existing.replace(re, block);
  } else {
    updated = existing ? `${existing}\n\n${block}\n` : `${block}\n`;
  }

  writeFileSync(claudePath, updated, 'utf8');
}

/**
 * Write each command as a separate YAML file under .gemini/commands/.
 */
export function injectGemini(
  commands: UniversalCommand[],
  projectPath: string
): void {
  const geminiDir = join(projectPath, '.gemini', 'commands');
  mkdirSync(geminiDir, { recursive: true });

  for (const cmd of commands) {
    const filePath = join(geminiDir, `${cmd.name}.yaml`);
    writeFileSync(filePath, toGeminiFormat(cmd) + '\n', 'utf8');
  }
}

/**
 * Factory: returns the injector function for the given provider name.
 * Throws for unknown providers.
 */
export function getInjectorForProvider(provider: string): InjectorFn {
  switch (provider.toLowerCase()) {
    case 'claude':
      return injectClaude;
    case 'gemini':
      return injectGemini;
    default:
      throw new Error(`Unknown provider: "${provider}". Supported: claude, gemini`);
  }
}

// --- helpers ---

function escapeRe(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
