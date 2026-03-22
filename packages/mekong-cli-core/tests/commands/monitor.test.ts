import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerMonitorCommand } from '../../src/cli/commands/monitor.js';

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
  registerMonitorCommand(program);
  return program;
}

describe('monitor command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  it('should register monitor command', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'monitor');
    expect(cmd).toBeDefined();
  });

  it('monitor should have 4 subcommands', () => {
    const program = createProgram();
    const monitor = program.commands.find(c => c.name() === 'monitor');
    expect(monitor).toBeDefined();
    const subNames = monitor!.commands.map(c => c.name());
    expect(subNames).toContain('uptime');
    expect(subNames).toContain('alerts');
    expect(subNames).toContain('incidents');
    expect(subNames).toContain('sla');
  });

  it('monitor uptime should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'monitor', 'uptime'])
    ).resolves.not.toThrow();
  });

  it('monitor alerts should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'monitor', 'alerts'])
    ).resolves.not.toThrow();
  });

  it('monitor incidents should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'monitor', 'incidents'])
    ).resolves.not.toThrow();
  });

  it('monitor sla should run without error', async () => {
    const program = createProgram();
    await expect(
      program.parseAsync(['node', 'test', 'monitor', 'sla'])
    ).resolves.not.toThrow();
  });

  it('monitor uptime description should mention uptime', () => {
    const program = createProgram();
    const monitor = program.commands.find(c => c.name() === 'monitor')!;
    const up = monitor.commands.find(c => c.name() === 'uptime');
    expect(up?.description()).toMatch(/[Uu]ptime/);
  });

  it('monitor alerts description should mention alerts', () => {
    const program = createProgram();
    const monitor = program.commands.find(c => c.name() === 'monitor')!;
    const al = monitor.commands.find(c => c.name() === 'alerts');
    expect(al?.description()).toMatch(/[Aa]lerts?/);
  });

  it('monitor incidents description should mention incidents', () => {
    const program = createProgram();
    const monitor = program.commands.find(c => c.name() === 'monitor')!;
    const inc = monitor.commands.find(c => c.name() === 'incidents');
    expect(inc?.description()).toMatch(/[Ii]ncidents?/);
  });

  it('monitor sla description should mention SLA', () => {
    const program = createProgram();
    const monitor = program.commands.find(c => c.name() === 'monitor')!;
    const sla = monitor.commands.find(c => c.name() === 'sla');
    expect(sla?.description()).toMatch(/[Ss][Ll][Aa]/);
  });

  it('monitor command description should mention monitoring', () => {
    const program = createProgram();
    const monitor = program.commands.find(c => c.name() === 'monitor')!;
    expect(monitor.description()).toMatch(/[Mm]onitor/);
  });
});
