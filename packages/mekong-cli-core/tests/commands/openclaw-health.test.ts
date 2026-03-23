/**
 * Tests for `mekong openclaw-health` command.
 * Covers: status, workers, queue, circuit subcommands with mock engine.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Command } from 'commander';
import { registerOpenClawHealthCommand } from '../../src/cli/commands/openclaw-health.js';

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
  registerOpenClawHealthCommand(program, engine);
  return program;
}

describe('openclaw-health command', () => {
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleSpy = vi.spyOn(console, 'log').mockImplementation(noop);
    vi.spyOn(console, 'error').mockImplementation(noop);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should register openclaw-health command on program', () => {
    const program = createProgram();
    const cmd = program.commands.find(c => c.name() === 'openclaw-health');
    expect(cmd).toBeDefined();
  });

  it('should register all 4 subcommands', () => {
    const program = createProgram();
    const healthCmd = program.commands.find(c => c.name() === 'openclaw-health');
    expect(healthCmd).toBeDefined();
    const subNames = healthCmd!.commands.map(c => c.name());
    expect(subNames).toContain('status');
    expect(subNames).toContain('workers');
    expect(subNames).toContain('queue');
    expect(subNames).toContain('circuit');
  });

  describe('status subcommand', () => {
    it('should call getHealth when engine.openclaw is available', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      expect(mockEngine.openclaw.getHealth).toHaveBeenCalled();
    });

    it('should display real uptime from engine (86400000ms = 1d 0m)', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      // 86400000ms = 1 day
      expect(output).toContain('1d');
    });

    it('should display AGI score from engine', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('95');
    });

    it('should display missions completed count', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('42');
    });

    it('should fallback to demo mode when engine.openclaw is undefined', async () => {
      const engine = { openclaw: undefined } as any;
      const program = createProgram(engine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should handle getHealth errors gracefully', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.getHealth = vi.fn().mockImplementation(() => { throw new Error('SDK error'); });
      const warnSpy = vi.spyOn(console, 'log');
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      expect(warnSpy).toHaveBeenCalled();
    });

    it('should show OPEN warning when circuit breaker is open', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.getHealth = vi.fn().mockReturnValue({
        uptime: 3600000,
        missionsCompleted: 10,
        missionsFailed: 8,
        agiScore: 60,
        circuitBreakerState: 'open',
      });
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'status']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('workers subcommand', () => {
    it('should list all 4 workers', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'workers']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('4');
    });

    it('should output worker IDs', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'workers']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('wkr_a1b2');
    });

    it('should show aggregate CPU and memory stats', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'workers']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('CPU');
      expect(output).toContain('Mem');
    });
  });

  describe('queue subcommand', () => {
    it('should call getHealth for real completed/failed counts', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'queue']);
      expect(mockEngine.openclaw.getHealth).toHaveBeenCalled();
    });

    it('should display real missionsCompleted from engine', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'queue']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('42');
    });

    it('should display real missionsFailed from engine', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'queue']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('2');
    });

    it('should fallback gracefully when getHealth throws', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.getHealth = vi.fn().mockImplementation(() => { throw new Error('unavailable'); });
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'queue']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('circuit subcommand', () => {
    it('should call getHealth for real circuit breaker state', async () => {
      const mockEngine = createMockEngine();
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'circuit']);
      expect(mockEngine.openclaw.getHealth).toHaveBeenCalled();
    });

    it('should display CLOSED state from engine', async () => {
      const program = createProgram();
      await program.parseAsync(['node', 'test', 'openclaw-health', 'circuit']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('CLOSED');
    });

    it('should display OPEN state when circuit is open', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.getHealth = vi.fn().mockReturnValue({
        uptime: 3600000,
        missionsCompleted: 5,
        missionsFailed: 6,
        agiScore: 50,
        circuitBreakerState: 'open',
      });
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'circuit']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('OPEN');
    });

    it('should display HALF-OPEN state when circuit is half-open', async () => {
      const mockEngine = createMockEngine();
      mockEngine.openclaw.getHealth = vi.fn().mockReturnValue({
        uptime: 3600000,
        missionsCompleted: 5,
        missionsFailed: 3,
        agiScore: 70,
        circuitBreakerState: 'half-open',
      });
      const program = createProgram(mockEngine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'circuit']);
      const output = consoleSpy.mock.calls.flat().join(' ');
      expect(output).toContain('HALF-OPEN');
    });

    it('should fallback to demo mode when engine.openclaw is undefined', async () => {
      const engine = { openclaw: undefined } as any;
      const program = createProgram(engine);
      await program.parseAsync(['node', 'test', 'openclaw-health', 'circuit']);
      expect(consoleSpy).toHaveBeenCalled();
    });
  });
});
