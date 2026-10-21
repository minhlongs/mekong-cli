/**
 * `mekong ship` — Ship code to production với Cloudflare-only support.
 */
import type { Command } from 'commander';
import { success, info, warn, error, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';
import { PlatformDetector, type DetectionResult } from '../../core/platform-detector.js';
import { execSync } from 'child_process';
import {
  escapeFileName,
  getStagedFiles,
  getUnstagedFiles,
  getAllChangedFiles,
  askConfirmation,
  preflightCheck,
  verifyLive,
  updatePrDescription,
  unstageNonCloudflareFiles,
} from './ship-helpers.js';
import * as shipModule from './ship.js';

export {
  getAllChangedFiles,
  askConfirmation,
  preflightCheck,
  verifyLive,
  updatePrDescription,
};

export function registerShipCommand(program: Command, _engine?: MekongEngine): void {
  const cmd = program.command('ship').description('Ship code to production');

  cmd
    .argument('<message>', 'Commit message')
    .option('--cloudflare-only', 'Chỉ ship các file thuộc Cloudflare platform')
    .option('--yes', 'Skip confirmation prompts (assume yes)')
    .option('--branch <branch>', 'Target branch để push', 'main')
    .action(async (message: string, opts: { cloudflareOnly?: boolean; yes?: boolean; branch?: string }) => {
      heading('🚢 Ship Command');

      let detectionResult: DetectionResult | null = null;

      if (opts.cloudflareOnly) {
        info('🔍 Detecting platform với --cloudflare-only...');

        try {
          const detector = new PlatformDetector();
          detectionResult = detector.detectPlatform();
        } catch (err) {
          error('❌ Platform detection failed: ' + (err as Error).message);
          throw new Error('Platform detection failed');
        }

        keyValue('Platform', detectionResult.platform);
        keyValue('Confidence', detectionResult.confidence.toFixed(2));
        keyValue('CF files', String(detectionResult.files.length));

        if (detectionResult.debug) {
          info('Debug signals:');
          for (const sig of detectionResult.debug.matchedSignals) {
            info(`  - ${sig.signal}: ${sig.file} (weight: ${sig.weight})`);
          }
        }

        if (detectionResult.platform === 'other') {
          error('❌ No Cloudflare projects detected.');
          error('   Không thể sử dụng --cloudflare-only với repository này.');
          throw new Error('No Cloudflare projects detected');
        }

        if (detectionResult.platform === 'mixed') {
          const allChanged = shipModule.getAllChangedFiles();
          const nonCfFiles = allChanged.filter(f => !detectionResult!.files.includes(f));

          if (nonCfFiles.length > 0) {
            warn('⚠️  Mixed platform: phát hiện non-Cloudflare files:');
            for (const file of nonCfFiles) {
              info(`   - ${file}`);
            }

            if (!opts.yes) {
              const confirmed = await shipModule.askConfirmation('   Tiếp tục với Cloudflare-only deployment? (y/N): ');
              if (!confirmed) {
                info('🚫 Đã hủy bởi người dùng.');
                return;
              }
            } else {
              info('✅ --yes flag: bỏ qua confirmation');
            }
          } else {
            info('✅ Tất cả file đều thuộc Cloudflare platform');
          }
        }
      }

      const preflightOk = await shipModule.preflightCheck();
      if (!preflightOk) {
        error('❌ Pre-flight checks thất bại. Dừng lại.');
        throw new Error('Pre-flight checks failed');
      }

      if (opts.cloudflareOnly && detectionResult) {
        unstageNonCloudflareFiles(detectionResult);
      }

      const remainingStaged = getStagedFiles();
      if (remainingStaged.length === 0) {
        warn('⚠️  Không có file nào để commit sau khi filter');
        return;
      }

      info(`📝 Committing ${remainingStaged.length} files với message: "${message}"`);
      try {
        execSync(`git commit -m ${escapeFileName(message)}`, { stdio: 'inherit' });
      } catch (err) {
        error('❌ Commit thất bại: ' + (err as Error).message);
        throw new Error('Commit failed: ' + (err as Error).message);
      }

      info(`📤 Pushing to origin/${opts.branch}...`);
      try {
        execSync(`git push origin HEAD:${opts.branch}`, { stdio: 'inherit' });
      } catch (err) {
        error('❌ Push thất bại: ' + (err as Error).message);
        throw new Error('Push failed: ' + (err as Error).message);
      }

      if (detectionResult) {
        await shipModule.updatePrDescription(detectionResult);
      }

      const verifyOk = await shipModule.verifyLive();
      if (!verifyOk) {
        warn('⚠️  Verification failed. Kiểm tra deployment thủ công.');
      }

      divider();
      success('🎉 Ship hoàn tất!');
      info(`   Commit đã được push đến ${opts.branch}`);
      if (detectionResult) {
        keyValue('   Platform', detectionResult.platform);
        keyValue('   CF files', String(detectionResult.files.length));
      }
    });
}
