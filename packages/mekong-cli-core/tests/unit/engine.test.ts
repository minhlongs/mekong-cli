import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MekongEngine } from '../../src/core/engine.js';
import { Gateway } from '../../src/core/gateway.js';
import { Scheduler } from '../../src/core/scheduler.js';
import { heading, success, error, warn, info, keyValue, divider } from '../../src/cli/ui/output.js';

// ---------------------------------------------------------------------------
// Mock loadConfig to avoid file I/O and LLM env requirements
// ---------------------------------------------------------------------------
vi.mock('../../src/config/loader.js', () => ({
  loadConfig: vi.fn().mockResolvedValue({
    version: '0.1.0',
    llm: {
      default_provider: 'test',
      default_model: 'test-model',
      providers: {},
      fallback_chain: [],
    },
    agents: {
      max_concurrent: 3,
      default_timeout: '300s',
      max_iterations: 10,
      max_tokens_per_turn: 4096,
      wip_limit: 3,
      timeout_seconds: 300,
    },
    budget: {
      max_cost_per_task: 1,
      max_tokens_per_task: 100000,
      max_time_seconds: 300,
      warn_at_percent: 80,
    },
    tools: {
      security_level: 2,
      allowed_directories: ['.'],
      blocked_commands: [],
      auto_approve_level: '2',
      sandbox_shell: false,
    },
    heartbeat: {
      interval: '30s',
      stale_threshold: '300s',
      auto_checkpoint: true,
      enabled: false,
      interval_minutes: 30,
      checklist_file: 'HEARTBEAT.md',
    },
    memory: {
      session_dir: '/tmp/test-sessions',
      knowledge_dir: '/tmp/test-knowledge',
      max_entries: 1000,
      compact_after: 500,
      max_session_size_mb: 10,
      auto_compact: false,
    },
  }),
}));

// ---------------------------------------------------------------------------
// MekongEngine
// ---------------------------------------------------------------------------

describe('MekongEngine', () => {
  let engine: MekongEngine;

  beforeEach(() => {
    engine = new MekongEngine();
  });

  afterEach(async () => {
    if (engine.getStatus().initialized) {
      await engine.shutdown();
    }
  });

  it('creates instance with uninitialized status', () => {
    const status = engine.getStatus();
    expect(status.initialized).toBe(false);
    expect(status.providers).toEqual([]);
    expect(status.toolCount).toBe(0);
    expect(status.sessionId).toBeNull();
    expect(status.usage).toBeNull();
  });

  it('init() sets initialized to true and wires components', async () => {
    await engine.init();
    const status = engine.getStatus();
    expect(status.initialized).toBe(true);
  });

  it('init() registers builtin tools', async () => {
    await engine.init();
    expect(engine.getStatus().toolCount).toBeGreaterThan(0);
  });

  it('getStatus() returns sessionId after init', async () => {
    await engine.init();
    const status = engine.getStatus();
    expect(status.sessionId).toBeTruthy();
    expect(typeof status.sessionId).toBe('string');
  });

  it('shutdown() sets initialized to false', async () => {
    await engine.init();
    await engine.shutdown();
    expect(engine.getStatus().initialized).toBe(false);
  });

  it('run() throws MekongError when not initialized', async () => {
    await expect(engine.run('do something')).rejects.toThrow('not initialized');
  });

  it('runSop() throws MekongError when not initialized', async () => {
    await expect(engine.runSop('/nonexistent/file.yaml')).rejects.toThrow('not initialized');
  });

  it('init() with configOverrides merges correctly', async () => {
    await engine.init({ configOverrides: {} });
    expect(engine.getStatus().initialized).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Gateway
// ---------------------------------------------------------------------------

describe('Gateway', () => {
  let engine: MekongEngine;
  let gateway: Gateway;

  beforeEach(async () => {
    engine = new MekongEngine();
    await engine.init();
    gateway = new Gateway(engine);
  });

  afterEach(async () => {
    await engine.shutdown();
  });

  it('registers and dispatches a named route', async () => {
    gateway.route('ping', async (_args, _eng) => 'pong');
    const result = await gateway.dispatch('ping');
    expect(result).toBe('pong');
  });

  it('passes args to registered handler', async () => {
    gateway.route('echo', async (args) => args.join(' '));
    const result = await gateway.dispatch('echo', ['hello', 'world']);
    expect(result).toBe('hello world');
  });

  it('listRoutes() returns registered command names', () => {
    gateway.route('cmd1', async () => '');
    gateway.route('cmd2', async () => '');
    expect(gateway.listRoutes()).toContain('cmd1');
    expect(gateway.listRoutes()).toContain('cmd2');
  });

  it('has() returns true for registered route', () => {
    gateway.route('exists', async () => '');
    expect(gateway.has('exists')).toBe(true);
    expect(gateway.has('missing')).toBe(false);
  });

  it('dispatch unknown command falls back to engine.run()', async () => {
    const runSpy = vi.spyOn(engine, 'run').mockResolvedValue('engine result');
    const result = await gateway.dispatch('unknown', ['arg1']);
    expect(runSpy).toHaveBeenCalledWith('unknown arg1');
    expect(result).toBe('engine result');
  });
});

// ---------------------------------------------------------------------------
// Scheduler
// ---------------------------------------------------------------------------

describe('Scheduler', () => {
  let scheduler: Scheduler;

  beforeEach(() => {
    vi.useFakeTimers();
    scheduler = new Scheduler();
  });

  afterEach(() => {
    scheduler.cancelAll();
    vi.useRealTimers();
  });

  it('schedule() registers a task and size reflects count', () => {
    scheduler.schedule({ id: 't1', name: 'test', intervalMs: 1000, handler: async () => {} });
    expect(scheduler.size).toBe(1);
  });

  it('scheduled task fires after interval', async () => {
    const handler = vi.fn().mockResolvedValue(undefined);
    scheduler.schedule({ id: 'tick', name: 'ticker', intervalMs: 500, handler });

    await vi.advanceTimersByTimeAsync(500);
    expect(handler).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(500);
    expect(handler).toHaveBeenCalledTimes(2);
  });

  it('cancel() stops the task and returns true', () => {
    scheduler.schedule({ id: 'cancel-me', name: 'c', intervalMs: 1000, handler: async () => {} });
    const removed = scheduler.cancel('cancel-me');
    expect(removed).toBe(true);
    expect(scheduler.size).toBe(0);
  });

  it('cancel() returns false for unknown id', () => {
    expect(scheduler.cancel('nonexistent')).toBe(false);
  });

  it('cancelAll() clears all tasks', () => {
    scheduler.schedule({ id: 'a', name: 'a', intervalMs: 100, handler: async () => {} });
    scheduler.schedule({ id: 'b', name: 'b', intervalMs: 200, handler: async () => {} });
    scheduler.cancelAll();
    expect(scheduler.size).toBe(0);
  });

  it('list() returns active task definitions', () => {
    scheduler.schedule({ id: 'x', name: 'X', intervalMs: 1000, handler: async () => {} });
    const tasks = scheduler.list();
    expect(tasks).toHaveLength(1);
    expect(tasks[0].id).toBe('x');
  });

  it('re-scheduling existing id replaces previous timer', async () => {
    const handler1 = vi.fn().mockResolvedValue(undefined);
    const handler2 = vi.fn().mockResolvedValue(undefined);

    scheduler.schedule({ id: 'dup', name: 'd', intervalMs: 1000, handler: handler1 });
    scheduler.schedule({ id: 'dup', name: 'd', intervalMs: 1000, handler: handler2 });

    await vi.advanceTimersByTimeAsync(1000);
    expect(handler1).not.toHaveBeenCalled();
    expect(handler2).toHaveBeenCalledTimes(1);
    expect(scheduler.size).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// CLI output helpers (smoke tests — just verify no throw)
// ---------------------------------------------------------------------------

describe('CLI output helpers', () => {
  it('all output functions execute without throwing', () => {
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => heading('Title')).not.toThrow();
    expect(() => success('done')).not.toThrow();
    expect(() => error('oops')).not.toThrow();
    expect(() => warn('careful')).not.toThrow();
    expect(() => info('note')).not.toThrow();
    expect(() => keyValue('key', 'val')).not.toThrow();
    expect(() => divider()).not.toThrow();

    logSpy.mockRestore();
    errSpy.mockRestore();
  });
});
