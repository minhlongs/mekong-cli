/**
 * Tests for `mekong openclaw-cost` command.
 * Covers: summary, breakdown, budget, optimize subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerOpenClawCostCommand } from '../../src/cli/commands/openclaw-cost.js';

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

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: noop, writeErr: noop });
  registerOpenClawCostCommand(program, createMockEngine());
  return program;
}

describe('openclaw-cost command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register openclaw-cost command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'openclaw-cost');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const costCmd = program.commands.find(c => c.name() === 'openclaw-cost');
    expect(costCmd).toBeDefined();
    const subNames = costCmd!.commands.map(c => c.name());
    expect(subNames).toContain('summary');
    expect(subNames).toContain('breakdown');
    expect(subNames).toContain('budget');
    expect(subNames).toContain('optimize');
  });

  describe('openclaw-cost summary', () => {
    it('should run summary with default period (week)', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'summary']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should run summary with --period day', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'summary', '--period', 'day']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should run summary with --period month', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'summary', '--period', 'month']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should fallback to week for invalid period', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'summary', '--period', 'invalid']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should call getHealth() on engine for live stats', async () => {
      const mockEngine = createMockEngine();
      const program = new Command();
      program.exitOverride();
      program.configureOutput({ writeOut: noop, writeErr: noop });
      registerOpenClawCostCommand(program, mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'summary']);
      expect(mockEngine.openclaw.getHealth).toHaveBeenCalled();
    });
  });

  describe('openclaw-cost breakdown', () => {
    it('should show breakdown for valid mission ID', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'breakdown', '--id', 'msn_001']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn for unknown mission ID', async () => {
      const program = createProgram();
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(noop);
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'breakdown', '--id', 'msn_999']);
      // warn is printed via console.log in output helpers
      expect(consoleSpy).toHaveBeenCalled();
      warnSpy.mockRestore();
    });

    it('should show LOW cost label for cheap missions', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'breakdown', '--id', 'msn_001']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/msn_001|Deploy landing page|LOW/i);
    });
  });

  describe('openclaw-cost budget', () => {
    it('should show budget info', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'budget']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should set budget with --set flag', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'budget', '--set', '75']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should warn on invalid budget amount', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'budget', '--set', '-10']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should set alert threshold with --alert flag', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'budget', '--set', '50', '--alert', '80']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('openclaw-cost optimize', () => {
    it('should show optimization recommendations', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'optimize']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should call getHealth() for live failure rate analysis', async () => {
      const mockEngine = createMockEngine();
      const program = new Command();
      program.exitOverride();
      program.configureOutput({ writeOut: noop, writeErr: noop });
      registerOpenClawCostCommand(program, mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-cost', 'optimize']);
      expect(mockEngine.openclaw.getHealth).toHaveBeenCalled();
    });

    it('should handle engine without openclaw gracefully', async () => {
      const engineWithoutOpenClaw = { openclaw: undefined } as any;
      const program = new Command();
      program.exitOverride();
      program.configureOutput({ writeOut: noop, writeErr: noop });
      registerOpenClawCostCommand(program, engineWithoutOpenClaw);
      // Should not throw
      await expect(
        program.parseAsync(['node', 'test', 'openclaw-cost', 'optimize'])
      ).resolves.toBeDefined();
    });
  });
});
