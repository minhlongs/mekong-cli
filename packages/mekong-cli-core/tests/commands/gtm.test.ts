import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerGtmCommand } from '../../src/cli/commands/gtm.js';

// Suppress console output during tests
vi.mock('../../src/cli/ui/output.js', () => ({
  heading: vi.fn(),
  success: vi.fn(),
  info:    vi.fn(),
  warn:    vi.fn(),
  keyValue: vi.fn(),
  divider: vi.fn(),
}));

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: () => {}, writeErr: () => {} });
  registerGtmCommand(program);
  return program;
}

describe('gtm command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  it('should register gtm command', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'gtm');
    expect(cmd).toBeDefined();
  });

  it('gtm should have 4 subcommands', () => {
    const program = createProgram();
    const gtm = program.commands.find(c => c.name() === 'gtm');
    expect(gtm).toBeDefined();
    const subNames = gtm!.commands.map(c => c.name());
    expect(subNames).toContain('producthunt');
    expect(subNames).toContain('appsumo');
    expect(subNames).toContain('social');
    expect(subNames).toContain('schedule');
  });

  it('gtm producthunt should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'gtm', 'producthunt'])
    ).resolves.not.toThrow();
  });

  it('gtm appsumo should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'gtm', 'appsumo'])
    ).resolves.not.toThrow();
  });

  it('gtm social should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'gtm', 'social'])
    ).resolves.not.toThrow();
  });

  it('gtm schedule should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'gtm', 'schedule'])
    ).resolves.not.toThrow();
  });

  it('gtm producthunt description should match', () => {
    const program = createProgram();
    const gtm = program.commands.find(c => c.name() === 'gtm')!;
    const ph = gtm.commands.find(c => c.name() === 'producthunt');
    expect(ph?.description()).toContain('ProductHunt');
  });

  it('gtm appsumo description should mention AppSumo', () => {
    const program = createProgram();
    const gtm = program.commands.find(c => c.name() === 'gtm')!;
    const as = gtm.commands.find(c => c.name() === 'appsumo');
    expect(as?.description()).toContain('AppSumo');
  });

  it('gtm social description should mention social media', () => {
    const program = createProgram();
    const gtm = program.commands.find(c => c.name() === 'gtm')!;
    const sc = gtm.commands.find(c => c.name() === 'social');
    expect(sc?.description()).toMatch(/[Ss]ocial/);
  });

  it('gtm schedule description should mention schedule or timeline', () => {
    const program = createProgram();
    const gtm = program.commands.find(c => c.name() === 'gtm')!;
    const sched = gtm.commands.find(c => c.name() === 'schedule');
    expect(sched?.description()).toMatch(/[Ss]chedule|[Tt]imeline/);
  });

  it('gtm command description should mention go-to-market', () => {
    const program = createProgram();
    const gtm = program.commands.find(c => c.name() === 'gtm')!;
    expect(gtm.description()).toMatch(/[Gg]o-to-market|[Gg][Tt][Mm]/i);
  });
});
