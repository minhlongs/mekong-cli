import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { ToolRegistry } from '../../src/tools/registry.js';
import { SecurityManager } from '../../src/tools/security.js';
import { createShellTool } from '../../src/tools/builtin/shell.js';
import {
  createFileReadTool,
  createFileWriteTool,
  createFileSearchTool,
} from '../../src/tools/builtin/file-ops.js';
import { createGitTool } from '../../src/tools/builtin/git-ops.js';
import { createAskUserTool } from '../../src/tools/builtin/ask-user.js';

// ---------------------------------------------------------------------------
// SecurityManager
// ---------------------------------------------------------------------------

describe('SecurityManager', () => {
  it('auto-approves level 0 regardless of autoApproveLevel', async () => {
    const sm = new SecurityManager(0);
    expect((await sm.checkPermission('tool', 0, 'ctx')).allowed).toBe(true);
  });

  it('auto-approves level 1 when autoApproveLevel >= 1', async () => {
    const sm = new SecurityManager(1);
    expect((await sm.checkPermission('tool', 1, 'ctx')).allowed).toBe(true);
  });

  it('denies level 1 when autoApproveLevel is 0', async () => {
    const sm = new SecurityManager(0);
    const result = await sm.checkPermission('tool', 1, 'ctx');
    expect(result.allowed).toBe(false);
  });

  it('caches level 2 approval — asks only once per tool+context', async () => {
    const askFn = vi.fn().mockResolvedValue(true);
    const sm = new SecurityManager(0, askFn);
    await sm.checkPermission('tool', 2, 'ctx');
    await sm.checkPermission('tool', 2, 'ctx');
    expect(askFn).toHaveBeenCalledOnce();
  });

  it('always asks for level 3 (no cache)', async () => {
    const askFn = vi.fn().mockResolvedValue(true);
    const sm = new SecurityManager(0, askFn);
    await sm.checkPermission('tool', 3, 'ctx');
    await sm.checkPermission('tool', 3, 'ctx');
    expect(askFn).toHaveBeenCalledTimes(2);
  });

  it('grant/revoke manipulates the level-2 cache', async () => {
    const sm = new SecurityManager(0);
    sm.grant('tool', 'ctx');
    expect((await sm.checkPermission('tool', 2, 'ctx')).allowed).toBe(true);
    sm.revoke('tool', 'ctx');
    // After revoke, cache is empty — falls through to askUser which returns false
    expect((await sm.checkPermission('tool', 2, 'ctx')).allowed).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ToolRegistry
// ---------------------------------------------------------------------------

describe('ToolRegistry', () => {
  let registry: ToolRegistry;

  beforeEach(() => {
    // auto-approve levels 0-2 to avoid interactive prompts in tests
    registry = new ToolRegistry(new SecurityManager(2));
  });

  it('registers tools and reports correct size', () => {
    registry.register(createShellTool());
    registry.register(createFileReadTool());
    expect(registry.size).toBe(2);
  });

  it('has() reflects registered state', () => {
    registry.register(createShellTool());
    expect(registry.has('shell')).toBe(true);
    expect(registry.has('nonexistent')).toBe(false);
  });

  it('registerAll() bulk-registers tools', () => {
    registry.registerAll([createShellTool(), createFileReadTool(), createFileWriteTool()]);
    expect(registry.size).toBe(3);
  });

  it('listByCategory() filters correctly', () => {
    registry.registerAll([createShellTool(), createFileReadTool(), createGitTool()]);
    const shellTools = registry.listByCategory('shell');
    expect(shellTools).toContain('shell');
    expect(shellTools).toContain('git');
    const fsTools = registry.listByCategory('filesystem');
    expect(fsTools).toContain('file_read');
  });

  it('execute() runs a registered tool', async () => {
    registry.register(createShellTool());
    const result = await registry.execute('shell', { command: 'echo hello' });
    expect(result.success).toBe(true);
    expect(result.output).toContain('hello');
  });

  it('execute() returns error for unknown tool', async () => {
    const result = await registry.execute('nonexistent', {});
    expect(result.success).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('execute() respects security denial', async () => {
    // level 1 tool with autoApproveLevel 0 → denied
    const strictRegistry = new ToolRegistry(new SecurityManager(0));
    strictRegistry.register(createShellTool());
    const result = await strictRegistry.execute('shell', { command: 'echo hi' });
    expect(result.success).toBe(false);
    expect(result.error).toContain('Permission denied');
  });
});

// ---------------------------------------------------------------------------
// Builtin tools
// ---------------------------------------------------------------------------

describe('shell tool', () => {
  it('executes a simple command', async () => {
    const tool = createShellTool();
    const result = await tool.execute({ command: 'echo hello' });
    expect(result.success).toBe(true);
    expect(result.output).toContain('hello');
  });

  it('blocks dangerous patterns', async () => {
    const tool = createShellTool();
    const result = await tool.execute({ command: 'sudo rm -rf /' });
    expect(result.success).toBe(false);
    expect(result.error).toContain('Blocked');
  });

  it('respects custom blocked commands', async () => {
    const tool = createShellTool({ blockedCommands: ['forbidden'] });
    const result = await tool.execute({ command: 'echo forbidden' });
    expect(result.success).toBe(false);
  });
});

describe('file_read tool', () => {
  it('reads an existing file', async () => {
    const dir = join(tmpdir(), `mekong-read-${Date.now()}`);
    await mkdir(dir, { recursive: true });
    const filePath = join(dir, 'hello.txt');
    await writeFile(filePath, 'hello world', 'utf-8');

    const tool = createFileReadTool();
    const result = await tool.execute({ path: filePath });
    expect(result.success).toBe(true);
    expect(result.output).toBe('hello world');
  });

  it('returns error for missing file', async () => {
    const tool = createFileReadTool();
    const result = await tool.execute({ path: '/nonexistent/path/file.txt' });
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
  });
});

describe('file_write tool', () => {
  it('creates file and parent directories', async () => {
    const dir = join(tmpdir(), `mekong-write-${Date.now()}`);
    const filePath = join(dir, 'sub', 'out.txt');

    const tool = createFileWriteTool();
    const result = await tool.execute({ path: filePath, content: 'test content' });
    expect(result.success).toBe(true);
    expect(result.metadata?.path).toBe(filePath);
  });
});

describe('file_search tool', () => {
  it('finds files matching a glob pattern', async () => {
    const tool = createFileSearchTool();
    const result = await tool.execute({ pattern: '**/*.ts', cwd: 'src' });
    expect(result.success).toBe(true);
    expect((result.metadata?.count as number) ?? 0).toBeGreaterThan(0);
  });
});

describe('git tool', () => {
  it('runs git status', async () => {
    const tool = createGitTool();
    const result = await tool.execute({ command: 'status --short' });
    expect(result.success).toBe(true);
  });

  it('blocks force push', async () => {
    const tool = createGitTool();
    const result = await tool.execute({ command: 'push --force origin main' });
    expect(result.success).toBe(false);
    expect(result.error).toContain('Blocked');
  });

  it('blocks reset --hard', async () => {
    const tool = createGitTool();
    const result = await tool.execute({ command: 'reset --hard HEAD~1' });
    expect(result.success).toBe(false);
  });
});

describe('ask_user tool', () => {
  it('returns the injected answer', async () => {
    const tool = createAskUserTool(async () => 'yes');
    const result = await tool.execute({ question: 'Continue?' });
    expect(result.success).toBe(true);
    expect(result.output).toBe('yes');
  });

  it('uses default fallback when no askFn provided', async () => {
    const tool = createAskUserTool();
    const result = await tool.execute({ question: 'Continue?' });
    expect(result.success).toBe(true);
    expect(typeof result.output).toBe('string');
  });
});
