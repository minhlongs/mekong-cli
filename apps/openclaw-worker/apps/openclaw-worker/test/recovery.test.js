import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'events';
import * as cp from 'child_process';
import * as fs from 'fs';

// Mock config to point to /dev/null and set defaults
vi.mock('../config', () => ({
  default: {
    MODEL_NAME: 'gemini-3-flash-preview',
    LOG_FILE: '/dev/null',
    PROXY_PORT: 11436,
    ENGINE: 'antigravity'
  },
  MODEL_NAME: 'gemini-3-flash-preview',
  LOG_FILE: '/dev/null',
  PROXY_PORT: 11436,
  ENGINE: 'antigravity'
}));

// We can spy on fs functions too
// Note: In some environments, spying on fs exports directly might be read-only.
// If that fails, we'll revert to vi.mock('fs').
// But let's try to mock fs using vi.mock as it was working/not the primary issue.
vi.mock('fs', async (importOriginal) => {
    const actual = await importOriginal();
    return {
        ...actual,
        appendFileSync: vi.fn(),
        existsSync: vi.fn(() => true),
        default: {
            ...actual.default,
            appendFileSync: vi.fn(),
            existsSync: vi.fn(() => true),
        }
    };
});

describe('Brain Headless Recovery (Fresh CC CLI Instance)', () => {
  let brainHeadless;
  let spawnSpy;

  beforeEach(async () => {
    vi.resetModules(); // Ensure SUT is re-loaded

    // Spy on child_process.spawn
    // This modifies the exported object of the built-in module
    spawnSpy = vi.spyOn(cp, 'spawn').mockImplementation((cmd, args, opts) => {
        const child = new EventEmitter();
        child.stdout = new EventEmitter();
        child.stderr = new EventEmitter();
        child.kill = vi.fn();
        // Default behavior: do nothing, just return child
        return child;
    });

    // Load the SUT
    // Since we resetModules, this triggers a fresh require('child_process')
    // causing it to grab the spied 'spawn' from the module exports.
    brainHeadless = (await import('../lib/brain-headless-per-mission.js')).default;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should retry with fallback model on HTTP 400 error', async () => {
    let callCount = 0;

    spawnSpy.mockImplementation((cmd, args, opts) => {
      callCount++;
      const child = new EventEmitter();
      child.stdout = new EventEmitter();
      child.stderr = new EventEmitter();
      child.kill = vi.fn();

      setTimeout(() => {
        if (callCount === 1) {
          // First attempt: Fail with 400
          child.stderr.emit('data', 'Error: Request failed with status code 400');
          child.emit('close', 1);
        } else {
          // Second attempt: Success
          child.stdout.emit('data', 'Mission accomplished');
          child.emit('close', 0);
        }
      }, 10);

      return child;
    });

    const result = await brainHeadless.runMission('Test prompt', '/tmp', 1000);

    expect(spawnSpy).toHaveBeenCalledTimes(2);
    expect(result.success).toBe(true);

    const calls = spawnSpy.mock.calls;
    expect(calls.length).toBe(2);
    // First call uses default model
    expect(calls[0][1]).toContain('gemini-3-flash-preview');

    // Second call uses fallback model
    const secondArgs = calls[1][1];
    const modelIndex = secondArgs.indexOf('--model');
    expect(secondArgs[modelIndex + 1]).toBe('claude-sonnet-4-20250514');
  });

  it('should retry with truncated prompt on context overflow', async () => {
    let callCount = 0;
    const longPrompt = 'A'.repeat(10000);

    spawnSpy.mockImplementation((cmd, args, opts) => {
      callCount++;
      const child = new EventEmitter();
      child.stdout = new EventEmitter();
      child.stderr = new EventEmitter();
      child.kill = vi.fn();

      setTimeout(() => {
        if (callCount === 1) {
          // First attempt: Context overflow
          child.stderr.emit('data', 'Error: prompt is too long. context overflow.');
          child.emit('close', 1);
        } else {
          // Second attempt: Success
          child.stdout.emit('data', 'Truncated mission success');
          child.emit('close', 0);
        }
      }, 10);

      return child;
    });

    const result = await brainHeadless.runMission(longPrompt, '/tmp', 1000);

    expect(spawnSpy).toHaveBeenCalledTimes(2);
    expect(result.success).toBe(true);

    const calls = spawnSpy.mock.calls;
    const sentPrompt = calls[1][1][1]; // -p <prompt>
    expect(sentPrompt.length).toBeLessThan(longPrompt.length);
    expect(sentPrompt).toContain('[TRUNCATED');
  });

  it('should NOT retry on unrecoverable error', async () => {
    spawnSpy.mockImplementation((cmd, args, opts) => {
      const child = new EventEmitter();
      child.stdout = new EventEmitter();
      child.stderr = new EventEmitter();
      child.kill = vi.fn();

      setTimeout(() => {
        child.stderr.emit('data', 'SyntaxError: Unexpected token');
        child.emit('close', 1);
      }, 10);

      return child;
    });

    const result = await brainHeadless.runMission('Test prompt', '/tmp', 1000);

    expect(spawnSpy).toHaveBeenCalledTimes(1);
    expect(result.success).toBe(false);
    expect(result.result).toBe('exit_1');
  });
});
