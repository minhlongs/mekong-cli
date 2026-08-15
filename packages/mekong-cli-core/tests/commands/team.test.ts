/**
 * Tests for `mekong team` command (Wave 47).
 * Covers: create, list, assign, dashboard subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerTeamCommand } from '../../src/cli/commands/team.js';

// Suppress console output during tests
const noop = () => {};

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerTeamCommand(program);
  return program;
}

describe('team command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register team command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'team');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const teamCmd = program.commands.find(c => c.name() === 'team');
    expect(teamCmd).toBeDefined();
    const subNames = teamCmd!.commands.map(c => c.name());
    expect(subNames).toContain('create');
    expect(subNames).toContain('list');
    expect(subNames).toContain('assign');
    expect(subNames).toContain('dashboard');
  });

  describe('team create', () => {
    it('should create a team with given name', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'create', 'Đội Alpha']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create a team with custom member count', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'create', 'Đội Beta', '--members', '5']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should require name argument', async () => {
      const program = createProgram();
      await expect(
        program.parseAsync(['node', 'test', 'team', 'create'])
      ).rejects.toThrow();
    });
  });

  describe('team list', () => {
    it('should list all teams', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'list']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter teams by status active', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'list', '--status', 'active']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter teams by status idle', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'list', '--status', 'idle']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when no teams match filter', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'list', '--status', 'nonexistent']);
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  describe('team assign', () => {
    it('should assign task to team', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'assign', 'Đội Kỹ Thuật', 'Fix login bug']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should assign with high priority', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'team', 'assign', 'Đội Kinh Doanh', 'Q2 sales report', '--priority', 'high'
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should require both team and task arguments', async () => {
      const program = createProgram();
      await expect(
        program.parseAsync(['node', 'test', 'team', 'assign', 'Đội Alpha'])
      ).rejects.toThrow();
    });
  });

  describe('team dashboard', () => {
    it('should render team dashboard', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'dashboard']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('dashboard should output multiple lines', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'team', 'dashboard']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });
});
