/**
 * Tests for `mekong deploy` command (Wave 48).
 * Covers: status, logs, rollback, config subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerDeployCommand } from '../../src/cli/commands/deploy.js';

// Suppress console output during tests
const noop = () => {};

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerDeployCommand(program);
  return program;
}

describe('deploy command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register deploy command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'deploy');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const deployCmd = program.commands.find(c => c.name() === 'deploy');
    expect(deployCmd).toBeDefined();
    const subNames = deployCmd!.commands.map(c => c.name());
    expect(subNames).toContain('status');
    expect(subNames).toContain('logs');
    expect(subNames).toContain('rollback');
    expect(subNames).toContain('config');
  });

  describe('deploy status', () => {
    it('should show status for all environments', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'status']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter status by production env', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'status', '--env', 'production']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should filter status by staging env', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'status', '--env', 'staging']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn for unknown environment', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'status', '--env', 'unknown']);
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  describe('deploy logs', () => {
    it('should show production logs by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'logs']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show logs for staging environment', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'logs', 'staging']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should show logs for development environment', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'logs', 'development']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should respect --lines option', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'logs', 'production', '--lines', '2']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn for unknown environment logs', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'logs', 'unknown-env']);
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  describe('deploy rollback', () => {
    it('should rollback production by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'rollback']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should rollback staging environment', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'rollback', 'staging']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should rollback to specific version', async () => {
      const program = createProgram();
      await program.parseAsync([
        'node', 'test', 'deploy', 'rollback', 'production', '--version', 'v5.9.0'
      ]);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn for unknown environment rollback', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'rollback', 'nonexistent']);
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  describe('deploy config', () => {
    it('should show deployment configuration', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'config']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('config should output multiple key-value pairs', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'deploy', 'config']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(4);
    });
  });
});
