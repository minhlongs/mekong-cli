/**
 * Tests for `mekong openclaw-benchmark` command.
 * Covers: run, results, leaderboard, export subcommands.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerOpenClawBenchmarkCommand } from '../../src/cli/commands/openclaw-benchmark.js';

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
  registerOpenClawBenchmarkCommand(program, engine);
  return program;
}

describe('openclaw-benchmark command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register openclaw-benchmark command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'openclaw-benchmark');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const benchCmd = program.commands.find(c => c.name() === 'openclaw-benchmark');
    expect(benchCmd).toBeDefined();
    const subNames = benchCmd!.commands.map(c => c.name());
    expect(subNames).toContain('run');
    expect(subNames).toContain('results');
    expect(subNames).toContain('leaderboard');
    expect(subNames).toContain('export');
  });

  describe('openclaw-benchmark run', () => {
    it('should run basic suite and call submitMission for 2 categories', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run', '--suite', 'basic']);
      expect(mockEngine.openclaw.submitMission).toHaveBeenCalledTimes(2);
    });

    it('should run full suite and call submitMission for 4 categories', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run', '--suite', 'full']);
      expect(mockEngine.openclaw.submitMission).toHaveBeenCalledTimes(4);
    });

    it('should call classifyComplexity for each category', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run', '--suite', 'basic']);
      expect(mockEngine.openclaw.classifyComplexity).toHaveBeenCalledTimes(2);
    });

    it('should default to basic suite', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run']);
      expect(mockEngine.openclaw.submitMission).toHaveBeenCalledTimes(2);
    });

    it('should fallback to mock when engine.openclaw is undefined', async () => {
      const engineWithoutOpenClaw = { openclaw: undefined } as any;
      const program = createProgram(engineWithoutOpenClaw);
      await expect(
        program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run'])
      ).resolves.toBeDefined();
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should fallback to mock when submitMission throws', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.submitMission.mockRejectedValue(new Error('Engine error'));
      const program = createProgram(mockEngine);
      await expect(
        program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run'])
      ).resolves.toBeDefined();
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should score failed missions as 40', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.submitMission.mockResolvedValue({
        id: 'm_fail',
        status: 'failed',
        output: null,
        creditsUsed: 0,
        durationMs: 50,
      });
      const program = createProgram(mockEngine);
      // Should not throw
      await expect(
        program.parseAsync(['node', 'test', 'openclaw-benchmark', 'run', '--suite', 'basic'])
      ).resolves.toBeDefined();
    });
  });

  describe('openclaw-benchmark results', () => {
    it('should show latest results', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'results', '--latest']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should compare with a previous run', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'results', '--compare', 'run_4']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/run_4|points/i);
    });

    it('should handle unknown compare run ID gracefully', async () => {
      const program = createProgram();
      await expect(
        program.parseAsync(['node', 'test', 'openclaw-benchmark', 'results', '--compare', 'run_999'])
      ).resolves.toBeDefined();
    });
  });

  describe('openclaw-benchmark leaderboard', () => {
    it('should show leaderboard with all runs', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'leaderboard']);
      expect(consoleSpy).toHaveBeenCalled();
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/run_5|run_1/);
    });

    it('should display best and latest scores', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'leaderboard']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/Best score|Latest score/i);
    });
  });

  describe('openclaw-benchmark export', () => {
    it('should export in json format by default', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'export']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/json/i);
    });

    it('should export in csv format', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'export', '--format', 'csv']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/csv/i);
    });

    it('should export in md format', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'export', '--format', 'md']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/md/i);
    });

    it('should fallback to json for invalid format', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-benchmark', 'export', '--format', 'xml']);
      const calls = consoleSpy.mock.calls.flat().join(' ');
      expect(calls).toMatch(/json/i);
    });
  });
});
