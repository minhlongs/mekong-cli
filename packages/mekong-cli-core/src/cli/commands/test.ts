import type { Command } from 'commander';
import { PlatformDetector, type DetectionResult } from '../../core/platform-detector.js';
import { heading, keyValue, divider, info, success, warn } from '../ui/output.js';
import { CloudflareTestFilter } from './test-cloudflare-filter.js';

export { CloudflareTestFilter };

export function registerTestCommand(program: Command): void {
  program
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

        heading('Test Runner');
        keyValue('Mode', opts.cloudflareOnly ? 'Cloudflare-only' : 'Full');
        keyValue('Project Root', projectRoot);
        divider();

        let testPattern = opts.pattern;
        let cloudflareFiles: string[] = [];
        let detectionResult: DetectionResult | null = null;

        if (opts.cloudflareOnly) {
          info('Đang phát hiện Cloudflare platform...');

          const detector = new PlatformDetector(projectRoot);
          detectionResult = detector.detectPlatform();

          keyValue('Detected Platform', detectionResult.platform);
          keyValue('Confidence', `${(detectionResult.confidence * 100).toFixed(1)}%`);

          if (detectionResult.files.length > 0) {
            keyValue('Signal Files', detectionResult.files.slice(0, 5).join(', ') +
              (detectionResult.files.length > 5 ? `... (+${detectionResult.files.length - 5} more)` : ''));
          }
          divider();

          const filter = new CloudflareTestFilter(projectRoot);
          cloudflareFiles = filter.getCloudflareTestFiles();

          if (cloudflareFiles.length === 0) {
            warn('Không tìm thấy test files nào thuộc Cloudflare ecosystem');
            info('Tạo cấu trúc tests/cloudflare/ hoặc thêm import @cloudflare/* vào test files');
            process.exit(0);
          }

          testPattern = testPattern || filter.getCloudflarePattern();

          success(`Cloudflare-only mode: tìm thấy ${cloudflareFiles.length} test files từ Cloudflare ecosystem`);
        }

        const vitestArgs: string[] = opts.watch ? ['vitest'] : ['vitest', 'run'];

        if (testPattern) {
          vitestArgs.push('--testPathPattern', testPattern);
        }

        if (opts.coverage) {
          vitestArgs.push('--coverage');
        }

        if (opts.verbose) {
          vitestArgs.push('--reporter=verbose');
        }

        divider();
        info(`Chạy: npx ${vitestArgs.join(' ')}`);
        divider();

        const { spawnSync } = await import('child_process');
        const result = spawnSync('npx', vitestArgs, {
          cwd: projectRoot,
          stdio: 'inherit',
          env: { ...process.env, FORCE_COLOR: '1' },
        });

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
