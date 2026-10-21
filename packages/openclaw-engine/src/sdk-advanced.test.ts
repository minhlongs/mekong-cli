/**
 * Unit tests for OpenClawEngine SDK facade — Mission Submission, Health & Circuit Breaker
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { OpenClawEngine } from './sdk.js';
import type { MissionConfig, EngineHealth } from './sdk.js';

describe('OpenClawEngine — submitMission, getHealth & circuit breaker', () => {
  let engine: OpenClawEngine;

  beforeEach(() => {
    engine = new OpenClawEngine();
  });

  describe('submitMission', () => {
    it('completes a trivial mission with 1 credit', async () => {
      const result = await engine.submitMission({ goal: 'fix typo', complexity: 'trivial' });
      expect(result.status).toBe('completed');
      expect(result.creditsUsed).toBe(1);
    });

    it('completes a standard mission with 3 credits', async () => {
      const result = await engine.submitMission({ goal: 'add feature', complexity: 'standard' });
      expect(result.status).toBe('completed');
      expect(result.creditsUsed).toBe(3);
    });

    it('completes a complex mission with 10 credits', async () => {
      const result = await engine.submitMission({ goal: 'refactor system', complexity: 'complex' });
      expect(result.status).toBe('completed');
      expect(result.creditsUsed).toBe(10);
    });

    it('completes an epic mission with 25 credits', async () => {
      const result = await engine.submitMission({ goal: 'rebuild everything', complexity: 'epic' });
      expect(result.status).toBe('completed');
      expect(result.creditsUsed).toBe(25);
    });

    it('returns id prefixed with m_', async () => {
      const result = await engine.submitMission({ goal: 'task', complexity: 'trivial' });
      expect(result.id).toMatch(/^m_/);
    });

    it('returns id matching m_<base36>_<base36> pattern', async () => {
      const result = await engine.submitMission({ goal: 'task', complexity: 'trivial' });
      expect(result.id).toMatch(/^m_[a-z0-9]+_[a-z0-9]+$/);
    });

    it('generates unique ids across consecutive missions', async () => {
      const r1 = await engine.submitMission({ goal: 'task 1', complexity: 'trivial' });
      const r2 = await engine.submitMission({ goal: 'task 2', complexity: 'trivial' });
      expect(r1.id).not.toBe(r2.id);
    });

    it('includes durationMs >= 0', async () => {
      const result = await engine.submitMission({ goal: 'task', complexity: 'trivial' });
      expect(result.durationMs).toBeGreaterThanOrEqual(0);
    });

    it('output contains the submitted goal text', async () => {
      const result = await engine.submitMission({ goal: 'my special task', complexity: 'trivial' });
      expect(result.output).toContain('my special task');
    });

    it('tracks missionsCompleted after each call', async () => {
      await engine.submitMission({ goal: 'task a', complexity: 'trivial' });
      await engine.submitMission({ goal: 'task b', complexity: 'standard' });
      expect(engine.getHealth().missionsCompleted).toBe(2);
    });

    it('accepts optional maxRetries field without error', async () => {
      const config: MissionConfig = { goal: 'test', complexity: 'standard', maxRetries: 3 };
      const result = await engine.submitMission(config);
      expect(result.status).toBe('completed');
    });

    it('accepts optional timeoutMs field without error', async () => {
      const config: MissionConfig = { goal: 'test', complexity: 'standard', timeoutMs: 60_000 };
      const result = await engine.submitMission(config);
      expect(result.status).toBe('completed');
    });

    it('accepts all optional fields together', async () => {
      const config: MissionConfig = {
        goal: 'full config test',
        complexity: 'complex',
        maxRetries: 5,
        timeoutMs: 120_000,
      };
      const result = await engine.submitMission(config);
      expect(result.status).toBe('completed');
    });

    it('processes all four complexity levels without error', async () => {
      const levels: MissionConfig['complexity'][] = ['trivial', 'standard', 'complex', 'epic'];
      for (const complexity of levels) {
        const result = await engine.submitMission({ goal: 'test', complexity });
        expect(result.status).toBe('completed');
      }
    });
  });

  describe('getHealth', () => {
    it('returns all required EngineHealth fields', () => {
      const health: EngineHealth = engine.getHealth();
      expect(health).toHaveProperty('uptime');
      expect(health).toHaveProperty('missionsCompleted');
      expect(health).toHaveProperty('missionsFailed');
      expect(health).toHaveProperty('agiScore');
      expect(health).toHaveProperty('circuitBreakerState');
    });

    it('returns zero missionsFailed initially', () => {
      expect(engine.getHealth().missionsFailed).toBe(0);
    });

    it('returns agiScore of 100 after one successful mission', async () => {
      await engine.submitMission({ goal: 'task', complexity: 'trivial' });
      expect(engine.getHealth().agiScore).toBe(100);
    });

    it('uptime increases over time', async () => {
      const h1 = engine.getHealth();
      await new Promise(r => setTimeout(r, 15));
      const h2 = engine.getHealth();
      expect(h2.uptime).toBeGreaterThan(h1.uptime);
    });

    it('agiScore stays 100 after multiple successful missions', async () => {
      await engine.submitMission({ goal: 'a', complexity: 'trivial' });
      await engine.submitMission({ goal: 'b', complexity: 'standard' });
      await engine.submitMission({ goal: 'c', complexity: 'complex' });
      expect(engine.getHealth().agiScore).toBe(100);
    });
  });

  describe('circuit breaker', () => {
    it('starts in closed state', () => {
      expect(engine.getHealth().circuitBreakerState).toBe('closed');
    });

    it('stays closed after many successful missions', async () => {
      for (let i = 0; i < 10; i++) {
        await engine.submitMission({ goal: `task ${i}`, complexity: 'trivial' });
      }
      expect(engine.getHealth().circuitBreakerState).toBe('closed');
    });

    it('respects enableCircuitBreaker=false config — always allows missions', async () => {
      const noBreaker = new OpenClawEngine({ enableCircuitBreaker: false });
      for (let i = 0; i < 5; i++) {
        await noBreaker.submitMission({ goal: `task ${i}`, complexity: 'trivial' });
      }
      expect(noBreaker.getHealth().circuitBreakerState).toBe('closed');
    });
  });
});
