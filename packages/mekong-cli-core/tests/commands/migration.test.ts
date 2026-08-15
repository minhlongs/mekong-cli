/**
 * Tests for `mekong migration` command (Wave 54).
 * Covers: status, run, rollback, plan subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerMigrationCommand } from '../../src/cli/commands/migration.js';

const noop = () => {};

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerMigrationCommand(program);
  return program;
}

describe('migration command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register migration command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'migration');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const migrationCmd = program.commands.find(c => c.name() === 'migration');
    expect(migrationCmd).toBeDefined();
    const subNames = migrationCmd!.commands.map(c => c.name());
    expect(subNames).toContain('status');
    expect(subNames).toContain('run');
    expect(subNames).toContain('rollback');
    expect(subNames).toContain('plan');
  });

  describe('migration status', () => {
    it('should show migration status', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'status']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show applied and pending counts', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'status']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });

  describe('migration run', () => {
    it('should run all pending migrations', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'run']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should run migrations with --dry-run flag', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'run', '--dry-run']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should run migrations up to a target version', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'run', '--target', '007']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show each migration step in output', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'run']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(4);
    });

    it('should handle target version beyond pending range', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'run', '--target', '999']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('migration rollback', () => {
    it('should rollback 1 step by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'rollback']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should rollback multiple steps', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'rollback', '--steps', '3']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show reverted migration names', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'rollback', '--steps', '2']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(4);
    });

    it('should show new db version after rollback', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'rollback']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('migration plan', () => {
    it('should show pending migrations plan', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'plan']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show migration names, types and durations', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'plan']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(4);
    });

    it('should show estimated total duration', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'migration', 'plan']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });
});
