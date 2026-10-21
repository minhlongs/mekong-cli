/**
 * Unit tests for OpenClawEngine SDK facade — Constructor & Complexity Classification
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { OpenClawEngine } from './sdk.js';
import type { EngineConfig } from './sdk.js';

describe('OpenClawEngine — constructor & classifyComplexity', () => {
  let engine: OpenClawEngine;

  beforeEach(() => {
    engine = new OpenClawEngine();
  });

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
      expect(custom.getHealth().missionsCompleted).toBe(0);
    });

    it('tracks uptime from creation', async () => {
      await new Promise(r => setTimeout(r, 10));
      expect(engine.getHealth().uptime).toBeGreaterThan(0);
    });
  });

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
      expect(
        engine.classifyComplexity('add a dark mode toggle button to the navigation bar'),
      ).toBe('standard');
    });

    it('returns standard for moderate-length goal without multi-step keywords', () => {
      expect(
        engine.classifyComplexity('implement user authentication with JWT tokens for the backend API server'),
      ).toBe('standard');
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
      const thirtyWordGoal =
        'create a comprehensive dashboard with real-time data visualization including charts graphs tables filters sorting pagination export functionality user preferences saved views custom themes responsive layout dark mode accessibility compliance internationalization';
      expect(engine.classifyComplexity(thirtyWordGoal)).toBe('standard');
    });

    it('returns complex for goal with word count > 30 and no multi-step keywords', () => {
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
});
