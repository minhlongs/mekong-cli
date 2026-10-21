/**
 * Tests for `mekong ship` command với --cloudflare-only integration.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Command } from 'commander';
import { mkdirSync, rmSync, existsSync, writeFileSync } from 'fs';
import { join } from 'path';

// Mock child_process.execSync
vi.mock('child_process', () => ({ execSync: vi.fn() }));

// Mock readline
vi.mock('readline', () => ({
  createInterface: vi.fn().mockReturnValue({
    question: vi.fn(),
    close: vi.fn(),
  }),
}));

// Mock PlatformDetector
const mockDetectPlatform = vi.fn();
vi.mock('../../src/core/platform-detector.js', () => ({
  PlatformDetector: class {
    detectPlatform = mockDetectPlatform;
  },
  DetectionResult: {},
}));

// Import module under test
import * as shipModule from '../../src/cli/commands/ship.js';
import { execSync } from 'child_process';

const mockedExecSync = vi.mocked(execSync);

interface ExecOpts {
  encoding?: string;
  stdio?: string;
}

function createProgram(): Command {
  const program = new Command();
  program.exitOverride();
  program.configureOutput({ writeOut: () => {}, writeErr: () => {} });
  return program;
}

describe('ship command', () => {
  let tempDir: string;
  let originalCwd: string;

  beforeEach(() => {
    vi.clearAllMocks();
    originalCwd = process.cwd();
    tempDir = join(originalCwd, '.test-temp', `ship-${Date.now()}`);
    mkdirSync(tempDir, { recursive: true });
    process.chdir(tempDir);

    // Setup git repo basics
    mockedExecSync.mockImplementation(((cmd: string, opts?: ExecOpts) => {
      const encoding = opts?.encoding || 'buffer';
      if (cmd === 'git init') return Buffer.from('');
      if (cmd.includes('git config')) return Buffer.from('');
      if (cmd === 'git rev-parse --is-inside-work-tree') return encoding === 'utf-8' ? 'true' : Buffer.from('true');
      if (cmd === 'git rev-parse --abbrev-ref HEAD') return encoding === 'utf-8' ? 'main' : Buffer.from('main');
      if (cmd === 'git diff --cached --name-only') return encoding === 'utf-8' ? '' : Buffer.from('');
      if (cmd === 'git diff --name-only') return encoding === 'utf-8' ? '' : Buffer.from('');
      if (cmd.startsWith('git reset HEAD')) return encoding === 'utf-8' ? '' : Buffer.from('');
      if (cmd.startsWith('git commit -m')) return encoding === 'utf-8' ? '' : Buffer.from('');
      if (cmd.startsWith('git push')) return encoding === 'utf-8' ? '' : Buffer.from('');
      return encoding === 'utf-8' ? '' : Buffer.from('');
    }) as unknown as typeof execSync);
  });

  afterEach(() => {
    process.chdir(originalCwd);
    if (existsSync(tempDir)) {
      rmSync(tempDir, { recursive: true, force: true });
    }
    vi.restoreAllMocks();
  });

  describe('registration', () => {
    it('should register ship command', () => {
      const program = createProgram();
      shipModule.registerShipCommand(program);
      expect(program.commands.find(c => c.name() === 'ship')).toBeDefined();
    });
  });

  describe('--cloudflare-only behavior', () => {
    beforeEach(() => {
      writeFileSync(join(tempDir, 'base.txt'), 'base');
      mockedExecSync('git add -A', { stdio: 'ignore' });
      mockedExecSync('git commit -m "init"', { stdio: 'ignore' });
    });

    it('should proceed with pure Cloudflare repo', async () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      writeFileSync(join(tempDir, 'worker.ts'), 'import { Worker } from "@cloudflare/workers"');
      mockedExecSync('git add -A', { stdio: 'ignore' });

      mockDetectPlatform.mockReturnValue({
        platform: 'cloudflare',
        confidence: 0.95,
        files: ['wrangler.toml', 'worker.ts'],
      });

      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);
      vi.spyOn(shipModule, 'verifyLive').mockResolvedValue(true);
      vi.spyOn(shipModule, 'updatePrDescription').mockResolvedValue(undefined);

      mockedExecSync.mockImplementation(((cmd: string, opts?: ExecOpts) => {
        const encoding = opts?.encoding || 'buffer';
        if (cmd === 'git diff --cached --name-only') {
          return encoding === 'utf-8' ? 'wrangler.toml\nworker.ts\n' : Buffer.from('wrangler.toml\nworker.ts\n');
        }
        if (cmd.startsWith('git commit -m') || cmd.startsWith('git push')) {
          return encoding === 'utf-8' ? '' : Buffer.from('');
        }
        return encoding === 'utf-8' ? '' : Buffer.from('');
      }) as unknown as typeof execSync);

      try {
        await program.parseAsync(['node', 'test', 'ship', 'msg', '--cloudflare-only', '--yes']);
      } catch {
        // commander may exit
      }

      expect(mockDetectPlatform).toHaveBeenCalled();
      expect(execSync).toHaveBeenCalledWith(expect.stringContaining('git commit -m'), expect.anything());
      expect(execSync).toHaveBeenCalledWith(expect.stringContaining('git push'), expect.anything());
    });

    it('should abort on non-Cloudflare repo', async () => {
      writeFileSync(join(tempDir, 'docker-compose.yml'), 'version: "3.8"');
      mockedExecSync('git add -A', { stdio: 'ignore' });

      mockDetectPlatform.mockReturnValue({
        platform: 'other',
        confidence: 0.1,
        files: [],
      });

      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);

      await expect(
        program.parseAsync(['node', 'test', 'ship', 'msg', '--cloudflare-only'])
      ).rejects.toThrow(/No Cloudflare projects detected/);
    });

    it('should handle mixed repo with --yes', async () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      writeFileSync(join(tempDir, 'docker-compose.yml'), 'version: "3.8"');
      mockedExecSync('git add -A', { stdio: 'ignore' });

      mockDetectPlatform.mockReturnValue({
        platform: 'mixed',
        confidence: 0.45,
        files: ['wrangler.toml'],
      });

      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);
      vi.spyOn(shipModule, 'verifyLive').mockResolvedValue(true);

      mockedExecSync.mockImplementation(((cmd: string, opts?: ExecOpts) => {
        const encoding = opts?.encoding || 'buffer';
        if (cmd === 'git diff --cached --name-only') {
          return encoding === 'utf-8' ? 'wrangler.toml\n' : Buffer.from('wrangler.toml\n');
        }
        if (cmd === 'git diff --name-only') {
          return encoding === 'utf-8' ? 'docker-compose.yml\n' : Buffer.from('docker-compose.yml\n');
        }
        if (cmd === 'git reset HEAD') {
          return encoding === 'utf-8' ? '' : Buffer.from('');
        }
        if (cmd.startsWith('git commit -m') || cmd.startsWith('git push')) {
          return encoding === 'utf-8' ? '' : Buffer.from('');
        }
        return encoding === 'utf-8' ? '' : Buffer.from('');
      }) as unknown as typeof execSync);

      try {
        await program.parseAsync(['node', 'test', 'ship', 'msg', '--cloudflare-only', '--yes']);
      } catch {}

      expect(mockDetectPlatform).toHaveBeenCalled();
      expect(execSync).toHaveBeenCalledWith(
        expect.stringContaining('git reset HEAD'),
        expect.anything()
      );
      expect(execSync).toHaveBeenCalledWith(
        expect.stringContaining('git commit -m'),
        expect.anything()
      );
    });

    it('should abort on mixed repo without --yes when user declines', async () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      writeFileSync(join(tempDir, 'other.txt'), 'other');
      mockedExecSync('git add -A', { stdio: 'ignore' });

      mockDetectPlatform.mockReturnValue({
        platform: 'mixed',
        confidence: 0.4,
        files: ['wrangler.toml'],
      });

      mockedExecSync.mockImplementation(((cmd: string, opts?: ExecOpts) => {
        const encoding = opts?.encoding || 'buffer';
        if (cmd === 'git diff --cached --name-only') {
          return encoding === 'utf-8' ? 'wrangler.toml\nother.txt\n' : Buffer.from('wrangler.toml\nother.txt\n');
        }
        return encoding === 'utf-8' ? '' : Buffer.from('');
      }) as unknown as typeof execSync);

      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);
      const askMock = vi.spyOn(shipModule, 'askConfirmation').mockResolvedValue(false);

      await expect(
        program.parseAsync(['node', 'test', 'ship', 'msg', '--cloudflare-only'])
      ).resolves.toBeDefined();

      expect(askMock).toHaveBeenCalled();
      expect(execSync).not.toHaveBeenCalledWith(
        expect.stringContaining('git commit -m "msg"'),
        expect.anything()
      );
    });
  });

  describe('normal ship (without --cloudflare-only)', () => {
    beforeEach(() => {
      writeFileSync(join(tempDir, 'README.md'), '# Test');
      mockedExecSync('git add -A', { stdio: 'ignore' });
      mockedExecSync('git commit -m "init"', { stdio: 'ignore' });
    });

    it('should proceed without platform detection', async () => {
      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);
      vi.spyOn(shipModule, 'verifyLive').mockResolvedValue(true);

      mockedExecSync.mockImplementation(((cmd: string, opts?: ExecOpts) => {
        const encoding = opts?.encoding || 'buffer';
        if (cmd === 'git diff --cached --name-only') {
          return encoding === 'utf-8' ? 'README.md\n' : Buffer.from('README.md\n');
        }
        if (cmd.startsWith('git commit -m') || cmd.startsWith('git push')) {
          return encoding === 'utf-8' ? '' : Buffer.from('');
        }
        return encoding === 'utf-8' ? '' : Buffer.from('');
      }) as unknown as typeof execSync);

      try {
        await program.parseAsync(['node', 'test', 'ship', 'normal commit']);
      } catch {}

      expect(mockDetectPlatform).not.toHaveBeenCalled();
      expect(execSync).toHaveBeenCalledWith(
        expect.stringContaining('git commit -m'),
        expect.anything()
      );
    });
  });

  describe('edge cases', () => {
    it('should handle preflight failure', async () => {
      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(false);

      await expect(
        program.parseAsync(['node', 'test', 'ship', 'msg'])
      ).rejects.toThrow(/Pre-flight checks/);
    });

    it('should handle PlatformDetector error', async () => {
      const program = createProgram();
      shipModule.registerShipCommand(program);

      mockDetectPlatform.mockImplementation(() => {
        throw new Error('Detection failed');
      });

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);

      await expect(
        program.parseAsync(['node', 'test', 'ship', 'msg', '--cloudflare-only', '--yes'])
      ).rejects.toThrow(/Platform detection failed/);
    });

    it('should return when no files after filtering', async () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      writeFileSync(join(tempDir, 'docker-compose.yml'), 'version: "3.8"');
      mockedExecSync('git add -A', { stdio: 'ignore' });

      mockDetectPlatform.mockReturnValue({
        platform: 'cloudflare',
        confidence: 0.9,
        files: ['wrangler.toml'],
      });

      const program = createProgram();
      shipModule.registerShipCommand(program);

      vi.spyOn(shipModule, 'preflightCheck').mockResolvedValue(true);

      mockedExecSync.mockImplementation(((cmd: string, opts?: ExecOpts) => {
        const encoding = opts?.encoding || 'buffer';
        if (cmd === 'git diff --cached --name-only') {
          return encoding === 'utf-8' ? '' : Buffer.from('');
        }
        if (cmd === 'git diff --name-only') {
          return encoding === 'utf-8' ? 'wrangler.toml\n' : Buffer.from('wrangler.toml\n');
        }
        if (cmd.startsWith('git reset HEAD')) {
          return encoding === 'utf-8' ? '' : Buffer.from('');
        }
        return encoding === 'utf-8' ? '' : Buffer.from('');
      }) as unknown as typeof execSync);

      await expect(
        program.parseAsync(['node', 'test', 'ship', 'msg', '--cloudflare-only', '--yes'])
      ).resolves.toBeDefined();

      expect(execSync).not.toHaveBeenCalledWith(
        expect.stringContaining('git commit'),
        expect.anything()
      );
    });
  });
});
