import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { scanCommands, scanSkills } from '../scanner.js';
import { toUniversalFormat, toClaudeFormat, toGeminiFormat } from '../converter.js';
import { injectClaude, injectGemini, getInjectorForProvider } from '../injector.js';

// ── fixtures ────────────────────────────────────────────────────────────────

const COOK_MD = `---
description: "Build/implement feature"
argument-hint: "description"
---
# Cook

Implements features end-to-end.
`;

const PLAN_MD = `---
description: "Plan complex task"
---
# Plan
`;

const SKILL_MD = `# Debug Skill

Systematic debugging references.
`;

// ── helpers ─────────────────────────────────────────────────────────────────

function makeFixtureRoot(): string {
  const root = join(tmpdir(), `command-loader-test-${Date.now()}`);
  const commandsDir = join(root, '.claude', 'commands');
  const skillsDir = join(root, '.claude', 'skills', 'debug');

  mkdirSync(commandsDir, { recursive: true });
  mkdirSync(skillsDir, { recursive: true });

  writeFileSync(join(commandsDir, 'cook.md'), COOK_MD, 'utf8');
  writeFileSync(join(commandsDir, 'plan.md'), PLAN_MD, 'utf8');
  writeFileSync(join(skillsDir, 'SKILL.md'), SKILL_MD, 'utf8');

  return root;
}

// ── scanner ─────────────────────────────────────────────────────────────────

describe('scanCommands', () => {
  let root: string;
  beforeEach(() => { root = makeFixtureRoot(); });
  afterEach(() => { rmSync(root, { recursive: true, force: true }); });

  it('returns both commands', () => {
    const cmds = scanCommands(root);
    expect(cmds).toHaveLength(2);
    expect(cmds.map((c) => c.name).sort()).toEqual(['cook', 'plan']);
  });

  it('sets type to command', () => {
    const cmds = scanCommands(root);
    expect(cmds.every((c) => c.type === 'command')).toBe(true);
  });

  it('returns empty array for missing dir', () => {
    expect(scanCommands('/nonexistent/path')).toEqual([]);
  });
});

describe('scanSkills', () => {
  let root: string;
  beforeEach(() => { root = makeFixtureRoot(); });
  afterEach(() => { rmSync(root, { recursive: true, force: true }); });

  it('finds the debug skill', () => {
    const skills = scanSkills(root);
    expect(skills).toHaveLength(1);
    expect(skills[0]?.name).toBe('debug');
    expect(skills[0]?.type).toBe('skill');
  });

  it('returns empty array for missing dir', () => {
    expect(scanSkills('/nonexistent/path')).toEqual([]);
  });
});

// ── converter ────────────────────────────────────────────────────────────────

describe('toUniversalFormat', () => {
  it('extracts frontmatter description', () => {
    const cmds = scanCommands(makeFixtureRoot());
    const cook = cmds.find((c) => c.name === 'cook')!;
    const u = toUniversalFormat(cook);
    expect(u.description).toBe('Build/implement feature');
    expect(u.trigger).toBe('/cook');
    expect(u.name).toBe('cook');
  });

  it('falls back to first heading when no frontmatter', () => {
    const fake = { name: 'test', path: '/tmp/test.md', content: '# My Tool\n\nDoes stuff.', type: 'command' as const };
    const u = toUniversalFormat(fake);
    expect(u.description).toBe('My Tool');
  });
});

describe('toClaudeFormat', () => {
  it('produces backtick trigger line', () => {
    const line = toClaudeFormat({ name: 'cook', description: 'Build feature', trigger: '/cook', content: '' });
    expect(line).toBe('- `/cook` - Build feature');
  });

  it('omits dash when description is empty', () => {
    const line = toClaudeFormat({ name: 'cook', description: '', trigger: '/cook', content: '' });
    expect(line).toBe('- `/cook`');
  });
});

describe('toGeminiFormat', () => {
  it('emits valid YAML fields', () => {
    const yaml = toGeminiFormat({ name: 'cook', description: 'Build "feature"', trigger: '/cook', content: '' });
    expect(yaml).toContain('name: "cook"');
    expect(yaml).toContain('trigger: "/cook"');
    expect(yaml).toContain('description: "Build \\"feature\\""');
  });
});

// ── injector ─────────────────────────────────────────────────────────────────

describe('injectClaude', () => {
  let root: string;
  beforeEach(() => { root = makeFixtureRoot(); });
  afterEach(() => { rmSync(root, { recursive: true, force: true }); });

  it('creates CLAUDE.md when absent', () => {
    const cmds = scanCommands(root).map(toUniversalFormat);
    injectClaude(cmds, root);
    const content = readFileSync(join(root, 'CLAUDE.md'), 'utf8');
    expect(content).toContain('<!-- openclaw:commands:start -->');
    expect(content).toContain('/cook');
  });

  it('replaces existing block idempotently', () => {
    const cmds = scanCommands(root).map(toUniversalFormat);
    injectClaude(cmds, root);
    injectClaude(cmds, root);
    const content = readFileSync(join(root, 'CLAUDE.md'), 'utf8');
    const count = (content.match(/openclaw:commands:start/g) ?? []).length;
    expect(count).toBe(1);
  });

  it('appends block to existing CLAUDE.md content', () => {
    writeFileSync(join(root, 'CLAUDE.md'), '# Existing\n', 'utf8');
    injectClaude(scanCommands(root).map(toUniversalFormat), root);
    const content = readFileSync(join(root, 'CLAUDE.md'), 'utf8');
    expect(content).toContain('# Existing');
    expect(content).toContain('<!-- openclaw:commands:start -->');
  });
});

describe('injectGemini', () => {
  let root: string;
  beforeEach(() => { root = makeFixtureRoot(); });
  afterEach(() => { rmSync(root, { recursive: true, force: true }); });

  it('writes one yaml file per command', () => {
    const cmds = scanCommands(root).map(toUniversalFormat);
    injectGemini(cmds, root);
    const cookYaml = readFileSync(join(root, '.gemini', 'commands', 'cook.yaml'), 'utf8');
    expect(cookYaml).toContain('trigger: "/cook"');
  });
});

describe('getInjectorForProvider', () => {
  it('returns injectClaude for "claude"', () => {
    expect(getInjectorForProvider('claude')).toBe(injectClaude);
  });

  it('returns injectGemini for "gemini"', () => {
    expect(getInjectorForProvider('gemini')).toBe(injectGemini);
  });

  it('throws for unknown provider', () => {
    expect(() => getInjectorForProvider('openai')).toThrow('Unknown provider');
  });
});
