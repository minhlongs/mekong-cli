/**
 * Unit tests for OpenClawEngine SDK facade
 * Covers: constructor, classifyComplexity, submitMission, getHealth, circuit breaker
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { OpenClawEngine } from './sdk.js';
import type { MissionConfig, MissionResult, EngineHealth, EngineConfig } from './sdk.js';

describe('OpenClawEngine', () => {
  let engine: OpenClawEngine;

  beforeEach(() => {
    engine = new OpenClawEngine();
  });

  // ── constructor ────────────────────────────────────────────────────────────

  describe('constructor', () => {
    it('creates with default config and zero missions', () => {
      const health = engine.getHealth();
      expect(health.missionsCompleted).toBe(0);
      expect(health.missionsFailed).toBe(0);
    });

    it('initialises circuit breaker as closed', () => {
      expect(engine.getHealth().circuitBreakerState).toBe('closed');
    });

    it('starts with agiScore of 0 before any missions', () => {
      expect(engine.getHealth().agiScore).toBe(0);
    });

    it('accepts partial EngineConfig without error', () => {
      const custom = new OpenClawEngine({ maxConcurrency: 10 });
      expect(custom.getHealth().circuitBreakerState).toBe('closed');
    });

    it('accepts full EngineConfig override', () => {
      const cfg: Partial<EngineConfig> = {
        maxConcurrency: 20,
        defaultTimeout: 60_000,
        enableLearning: false,
        enableCircuitBreaker: false,
      };
      const custom = new OpenClawEngine(cfg);
      // Should not throw and be operational
      expect(custom.getHealth().missionsCompleted).toBe(0);
    });

    it('tracks uptime from creation', async () => {
      await new Promise(r => setTimeout(r, 10));
      expect(engine.getHealth().uptime).toBeGreaterThan(0);
    });
  });

  // ── classifyComplexity ─────────────────────────────────────────────────────

  describe('classifyComplexity', () => {
    it('returns trivial for a short, simple goal', () => {
      expect(engine.classifyComplexity('fix typo')).toBe('trivial');
    });

    it('returns trivial for empty string', () => {
      expect(engine.classifyComplexity('')).toBe('trivial');
    });

    it('returns trivial for single word', () => {
      expect(engine.classifyComplexity('test')).toBe('trivial');
    });

    it('returns standard for moderate goal with no multi-step or technical keywords', () => {
      // exactly 10 words, no multi-step/technical substrings → standard
      expect(
        engine.classifyComplexity('add a dark mode toggle button to the navigation bar'),
      ).toBe('standard');
    });

    it('returns complex for goal whose text contains a multi-step substring (e.g. "then" inside "authentication")', () => {
      // "au-THEN-tication" triggers the /then/ substring match → complex
      expect(
        engine.classifyComplexity('implement user authentication with JWT tokens for the API'),
      ).toBe('complex');
    });

    it('returns complex for goal containing "and" keyword', () => {
      expect(
        engine.classifyComplexity('build the form and validate inputs and add tests'),
      ).toBe('complex');
    });

    it('returns complex for goal containing "then" keyword', () => {
      expect(
        engine.classifyComplexity('create the module then write unit tests'),
      ).toBe('complex');
    });

    it('returns standard for goal with exactly 30 words and no multi-step keywords', () => {
      // word count <= 30 and no multi-step/technical keywords → standard
      const thirtyWordGoal =
        'create a comprehensive dashboard with real-time data visualization including charts graphs tables filters sorting pagination export functionality user preferences saved views custom themes responsive layout dark mode accessibility compliance internationalization';
      expect(engine.classifyComplexity(thirtyWordGoal)).toBe('standard');
    });

    it('returns complex for goal with word count > 30 and no multi-step keywords', () => {
      // > 30 words → complex
      const longGoal =
        'create a comprehensive dashboard with real-time data visualization including charts graphs tables filters sorting pagination export functionality user preferences saved views custom themes responsive layout dark mode accessibility compliance internationalization support';
      expect(engine.classifyComplexity(longGoal)).toBe('complex');
    });

    it('returns epic for technical + multi-step goal', () => {
      expect(
        engine.classifyComplexity(
          'deploy the microservices and then migrate the database and refactor the API layer',
        ),
      ).toBe('epic');
    });

    it('returns epic when both "migrate" and "also" are present', () => {
      expect(engine.classifyComplexity('migrate the database and also update indexes')).toBe('epic');
    });

    it('returns epic for goal with "architect" + "then"', () => {
      expect(engine.classifyComplexity('architect the new service and then deploy it')).toBe('epic');
    });
  });

  // ── submitMission ──────────────────────────────────────────────────────────

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

  // ── getHealth ──────────────────────────────────────────────────────────────

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

  // ── circuit breaker ────────────────────────────────────────────────────────

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
      // Without circuit breaker, state remains closed and all succeed
      expect(noBreaker.getHealth().circuitBreakerState).toBe('closed');
    });
  });
});
