
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'events';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

// Mock internal dependencies
// We use vi.mock for non-built-ins as Vitest handles them reasonably well
vi.mock('../config', () => ({
  default: {
    MEKONG_DIR: '/mock/mekong',
    WATCH_DIR: '/mock/mekong/tasks',
    OPENCLAW_HOME: '/mock/home/.openclaw',
  },
  MEKONG_DIR: '/mock/mekong',
  WATCH_DIR: '/mock/mekong/tasks',
  OPENCLAW_HOME: '/mock/home/.openclaw',
}));

vi.mock('../lib/brain-process-manager', () => ({
  log: vi.fn(),
  default: { log: vi.fn() }
}));

describe('AGI Level 3 Tests', () => {
  let sut;
  let cpMock;
  let fsMock;
  let Module;
  let originalRequire;

  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();

    // Define fresh mocks for each test
    cpMock = {
      spawn: vi.fn(),
      execSync: vi.fn(),
    };

    fsMock = {
      writeFileSync: vi.fn(),
      existsSync: vi.fn(),
      readFileSync: vi.fn(),
    };

    // INTERCEPT REQUIRE:
    // The SUT is a CommonJS module that calls require('child_process') directly.
    // Vitest's ESM-based mocking sometimes struggles to intercept these built-in calls
    // when running in certain environments. We manually intercept Module.prototype.require
    // to ensure our mocks are returned.
    Module = require('module');
    originalRequire = Module.prototype.require;

    Module.prototype.require = function(id) {
        if (id === 'child_process') {
            return cpMock;
        }
        if (id === 'fs') {
            return fsMock;
        }
        return originalRequire.apply(this, arguments);
    };

    // Setup default behavior
    cpMock.spawn.mockImplementation(() => {
        const child = new EventEmitter();
        child.stdout = new EventEmitter();
        child.stderr = new EventEmitter();
        child.kill = vi.fn();
        process.nextTick(() => {
            child.emit('close', 0);
        });
        return child;
    });

    cpMock.execSync.mockReturnValue('');
    fsMock.existsSync.mockReturnValue(true);

    // Load SUT — bust cache for both shim and actual engine module
    for (const key of Object.keys(require.cache)) {
      if (key.includes('post-mission-gate')) delete require.cache[key];
    }
    sut = require('../lib/post-mission-gate');
  });

  afterEach(() => {
    // Restore original require to prevent leaking into other tests
    if (Module && originalRequire) {
        Module.prototype.require = originalRequire;
    }
    vi.clearAllMocks();
  });

  it('should pass gate when build succeeds', async () => {
    // Setup for success
    cpMock.execSync.mockReturnValue('Build successful');

    // Run SUT
    const result = await sut.runPostMissionGate('/project/path', 'mission-123');

    // Verify
    expect(result.build).toBe(true);

    // Verify build command
    expect(cpMock.spawn).toHaveBeenCalledWith('npm', ['run', 'build'], expect.anything());

    // Verify git commands
    expect(cpMock.execSync).toHaveBeenCalledWith(expect.stringContaining('git add'), expect.anything());
    expect(cpMock.execSync).toHaveBeenCalledWith(expect.stringContaining('git commit'), expect.anything());
  });

  it('should fail gate and create fix mission when build fails', async () => {
    // Setup for failure (spawn returns non-zero exit code)
    cpMock.spawn.mockImplementation(() => {
        const child = new EventEmitter();
        child.stdout = new EventEmitter();
        child.stderr = new EventEmitter();
        child.kill = vi.fn();
        process.nextTick(() => {
            child.stdout.emit('data', 'Error: syntax error');
            child.emit('close', 1);
        });
        return child;
    });

    // Run SUT
    const result = await sut.runPostMissionGate('/project/path', 'mission-123');

    // Verify failure
    expect(result.build).toBe(false);

    // Verify fix mission creation
    expect(fsMock.writeFileSync).toHaveBeenCalledWith(
      expect.stringContaining('HIGH_mission_fix_mission-123.txt'),
      expect.stringContaining('MISSION: Fix build failure')
    );
  });
});
