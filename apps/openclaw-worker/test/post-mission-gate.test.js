/**
 * post-mission-gate.js — Unit tests
 * Tests the build gate and post-mission verification system.
 *
 * Note: Module was moved to packages/openclaw-engine/src/intelligence/.
 * Tests use proxyquire-style dynamic require to inject mocks into CJS module.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import path from 'path';
import Module from 'module';

// Direct path to the actual module (not the shim)
const MODULE_PATH = path.resolve(__dirname, '../../../packages/openclaw-engine/src/intelligence/post-mission-gate.js');

describe('post-mission-gate.js', () => {
    let runBuildGate, runPostMissionGate;
    let mockExecSync, mockExistsSync, mockWriteFileSync;

    beforeEach(() => {
        vi.resetModules();

        // Clear require cache for the module and its deps
        for (const key of Object.keys(require.cache)) {
            if (key.includes('post-mission-gate') || key.includes('brain-process-manager') || key.includes('_bridge/config')) {
                delete require.cache[key];
            }
        }

        // Setup mocks on the real modules before require
        mockExecSync = vi.fn().mockReturnValue('Build OK');
        mockExistsSync = vi.fn().mockReturnValue(true);
        mockWriteFileSync = vi.fn();

        // Patch child_process (both execSync and spawn used by spawnAsync)
        const cp = require('child_process');
        cp.execSync = mockExecSync;
        cp.spawn = vi.fn().mockImplementation(() => {
            const { EventEmitter } = require('events');
            const child = new EventEmitter();
            child.stdout = new EventEmitter();
            child.stderr = new EventEmitter();
            child.kill = vi.fn();
            process.nextTick(() => {
                child.stdout.emit('data', 'Build complete');
                child.emit('close', 0);
            });
            return child;
        });

        // Patch fs
        const fs = require('fs');
        fs.existsSync = mockExistsSync;
        fs.writeFileSync = mockWriteFileSync;

        // Load module fresh
        const mod = require(MODULE_PATH);
        runBuildGate = mod.runBuildGate;
        runPostMissionGate = mod.runPostMissionGate;
    });

    describe('runBuildGate', () => {
        it('should return error if project directory does not exist', () => {
            mockExistsSync.mockReturnValue(false);

            const result = runBuildGate('/non-existent');
            expect(result.pass).toBe(false);
            expect(result.error).toBe('Project dir not found');
        });

        it('should return pass if build succeeds', () => {
            const result = runBuildGate('/mock/project');
            expect(result.pass).toBe(true);
            expect(mockExecSync).toHaveBeenCalledWith('npm run build', expect.anything());
        });

        it('should fail if build command fails', () => {
            mockExecSync.mockImplementation(() => {
                const err = new Error('Build failed');
                err.stdout = 'error TS2345';
                err.stderr = '';
                throw err;
            });

            const result = runBuildGate('/mock/project');
            expect(result.pass).toBe(false);
            expect(result.error).toContain('Build failed');
        });
    });

    describe('runPostMissionGate', () => {
        it('should return GREEN result if build passes', async () => {
            const result = await runPostMissionGate('/mock/project', 'mission-1');
            expect(result.build).toBe(true);
        });

        it('should return error and create fix mission if build fails', async () => {
            // Must re-require module with failing spawn mock (CJS caches spawn at load time)
            for (const key of Object.keys(require.cache)) {
                if (key.includes('post-mission-gate')) delete require.cache[key];
            }
            const cp = require('child_process');
            cp.spawn = vi.fn().mockImplementation(() => {
                const { EventEmitter } = require('events');
                const child = new EventEmitter();
                child.stdout = new EventEmitter();
                child.stderr = new EventEmitter();
                child.kill = vi.fn();
                process.nextTick(() => {
                    child.stderr.emit('data', 'error TS2345: Argument of type X');
                    child.emit('close', 1);
                });
                return child;
            });
            const mod = require(MODULE_PATH);

            const result = await mod.runPostMissionGate('/mock/project', 'mission-1');
            expect(result.build).toBe(false);
            expect(mockWriteFileSync).toHaveBeenCalledWith(
                expect.stringContaining('HIGH_mission_fix_mission-1'),
                expect.any(String)
            );
        });
    });
});
