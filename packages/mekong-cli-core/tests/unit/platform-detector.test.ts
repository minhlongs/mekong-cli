import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { PlatformDetector } from '../../src/core/platform-detector.ts';
import { mkdirSync, rmSync, existsSync, writeFileSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

describe('PlatformDetector', () => {
  let tempDir: string;
  let originalCwd: string;

  beforeEach(() => {
    originalCwd = process.cwd();
    // Create temp directory for testing
    tempDir = join(originalCwd, '.test-temp', `platform-detector-${Date.now()}`);
    mkdirSync(tempDir, { recursive: true });
    process.chdir(tempDir);

    // Initialize git repo
    execSync('git init', { cwd: tempDir, stdio: 'ignore' });
    execSync('git config user.email "test@test.com"', { cwd: tempDir, stdio: 'ignore' });
    execSync('git config user.name "Test"', { cwd: tempDir, stdio: 'ignore' });
  });

  afterEach(() => {
    process.chdir(originalCwd);
    if (existsSync(tempDir)) {
      rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('detectPlatform', () => {
    it('detects pure Cloudflare with wrangler.toml and @cloudflare/workers (confidence > 0.8)', () => {
      // Setup files - all 4 signals to reach 1.0
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      mkdirSync(join(tempDir, 'cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, 'cloudflare', 'config.ts'), 'export const config = {};');
      mkdirSync(join(tempDir, '@cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, '@cloudflare', 'workers-types.d.ts'), '');
      mkdirSync(join(tempDir, 'cf'), { recursive: true });
      writeFileSync(join(tempDir, 'cf', 'config.json'), '{}');

      // Stage files but DON'T commit (so git diff shows them)
      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.platform).toBe('cloudflare');
      expect(result.confidence).toBeGreaterThanOrEqual(0.9);
      expect(result.files).toContain('wrangler.toml');
      expect(result.files.some(f => f.includes('@cloudflare/'))).toBe(true);
      expect(result.files.some(f => f.includes('cloudflare/'))).toBe(true);
      expect(result.files.some(f => f.startsWith('cf/'))).toBe(true);
    });

    it('detects mixed Cloudflare with wrangler.toml only (confidence ~0.36)', () => {
      // Only wrangler.toml - weight 1.0 / max 2.8 = 0.357
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.platform).toBe('mixed');
      expect(result.confidence).toBeGreaterThanOrEqual(0.3);
      expect(result.confidence).toBeLessThan(0.7);
      expect(result.files).toContain('wrangler.toml');
    });

    it('detects Cloudflare with multiple signals (confidence >= 0.7)', () => {
      // wrangler.toml (1.0) + @cloudflare/ (0.8) + cloudflare/ (0.6) + cf/ (0.4) = 2.8/2.8 = 1.0
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      mkdirSync(join(tempDir, 'cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, 'cloudflare', 'config.ts'), 'export const config = {};');
      mkdirSync(join(tempDir, '@cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, '@cloudflare', 'workers-types.d.ts'), '');
      mkdirSync(join(tempDir, 'cf'), { recursive: true });
      writeFileSync(join(tempDir, 'cf', 'config.json'), '{}');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.platform).toBe('cloudflare');
      expect(result.confidence).toBeGreaterThanOrEqual(0.7);
      expect(result.files.length).toBeGreaterThanOrEqual(4);
    });

    it('detects non-Cloudflare with docker-compose.yml (confidence < 0.3)', () => {
      writeFileSync(join(tempDir, 'docker-compose.yml'), 'version: "3.8"');
      writeFileSync(join(tempDir, 'Dockerfile'), 'FROM node:18');
      writeFileSync(join(tempDir, 'next.config.js'), 'module.exports = {}');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.platform).toBe('other');
      expect(result.confidence).toBeLessThan(0.3);
      expect(result.files).toHaveLength(0);
    });

    it('detects mixed with wrangler.toml and next.js', () => {
      // wrangler.toml (1.0) alone = 1.0 / 2.8 = 0.357
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      writeFileSync(join(tempDir, 'next.config.js'), 'module.exports = {}');
      writeFileSync(join(tempDir, 'package.json'), '{"name": "next-app"}');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.platform).toBe('mixed');
      expect(result.files).toContain('wrangler.toml');
    });

    it('detects cf branch pattern', () => {
      // cf-branch-name pattern (cf/ directory) + wrangler.toml to get mixed
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      mkdirSync(join(tempDir, 'cf'), { recursive: true });
      writeFileSync(join(tempDir, 'cf', 'config.json'), '{}');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      // wrangler (1.0) + cf (0.4) = 1.4/2.8 = 0.5 -> mixed
      expect(result.platform).toBe('mixed');
      expect(result.files.some(f => f.startsWith('cf/') || f.includes('cf/'))).toBe(true);
    });
  });

  describe('cache', () => {
    it('caches detection result', () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result1 = detector.detectPlatform();
      const result2 = detector.detectPlatform();

      // Result values should be equal (same cache hit)
      expect(result1.platform).toBe(result2.platform);
      expect(result1.confidence).toBe(result2.confidence);
      expect(result1.files).toEqual(result2.files);
    });

    it('refresh clears cache and recomputes', () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result1 = detector.detectPlatform();

      // Modify a file to change git state
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test2"');
      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const result2 = detector.refresh();

      // Confidence might change because git state changed
      expect(result2).toBeDefined();
    });

    it('clearCache removes cached entry', () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      detector.detectPlatform();

      // Access private cache via bracket notation for testing
      // @ts-expect-error - accessing private field for test
      expect(detector['cache']).not.toBeNull();

      detector.clearCache();
      // @ts-expect-error - accessing private field for test
      expect(detector['cache']).toBeNull();
    });
  });

  describe('helper methods', () => {
    it('isCloudflareOnly returns true for cloudflare platform', () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      mkdirSync(join(tempDir, 'cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, 'cloudflare', 'config.ts'), '{}');
      mkdirSync(join(tempDir, '@cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, '@cloudflare', 'workers-types.d.ts'), '');
      mkdirSync(join(tempDir, 'cf'), { recursive: true });
      writeFileSync(join(tempDir, 'cf', 'config.json'), '{}');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      expect(detector.isCloudflareOnly()).toBe(true);
    });

    it('isCloudflareOnly returns false for non-cloudflare', () => {
      writeFileSync(join(tempDir, 'docker-compose.yml'), 'version: "3.8"');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      expect(detector.isCloudflareOnly()).toBe(false);
    });

    it('getThreshold returns default threshold of 0.7', () => {
      const detector = new PlatformDetector(tempDir);
      expect(detector.getThreshold()).toBe(0.7);
    });

    it('setThreshold updates threshold within valid range', () => {
      const detector = new PlatformDetector(tempDir);
      detector.setThreshold(0.5);
      expect(detector.getThreshold()).toBe(0.5);
    });

    it('setThreshold throws for value > 1', () => {
      const detector = new PlatformDetector(tempDir);
      expect(() => detector.setThreshold(1.5)).toThrow('Threshold phải nằm trong khoảng [0, 1]');
    });

    it('setThreshold throws for value < 0', () => {
      const detector = new PlatformDetector(tempDir);
      expect(() => detector.setThreshold(-0.1)).toThrow('Threshold phải nằm trong khoảng [0, 1]');
    });
  });

  describe('edge cases', () => {
    it('handles empty git repo gracefully', () => {
      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.platform).toBe('other');
      expect(result.confidence).toBe(0);
      expect(result.files).toHaveLength(0);
    });

    it('handles deleted files gracefully', () => {
      // Create and stage a file, then delete it
      const filePath = join(tempDir, 'deleted.txt');
      writeFileSync(filePath, 'content');
      execSync('git add deleted.txt', { cwd: tempDir, stdio: 'ignore' });
      rmSync(filePath, { force: true });

      const detector = new PlatformDetector(tempDir);
      // Should not throw even though file was deleted
      const result = detector.detectPlatform();
      expect(result).toBeDefined();
    });

    it('handles files with special characters in path', () => {
      mkdirSync(join(tempDir, '@cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, '@cloudflare', 'workers-types.d.ts'), '');
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.files.some(f => f.includes('@cloudflare/'))).toBe(true);
    });
  });

  describe('debug information', () => {
    it('includes debug info in result', () => {
      writeFileSync(join(tempDir, 'wrangler.toml'), 'name = "test"');
      mkdirSync(join(tempDir, 'src'), { recursive: true });
      writeFileSync(join(tempDir, 'src', 'worker.ts'), 'import { Worker } from "@cloudflare/workers"');
      mkdirSync(join(tempDir, 'cloudflare'), { recursive: true });
      writeFileSync(join(tempDir, 'cloudflare', 'config.ts'), '{}');

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      expect(result.debug).toBeDefined();
      expect(result.debug!.totalWeight).toBeGreaterThan(0);
      expect(result.debug!.maxPossibleWeight).toBeGreaterThan(0);
      expect(result.debug!.matchedSignals).toBeInstanceOf(Array);
      expect(result.debug!.matchedSignals.length).toBeGreaterThan(0);
    });
  });

  describe('performance', () => {
    it('processes many files within 1000ms', () => {
      const startTime = Date.now();

      // Create many files
      for (let i = 0; i < 1000; i++) {
        writeFileSync(join(tempDir, `file-${i}.txt`), `content ${i}`);
      }

      execSync('git add -A', { cwd: tempDir, stdio: 'ignore' });

      const detector = new PlatformDetector(tempDir);
      const result = detector.detectPlatform();

      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(1000);
      expect(result).toBeDefined();
    });
  });
});
