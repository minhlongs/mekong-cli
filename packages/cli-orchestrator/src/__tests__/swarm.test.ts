import { describe, it, expect, beforeEach } from 'vitest';
import { CliSwarm } from '../swarm.js';
import type { SwarmTask } from '../swarm.js';

describe('CliSwarm', () => {
  let swarm: CliSwarm;

  beforeEach(() => {
    swarm = new CliSwarm();
    swarm.addProvider('claude', 10);
    swarm.addProvider('gemini', 8);
    swarm.addProvider('qwen', 6);
  });

  describe('routeTask', () => {
    it('routes code tasks to claude', () => {
      const task: SwarmTask = { id: '1', type: 'code', prompt: 'write a fn', priority: 1 };
      expect(swarm.routeTask(task)).toBe('claude');
    });

    it('routes research tasks to gemini', () => {
      const task: SwarmTask = { id: '2', type: 'research', prompt: 'find info', priority: 1 };
      expect(swarm.routeTask(task)).toBe('gemini');
    });

    it('routes quick tasks to qwen', () => {
      const task: SwarmTask = { id: '3', type: 'quick', prompt: 'summarize', priority: 1 };
      expect(swarm.routeTask(task)).toBe('qwen');
    });

    it('falls back to highest priority when preferred not registered', () => {
      const freshSwarm = new CliSwarm();
      freshSwarm.addProvider('gemini', 5);
      freshSwarm.addProvider('qwen', 9);
      const task: SwarmTask = { id: '4', type: 'code', prompt: 'fix bug', priority: 1 };
      // claude not registered — fallback to highest priority = qwen (9)
      expect(freshSwarm.routeTask(task)).toBe('qwen');
    });

    it('throws when no providers registered', () => {
      const empty = new CliSwarm();
      const task: SwarmTask = { id: '5', type: 'quick', prompt: 'x', priority: 1 };
      expect(() => empty.routeTask(task)).toThrow('No providers registered');
    });
  });

  describe('executeParallel', () => {
    it('returns one result per task', async () => {
      const tasks: SwarmTask[] = [
        { id: 't1', type: 'code', prompt: 'a', priority: 1 },
        { id: 't2', type: 'research', prompt: 'b', priority: 2 },
      ];
      const results = await swarm.executeParallel(tasks);
      expect(results).toHaveLength(2);
      expect(results[0]?.taskId).toBe('t1');
      expect(results[1]?.taskId).toBe('t2');
    });

    it('marks all results as successful', async () => {
      const tasks: SwarmTask[] = [{ id: 'x', type: 'quick', prompt: 'hi', priority: 1 }];
      const [result] = await swarm.executeParallel(tasks);
      expect(result?.success).toBe(true);
    });
  });

  describe('crossVerify', () => {
    it('returns zero confidence for empty results', () => {
      const task: SwarmTask = { id: 'v1', type: 'review', prompt: 'check', priority: 1 };
      const cv = swarm.crossVerify(task, []);
      expect(cv.confidence).toBe(0);
      expect(cv.consensus).toBe('');
    });

    it('returns full confidence when all agree', () => {
      const task: SwarmTask = { id: 'v2', type: 'review', prompt: 'check', priority: 1 };
      const results = [
        { taskId: 'v2', provider: 'claude', output: 'same', durationMs: 10, success: true },
        { taskId: 'v2', provider: 'gemini', output: 'same', durationMs: 12, success: true },
      ];
      const cv = swarm.crossVerify(task, results);
      expect(cv.confidence).toBe(1);
      expect(cv.consensus).toBe('same');
    });

    it('picks majority output', () => {
      const task: SwarmTask = { id: 'v3', type: 'review', prompt: 'check', priority: 1 };
      const results = [
        { taskId: 'v3', provider: 'claude', output: 'A', durationMs: 5, success: true },
        { taskId: 'v3', provider: 'gemini', output: 'A', durationMs: 6, success: true },
        { taskId: 'v3', provider: 'qwen', output: 'B', durationMs: 4, success: true },
      ];
      const cv = swarm.crossVerify(task, results);
      expect(cv.consensus).toBe('A');
      expect(cv.confidence).toBeCloseTo(2 / 3);
    });
  });

  describe('getLoadBalance', () => {
    it('returns entry for each registered provider', () => {
      const loads = swarm.getLoadBalance();
      const names = loads.map((l) => l.provider);
      expect(names).toContain('claude');
      expect(names).toContain('gemini');
      expect(names).toContain('qwen');
    });

    it('increments totalCompleted after execution', async () => {
      await swarm.executeParallel([{ id: 'lb1', type: 'code', prompt: 'x', priority: 1 }]);
      const loads = swarm.getLoadBalance();
      const claude = loads.find((l) => l.provider === 'claude');
      expect(claude?.totalCompleted).toBe(1);
    });
  });
});
