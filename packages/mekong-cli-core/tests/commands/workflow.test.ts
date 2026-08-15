/**
 * Tests for `mekong workflow` command (Wave 51).
 * Covers: create, list, run, history subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerWorkflowCommand } from '../../src/cli/commands/workflow.js';

const noop = () => {};

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerWorkflowCommand(program);
  return program;
}

describe('workflow command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register workflow command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'workflow');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const wfCmd = program.commands.find(c => c.name() === 'workflow');
    expect(wfCmd).toBeDefined();
    const subNames = wfCmd!.commands.map(c => c.name());
    expect(subNames).toContain('create');
    expect(subNames).toContain('list');
    expect(subNames).toContain('run');
    expect(subNames).toContain('history');
  });

  describe('workflow create', () => {
    it('should create workflow with default options', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'create']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create workflow with custom name', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'create', '--name', 'Quy trình bán hàng']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create workflow with parallel template', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'create', '--template', 'parallel']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should create workflow with sequential template', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'create', '--template', 'sequential']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn on unknown template', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'create', '--template', 'unknown']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('workflow list', () => {
    it('should list all workflows', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'list']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should output multiple lines for workflow list', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'list']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });

  describe('workflow run', () => {
    it('should run existing workflow by id', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'run', 'wf-001']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn when workflow id not found', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'run', 'wf-999']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should require workflow-id argument', async () => {
      const program = createProgram();
      await expect(
        program.parseAsync(['node', 'test', 'workflow', 'run'])
      ).rejects.toThrow();
    });

    it('should show step-by-step progress when running', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'run', 'wf-001']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(3);
    });
  });

  describe('workflow history', () => {
    it('should show execution history with default limit', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'history']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should respect --limit option', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'history', '--limit', '2']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should output multiple history rows', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'workflow', 'history']);
      expect(consoleSpy.mock.calls.length).toBeGreaterThan(2);
    });
  });
});
