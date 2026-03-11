import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { EventEmitter } from 'events';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const cp = require('child_process');
const fs = require('fs');

// Mock local modules (these work fine with vi.mock)
vi.mock('../lib/brain-process-manager', () => ({
    log: vi.fn(),
    default: { log: vi.fn() }
}));

vi.mock('../config', () => ({
    MEKONG_DIR: '/mock/mekong',
    HOME: '/mock/home',
    TOM_HUM_LOG: '/dev/null',
    WATCH_DIR: '/mock/mekong/tasks',
    PROCESSED_DIR: '/mock/mekong/tasks/processed',
    default: {
        MEKONG_DIR: '/mock/mekong'
    }
}));

describe('post-mission-gate.js', () => {
    let runBuildGate, runPostMissionGate;
    let spawnSpy, execSyncSpy, existsSyncSpy, writeFileSyncSpy;

    beforeEach(async () => {
        vi.resetModules();
        vi.restoreAllMocks(); // Restore spies to original state

        // Setup Spies on Node built-ins
        spawnSpy = vi.spyOn(cp, 'spawn').mockImplementation(() => {
            const child = new EventEmitter();
            child.stdout = new EventEmitter();
            child.stderr = new EventEmitter();
            child.kill = vi.fn();
            process.nextTick(() => {
                child.emit('close', 0);
            });
            return child;
        });

        execSyncSpy = vi.spyOn(cp, 'execSync').mockReturnValue('');

        existsSyncSpy = vi.spyOn(fs, 'existsSync').mockReturnValue(true);
        writeFileSyncSpy = vi.spyOn(fs, 'writeFileSync').mockImplementation(() => {});

        // Dynamic import of SUT
        const mod = await import('../lib/post-mission-gate');
        runBuildGate = mod.runBuildGate;
        runPostMissionGate = mod.runPostMissionGate;
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe('runBuildGate', () => {
        it('should return error if project directory does not exist', () => {
            existsSyncSpy.mockImplementation((p) => {
                return !String(p).includes('non-existent');
            });

            const result = runBuildGate('non-existent');
            expect(result.pass).toBe(false);
            expect(result.error).toBe('Project dir not found');
        });

        it('should return pass if build succeeds', () => {
            const result = runBuildGate('project');
            expect(result.pass).toBe(true);
            expect(execSyncSpy).toHaveBeenCalledWith('npm run build', expect.anything());
        });

        it('should fail if build command fails', () => {
            execSyncSpy.mockImplementation((cmd) => {
                if (cmd.includes('npm run build')) {
                    throw new Error('Build Error');
                }
                return '';
            });

            const result = runBuildGate('project');
            expect(result.pass).toBe(false);
            expect(result.error).toBe('Build Error');
        });
    });

    describe('runPostMissionGate', () => {
        it('should return GREEN result if build passes', async () => {
            // Setup successful spawn
            spawnSpy.mockImplementation(() => {
                const child = new EventEmitter();
                child.stdout = new EventEmitter();
                child.stderr = new EventEmitter();
                child.kill = vi.fn();
                process.nextTick(() => {
                    if (child.stdout) child.stdout.emit('data', 'Build OK');
                    child.emit('close', 0);
                });
                return child;
            });

            const result = await runPostMissionGate('/mock/project', 'mission-1');

            expect(result.build).toBe(true);
            // Verify git commit was called
            expect(execSyncSpy).toHaveBeenCalledWith(expect.stringContaining('git add'), expect.anything());
            expect(execSyncSpy).toHaveBeenCalledWith(expect.stringContaining('git commit'), expect.anything());
        });

        it('should return error output and create fix mission if build fails', async () => {
            // Setup failing spawn
            spawnSpy.mockImplementation(() => {
                const child = new EventEmitter();
                child.stdout = new EventEmitter();
                child.stderr = new EventEmitter();
                child.kill = vi.fn();
                process.nextTick(() => {
                    if (child.stdout) child.stdout.emit('data', 'Build Output');
                    if (child.stderr) child.stderr.emit('data', 'Critical Error');
                    child.emit('close', 1);
                });
                return child;
            });

            const result = await runPostMissionGate('/mock/project', 'mission-1');

            expect(result.build).toBe(false);
            expect(writeFileSyncSpy).toHaveBeenCalledWith(
                expect.stringContaining('HIGH_mission_fix_mission-1.txt'),
                expect.stringContaining('Critical Error')
            );
        });
    });
});
