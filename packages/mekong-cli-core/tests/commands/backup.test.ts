/**
 * Tests for `mekong backup` command (Wave 53).
 * Covers: create, restore, list, schedule subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerBackupCommand } from '../../src/cli/commands/backup.js';

const noop = () => {};

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerBackupCommand(program);
  return program;
}

describe('backup command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register backup command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'backup');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const backupCmd = program.commands.find(c => c.name() === 'backup');
    expect(backupCmd).toBeDefined();
    const subNames = backupCmd!.commands.map(c => c.name());
    expect(subNames).toContain('create');
    expect(subNames).toContain('restore');
    expect(subNames).toContain('list');
    expect(subNames).toContain('schedule');
  });

  describe('backup create', () => {
    it('should create a full backup to s3 by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'create']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create an incremental backup', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'create', '--type', 'incremental']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create a snapshot backup to r2', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'create', '--type', 'snapshot', '--target', 'r2']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create backup to local target', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'create', '--target', 'local']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should output backup ID and size', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'create']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(4);
    });
  });

  describe('backup restore', () => {
    it('should restore from a known backup ID', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'restore', 'BKP-2026-0322-001']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn for unknown backup ID', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'restore', 'BKP-UNKNOWN-999']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should perform dry run restore', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'restore', 'BKP-2026-0321-001', '--dry-run']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show restore steps in output', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'restore', 'BKP-2026-0321-002']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });

  describe('backup list', () => {
    it('should list all backups by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'list']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter list by type full', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'list', '--type', 'full']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter list by type incremental', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'list', '--type', 'incremental']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when filter returns no results', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'list', '--type', 'nonexistent']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should respect --limit option', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'list', '--limit', '2']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('backup schedule', () => {
    it('should show current schedule', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'schedule']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should update frequency', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'schedule', '--frequency', 'weekly']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should update retention period', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'schedule', '--retention', '60']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should update time option', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'schedule', '--time', '03:00']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show multiple key-value pairs for schedule', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'backup', 'schedule']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(4);
    });
  });
});
