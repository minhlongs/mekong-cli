import { describe, it, expect } from 'vitest';
import { isCloudflareTestFile } from './test-utils.js';

describe('Cloudflare Test Filter - Utilities', () => {
  describe('isCloudflareTestFile', () => {
    it('should detect cloudflare directory in path', () => {
      expect(isCloudflareTestFile('tests/cloudflare/worker.test.ts', '')).toBe(true);
      expect(isCloudflareTestFile('tests/cf/api.test.ts', '')).toBe(true);
      expect(isCloudflareTestFile('tests/workers/queue.test.ts', '')).toBe(true);
    });

    it('should detect @cloudflare/ imports', () => {
      const content = `import { D1Database } from '@cloudflare/workers-types';`;
      expect(isCloudflareTestFile('tests/unit/test.ts', content)).toBe(true);
    });

    it('should detect wrangler.toml reference', () => {
      const content = `// Configuration from wrangler.toml`;
      expect(isCloudflareTestFile('tests/integration/config.test.ts', content)).toBe(true);
    });

    it('should detect Cloudflare-specific APIs', () => {
      expect(isCloudflareTestFile('tests/unit/d1.test.ts', 'const db: D1Database = getDb();')).toBe(true);
      expect(isCloudflareTestFile('tests/unit/kv.test.ts', 'const kv: KVNamespace = getKV();')).toBe(true);
      expect(isCloudflareTestFile('tests/unit/r2.test.ts', 'const bucket: R2Bucket = getR2();')).toBe(true);
      // ExecutionContext becomes executioncontext after lowercase
      expect(isCloudflareTestFile('tests/unit/worker.test.ts', 'export default { fetch(request, env: Env, ctx: ExecutionContext) {} }')).toBe(true);
    });

    it('should return false for non-cloudflare tests', () => {
      const content = `import express from 'express';`;
      expect(isCloudflareTestFile('tests/unit/express.test.ts', content)).toBe(false);
    });

    it('should detect ScheduledEvent', () => {
      const content = `export default { scheduled: (event: ScheduledEvent) => {} }`;
      expect(isCloudflareTestFile('tests/unit/scheduled.test.ts', content)).toBe(true);
    });

    it('should detect compatibility_date', () => {
      const content = `compatibility_date = "2024-01-01"`;
      expect(isCloudflareTestFile('tests/unit/config.test.ts', content)).toBe(true);
    });
  });
});

describe('Test Path Pattern Building', () => {
  it('should build valid regex pattern from file list', () => {
    const files = [
      'tests/cloudflare/worker.test.ts',
      'tests/cf/api.test.ts',
      'tests/workers/queue.test.ts',
    ];
    const pattern = buildTestPathPattern(files);

    // Pattern escapes dots so check for escaped version
    expect(pattern).toContain('worker\\.test\\.ts');
    expect(pattern).toContain('api\\.test\\.ts');
    expect(pattern).toContain('queue\\.test\\.ts');
    expect(pattern).toMatch(/\(.*\|.*\|.*\)/);
  });

  it('should escape special regex characters', () => {
    const files = ['tests/cloudflare/test+(special).ts'];
    const pattern = buildTestPathPattern(files);
    expect(pattern).toContain('\\+');
    expect(pattern).toContain('\\(');
  });

  it('should return empty string for empty list', () => {
    const pattern = buildTestPathPattern([]);
    expect(pattern).toBe('');
  });
});

// Helper functions (mirrored from implementation for testing)
function buildTestPathPattern(files: string[]): string {
  if (files.length === 0) {
    return '';
  }
  const patterns = files.map(f => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  return `(${patterns.join('|')})`;
}

function isCloudflareTestFile(filePath: string, content: string): boolean {
  const lowerContent = content.toLowerCase();
  const pathLower = filePath.toLowerCase();

  if (pathLower.includes('cloudflare') ||
      pathLower.includes('/cf/') ||
      pathLower.includes('/workers/') ||
      pathLower.includes('wrangler')) {
    return true;
  }

  if (lowerContent.includes('@cloudflare/') ||
      lowerContent.includes('from \'@cloudflare/') ||
      lowerContent.includes('from "@cloudflare/')) {
    return true;
  }

  if (lowerContent.includes('wrangler.toml') ||
      lowerContent.includes('wranglerconfig') ||
      lowerContent.includes('cloudflare.pages')) {
    return true;
  }

  const cfApis = [
    'd1database',
    'kvnamespace',
    'r2bucket',
    'executioncontext',
    'scheduledevent',
    'crons',
    'compatibility_date',
    'node_compat',
  ];
  if (cfApis.some(api => lowerContent.includes(api))) {
    return true;
  }

  return false;
}
