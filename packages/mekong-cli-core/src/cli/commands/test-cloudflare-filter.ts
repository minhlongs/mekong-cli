/**
 * test-cloudflare-filter.ts — Detect test files belonging to the Cloudflare ecosystem.
 */
import { existsSync, readFileSync, readdirSync } from 'fs';
import { join, relative, extname, basename } from 'path';

export interface CloudflareTestFilterOptions {
  cloudflareOnly: boolean;
  projectRoot: string;
}

export class CloudflareTestFilter {
  private readonly projectRoot: string;
  private readonly testsDir: string;

  constructor(projectRoot: string) {
    this.projectRoot = projectRoot;
    this.testsDir = join(projectRoot, 'tests');
  }

  getCloudflareTestFiles(): string[] {
    const cloudflareTests: string[] = [];

    if (!existsSync(this.testsDir)) {
      return cloudflareTests;
    }

    const allTestFiles = this.scanTestFiles(this.testsDir);

    for (const filePath of allTestFiles) {
      if (this.isCloudflareTestFile(filePath)) {
        cloudflareTests.push(filePath);
      }
    }

    return cloudflareTests;
  }

  private scanTestFiles(dir: string): string[] {
    const files: string[] = [];

    if (!existsSync(dir)) {
      return files;
    }

    try {
      const entries = readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const fullPath = join(dir, entry.name);

        if (entry.isDirectory()) {
          files.push(...this.scanTestFiles(fullPath));
        } else if (this.isTestFile(entry.name)) {
          const relPath = relative(this.projectRoot, fullPath);
          files.push(relPath);
        }
      }
    } catch {
      // Ignore unreadable directories
    }

    return files;
  }

  private isTestFile(filename: string): boolean {
    const ext = extname(filename);
    const name = basename(filename, ext);
    return (
      (name.endsWith('.test') || name.endsWith('.spec')) &&
      (ext === '.ts' || ext === '.js' || ext === '.mts' || ext === '.mjs')
    );
  }

  private isCloudflareTestFile(filePath: string): boolean {
    const content = readFileSync(join(this.projectRoot, filePath), 'utf-8');
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

  buildTestPathPattern(files: string[]): string {
    if (files.length === 0) {
      return '';
    }

    const patterns = files.map(f => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    return `(${patterns.join('|')})`;
  }

  getCloudflarePattern(): string {
    return '(cloudflare|cf|workers|wrangler)';
  }
}
