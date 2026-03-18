import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, basename, extname } from 'node:path';

export interface CommandDefinition {
  name: string;
  path: string;
  content: string;
  type: 'command';
}

export interface SkillDefinition {
  name: string;
  path: string;
  content: string;
  type: 'skill';
}

/**
 * Scan .claude/commands/ directory and return all .md command definitions.
 */
export function scanCommands(basePath: string): CommandDefinition[] {
  const commandsDir = join(basePath, '.claude', 'commands');
  return readMdFiles(commandsDir).map((entry) => ({
    name: basename(entry.file, extname(entry.file)),
    path: entry.file,
    content: entry.content,
    type: 'command' as const,
  }));
}

/**
 * Scan .claude/skills/ directory tree and return all SKILL.md definitions.
 */
export function scanSkills(basePath: string): SkillDefinition[] {
  const skillsDir = join(basePath, '.claude', 'skills');
  const results: SkillDefinition[] = [];

  let entries: string[];
  try {
    entries = readdirSync(skillsDir);
  } catch {
    return results;
  }

  for (const entry of entries) {
    const entryPath = join(skillsDir, entry);
    try {
      const stat = statSync(entryPath);
      if (!stat.isDirectory()) continue;
    } catch {
      continue;
    }

    const skillFile = join(entryPath, 'SKILL.md');
    let content: string;
    try {
      content = readFileSync(skillFile, 'utf8');
    } catch {
      continue;
    }

    results.push({
      name: entry,
      path: skillFile,
      content,
      type: 'skill',
    });
  }

  return results;
}

// --- helpers ---

interface FileEntry {
  file: string;
  content: string;
}

function readMdFiles(dir: string): FileEntry[] {
  const results: FileEntry[] = [];
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return results;
  }

  for (const entry of entries) {
    if (!entry.endsWith('.md')) continue;
    const filePath = join(dir, entry);
    try {
      const stat = statSync(filePath);
      if (!stat.isFile()) continue;
      results.push({ file: filePath, content: readFileSync(filePath, 'utf8') });
    } catch {
      continue;
    }
  }

  return results;
}
