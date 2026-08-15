import type { Command } from 'commander';
import { existsSync, readFileSync, readdirSync, statSync } from 'fs';
import { join, relative, extname, basename } from 'path';
import { execSync } from 'child_process';
import { PlatformDetector, type DetectionResult } from '../../core/platform-detector.js';
import { heading, keyValue, divider, info, success, warn } from '../ui/output.js';

interface CloudflareTestFilterOptions {
  cloudflareOnly: boolean;
  projectRoot: string;
}

/**
 * Phát hiện test files thuộc Cloudflare ecosystem
 */
class CloudflareTestFilter {
  private readonly projectRoot: string;
  private readonly testsDir: string;

  constructor(projectRoot: string) {
    this.projectRoot = projectRoot;
    this.testsDir = join(projectRoot, 'tests');
  }

  /**
   * Lấy danh sách test files thuộc Cloudflare
   */
  getCloudflareTestFiles(): string[] {
    const cloudflareTests: string[] = [];

    if (!existsSync(this.testsDir)) {
      return cloudflareTests;
    }

    // Scan recursively tests directory
    const allTestFiles = this.scanTestFiles(this.testsDir);

    for (const filePath of allTestFiles) {
      if (this.isCloudflareTestFile(filePath)) {
        cloudflareTests.push(filePath);
      }
    }

    return cloudflareTests;
  }

  /**
   * Scan tất cả test files trong directory
   */
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

  /**
   * Kiểm tra file có phải là test file không
   */
  private isTestFile(filename: string): boolean {
    const ext = extname(filename);
    const name = basename(filename, ext);
    return (
      (name.endsWith('.test') || name.endsWith('.spec')) &&
      (ext === '.ts' || ext === '.js' || ext === '.mts' || ext === '.mjs')
    );
  }

  /**
   * Kiểm tra file có phải Cloudflare test không
   */
  private isCloudflareTestFile(filePath: string): boolean {
    const content = readFileSync(join(this.projectRoot, filePath), 'utf-8');
    const lowerContent = content.toLowerCase();

    // Check 1: Path contains cloudflare signals
    const pathLower = filePath.toLowerCase();
    if (pathLower.includes('cloudflare') ||
        pathLower.includes('/cf/') ||
        pathLower.includes('/workers/') ||
        pathLower.includes('wrangler')) {
      return true;
    }

    // Check 2: Import từ @cloudflare/*
    if (lowerContent.includes('@cloudflare/') ||
        lowerContent.includes('from \'@cloudflare/') ||
        lowerContent.includes('from "@cloudflare/')) {
      return true;
    }

    // Check 3: Reference to wrangler.toml
    if (lowerContent.includes('wrangler.toml') ||
        lowerContent.includes('wranglerconfig') ||
        lowerContent.includes('cloudflare.pages')) {
      return true;
    }

    // Check 4: Cloudflare-specific APIs (lowercase matching)
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

  /**
   * Build testPathPattern từ danh sách files
   */
  buildTestPathPattern(files: string[]): string {
    if (files.length === 0) {
      return '';
    }

    // Escape special regex chars and create pattern
    const patterns = files.map(f => {
      // Convert to regex-friendly pattern
      const escaped = f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return escaped;
    });

    // Combine into single pattern: (file1|file2|file3)
    return `(${patterns.join('|')})`;
  }

  /**
   * Build simple cloudflare pattern for quick filtering
   */
  getCloudflarePattern(): string {
    return '(cloudflare|cf|workers|wrangler)';
  }
}

/**
 * Đăng ký test command
 */
export function registerTestCommand(program: Command): void {
  const testCmd = program
    .command('test')
    .description('Chạy test suite với hỗ trợ Cloudflare-only mode')
    .option('--cloudflare-only', 'Chỉ chạy tests liên quan đến Cloudflare')
    .option('--pattern <pattern>', 'Custom test path pattern (overrides cloudflare filter)')
    .option('--watch', 'Chạy test trong watch mode')
    .option('--coverage', 'Tạo coverage report')
    .option('--verbose', 'Hiển thị output chi tiết')
    .action(async (opts: {
      cloudflareOnly: boolean;
      pattern?: string;
      watch: boolean;
      coverage: boolean;
      verbose: boolean;
    }) => {
      try {
        const projectRoot = process.cwd();

        // Hiển thị header
        heading('Test Runner');
        keyValue('Mode', opts.cloudflareOnly ? 'Cloudflare-only' : 'Full');
        keyValue('Project Root', projectRoot);
        divider();

        let testPattern = opts.pattern;
        let cloudflareFiles: string[] = [];
        let detectionResult: DetectionResult | null = null;

        // Xử lý cloudflare-only mode
        if (opts.cloudflareOnly) {
          info('Đang phát hiện Cloudflare platform...');

          // Detect platform
          const detector = new PlatformDetector(projectRoot);
          detectionResult = detector.detectPlatform();

          keyValue('Detected Platform', detectionResult.platform);
          keyValue('Confidence', `${(detectionResult.confidence * 100).toFixed(1)}%`);

          if (detectionResult.files.length > 0) {
            keyValue('Signal Files', detectionResult.files.slice(0, 5).join(', ') +
              (detectionResult.files.length > 5 ? `... (+${detectionResult.files.length - 5} more)` : ''));
          }
          divider();

          // Get Cloudflare test files
          const filter = new CloudflareTestFilter(projectRoot);
          cloudflareFiles = filter.getCloudflareTestFiles();

          if (cloudflareFiles.length === 0) {
            warn('Không tìm thấy test files nào thuộc Cloudflare ecosystem');
            info('Tạo cấu trúc tests/cloudflare/ hoặc thêm import @cloudflare/* vào test files');
            process.exit(0);
          }

          // Build pattern
          testPattern = testPattern || filter.getCloudflarePattern();

          success(`Cloudflare-only mode: tìm thấy ${cloudflareFiles.length} test files từ Cloudflare ecosystem`);
        }

        // Build vitest command
        let vitestArgs: string[] = opts.watch ? ['vitest'] : ['vitest', 'run'];

        if (testPattern) {
          vitestArgs.push('--testPathPattern', testPattern);
        }

        if (opts.coverage) {
          vitestArgs.push('--coverage');
        }

        if (opts.verbose) {
          vitestArgs.push('--reporter=verbose');
        }

        // Show summary
        divider();
        info(`Chạy: npx ${vitestArgs.join(' ')}`);
        divider();

        // Execute vitest
        const { spawnSync } = await import('child_process');
        const result = spawnSync('npx', vitestArgs, {
          cwd: projectRoot,
          stdio: 'inherit',
          env: { ...process.env, FORCE_COLOR: '1' },
        });

        // Post-run summary
        if (opts.cloudflareOnly && detectionResult) {
          divider();
          heading('Cloudflare Detection Summary');
          keyValue('Platform', detectionResult.platform);
          keyValue('Confidence', `${(detectionResult.confidence * 100).toFixed(1)}%`);
          keyValue('Test Files Found', String(cloudflareFiles.length));
          keyValue('Pattern Used', testPattern || 'default');
        }

        process.exit(result.status ?? 0);
      } catch (error) {
        console.error('Lỗi khi chạy test command:', error);
        process.exit(1);
      }
    });
}
