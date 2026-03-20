import { describe, it, expect, vi } from 'vitest';
import cp from 'child_process';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

describe('Probe', () => {
  it('spyOn works with require destructuring', () => {
    const spy = vi.spyOn(cp, 'spawn').mockImplementation(() => ({
      stdout: { on: vi.fn() },
      stderr: { on: vi.fn() },
      on: vi.fn(),
      kill: vi.fn()
    }));

    // Simulate SUT behavior
    const { spawn } = require('child_process');
    spawn('ls', [], {});

    expect(spy).toHaveBeenCalled();
    expect(vi.isMockFunction(spawn)).toBe(true);
  });
});
