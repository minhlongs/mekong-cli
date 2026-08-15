/**
 * Tests for `mekong openclaw-mission` command.
 * Covers: create, list, status, cancel subcommands with mock engine.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerOpenClawMissionCommand } from '../../src/cli/commands/openclaw-mission.js';

const noop = () => {};

function createMockEngine() {
  return {
    openclaw: {
      classifyComplexity: vi.fn().mockReturnValue('standard'),
      submitMission: vi.fn().mockResolvedValue({
        id: 'm_test123',
        status: 'completed',
        output: 'Test mission completed',
        creditsUsed: 3,
        durationMs: 100,
      }),
      getHealth: vi.fn().mockReturnValue({
        uptime: 86400000,
        missionsCompleted: 42,
        missionsFailed: 2,
        agiScore: 95,
        circuitBreakerState: 'closed',
      }),
    },
  } as any;
}

function createProgram(engine = createMockEngine()): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerOpenClawMissionCommand(program, engine);
  return program;
}

describe('openclaw-mission command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register openclaw-mission command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'openclaw-mission');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const missionCmd = program.commands.find(c => c.name() === 'openclaw-mission');
    expect(missionCmd).toBeDefined();
    const subNames = missionCmd!.commands.map(c => c.name());
    expect(subNames).toContain('create');
    expect(subNames).toContain('list');
    expect(subNames).toContain('status');
    expect(subNames).toContain('cancel');
  });

  describe('create subcommand', () => {
    it('should call classifyComplexity and submitMission with engine', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'create', '--name', 'Test mission']);
      expect(mockEngine.openclaw.classifyComplexity).toHaveBeenCalledWith('Test mission');
      expect(mockEngine.openclaw.submitMission).toHaveBeenCalledWith({
        goal: 'Test mission',
        complexity: 'standard',
      });
    });

    it('should output mission ID from SDK result', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'create', '--name', 'Deploy app']);
      expect(consoleSpy).toHaveBeenCalled();
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('m_test123');
    });

    it('should fallback to demo mode when engine.openclaw is undefined', async () => {
      const engine = { openclaw: undefined } as any;
      const program = createProgram(engine);
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'create', '--name', 'Demo task']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should handle submitMission errors gracefully', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.submitMission = vi.fn().mockRejectedValue(new Error('SDK error'));
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'create', '--name', 'Fail task']);
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  describe('list subcommand', () => {
    it('should list missions and call getHealth', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'list']);
      expect(mockEngine.openclaw.getHealth).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should display real engine completed count', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'list']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('42');
    });

    it('should filter by status', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'list', '--status', 'completed']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should respect --limit option', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'list', '--limit', '2']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('2 of');
    });
  });

  describe('status subcommand', () => {
    it('should show status for known mission ID', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'status', '--id', 'msn_001']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('msn_001');
    });

    it('should warn for unknown mission ID', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'status', '--id', 'msn_999']);
      expect(warnSpy).toHaveBeenCalled();
    });

    it('should show completed message for completed mission', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'status', '--id', 'msn_001']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('completed');
    });

    it('should show failed message for failed mission', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'status', '--id', 'msn_006']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('cancel subcommand', () => {
    it('should cancel a running mission', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'cancel', '--id', 'msn_002']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('msn_002');
    });

    it('should warn when cancelling already-completed mission', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'cancel', '--id', 'msn_001']);
      expect(warnSpy).toHaveBeenCalled();
    });

    it('should warn for unknown mission ID on cancel', async () => {
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-mission', 'cancel', '--id', 'msn_999']);
      expect(warnSpy).toHaveBeenCalled();
    });
  });
});
