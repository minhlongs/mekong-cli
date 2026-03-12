import { describe, it, expect } from 'vitest';
import { ok, err, MekongError } from '../../src/types/common.js';
import { ConfigSchema } from '../../src/types/config.js';
import { SopDefinitionSchema } from '../../src/types/sop.js';

describe('Result type', () => {
  it('ok wraps value', () => {
    const result = ok(42);
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value).toBe(42);
  });

  it('err wraps error', () => {
    const result = err(new Error('fail'));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toBe('fail');
  });
});

describe('MekongError', () => {
  it('has code and recoverable fields', () => {
    const e = new MekongError('test', 'TEST_ERR', false, { key: 'val' });
    expect(e.message).toBe('test');
    expect(e.code).toBe('TEST_ERR');
    expect(e.recoverable).toBe(false);
    expect(e.context).toEqual({ key: 'val' });
    expect(e.name).toBe('MekongError');
  });
});

describe('ConfigSchema', () => {
  it('parses empty object with defaults', () => {
    const config = ConfigSchema.parse({});
    expect(config.version).toBe('1');
    expect(config.llm.default_provider).toBe('anthropic');
    expect(config.agents.max_iterations).toBe(10);
    expect(config.budget.max_cost_per_task).toBe(1.0);
    expect(config.tools.auto_approve_level).toBe('1');
  });

  it('accepts full config', () => {
    const config = ConfigSchema.parse({
      version: '2',
      llm: {
        default_provider: 'openai',
        default_model: 'gpt-4o',
        providers: {
          openai: { api_key_env: 'OPENAI_API_KEY' },
        },
      },
    });
    expect(config.llm.default_provider).toBe('openai');
    expect(config.llm.providers.openai.api_key_env).toBe('OPENAI_API_KEY');
  });
});

describe('SopDefinitionSchema', () => {
  it('validates minimal SOP', () => {
    const sop = SopDefinitionSchema.parse({
      sop: {
        name: 'Test SOP',
        steps: [
          { id: 'step1', name: 'Step 1', action: 'shell', command: 'echo hello' },
        ],
      },
    });
    expect(sop.sop.name).toBe('Test SOP');
    expect(sop.sop.steps).toHaveLength(1);
    expect(sop.sop.version).toBe('1.0.0');
  });
});
