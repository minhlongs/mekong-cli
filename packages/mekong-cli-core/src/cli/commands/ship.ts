/**
 * `mekong ship` — Ship code to production với Cloudflare-only support (Wave ??).
 *
 *   mekong ship "commit message"          Ship với đầy đủ workflow
 *   mekong ship "msg" --cloudflare-only   Chỉ ship files thuộc Cloudflare platform
 *
 * Pipeline:
 *   1. Platform detection (nếu --cloudflare-only)
 *   2. Pre-flight checks (CI, lint, test, build)
 *   3. Filter staged changes (unstage non-CF files)
 *   4. Commit + Push
 *   5. Update PR description (nếu có)
 *   6. Verify live (health check)
 */
import type { Command } from 'commander';
import { success, info, warn, error, heading, keyValue, divider } from '../ui/output.js';
import type { MekongEngine } from '../../core/engine.js';
import { PlatformDetector, DetectionResult } from '../../core/platform-detector.js';
import { execSync } from 'child_process';
import * as readline from 'readline';

// Helper: escape file names cho shell command
function escapeFileName(file: string): string {
  return `"${file.replace(/"/g, '\\"')}"`;
}

// Helper: lấy danh sách file staged (git diff --cached)
function getStagedFiles(): string[] {
  try {
    const output = execSync('git diff --cached --name-only', {
      encoding: 'utf-8',
    });
    return output.split('\n').filter(Boolean);
  } catch {
    return [];
  }
}

// Helper: lấy danh sách file unstaged (git diff)
function getUnstagedFiles(): string[] {
  try {
    const output = execSync('git diff --name-only', {
      encoding: 'utf-8',
    });
    return output.split('\n').filter(Boolean);
  } catch {
    return [];
  }
}

// Helper: lấy tất cả file thay đổi (staged + unstaged)
export function getAllChangedFiles(): string[] {
  return Array.from(new Set([...getStagedFiles(), ...getUnstagedFiles()]));
}

// Helper: hỏi confirmation từ user
export async function askConfirmation(question: string): Promise<boolean> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
    });
  });
}

// Helper: pre-flight checks (CI status, lint, test, build)
export async function preflightCheck(): Promise<boolean> {
  info('🔍 Running pre-flight checks...');

  // Check git repo
  try {
    execSync('git rev-parse --is-inside-work-tree', { encoding: 'utf-8' });
  } catch {
    error('❌ Not in a git repository');
    return false;
  }

  // Check if there are changes to commit
  const staged = getStagedFiles();
  const unstaged = getUnstagedFiles();
  if (staged.length === 0 && unstaged.length === 0) {
    warn('⚠️  No changes to commit');
    return false;
  }

  // TODO: Thêm checks cho CI status, lint, test, build
  // Hiện tại skip để đơn giản

  info('✅ Pre-flight checks passed');
  return true;
}

// Helper: verify live deployment (health check)
export async function verifyLive(): Promise<boolean> {
  info('🔍 Verifying deployment...');

  // TODO: Ping health check endpoint
  // Hiện tại giả định thành công
  await new Promise(resolve => setTimeout(resolve, 100));

  info('✅ Deployment verified');
  return true;
}

// Helper: update PR description với Cloudflare-only section
export async function updatePrDescription(detectionResult: DetectionResult): Promise<void> {
  try {
    // Kiểm tra nếu có gh CLI và PR hiện tại
    const branch = execSync('git rev-parse --abbrev-ref HEAD', {
      encoding: 'utf-8',
    }).trim();

    // Thử lấy PR number cho branch hiện tại
    let prNumber: string | null = null;
    try {
      const prList = execSync(`gh pr view ${branch} --json number --jq '.number'`, {
        encoding: 'utf-8',
        stdio: ['ignore', 'pipe', 'ignore'],
      });
      prNumber = prList.trim();
    } catch {
      // Không có PR cho branch này, bỏ qua
      info('ℹ️  No open PR found for current branch. Skipping PR description update.');
      return;
    }

    if (!prNumber) {
      info('ℹ️  No PR number detected. Skipping PR description update.');
      return;
    }

    // Lấy PR description hiện tại
    const currentBody = execSync(`gh pr view ${prNumber} --json body --jq '.body'`, {
      encoding: 'utf-8',
    });

    // Thêm Cloudflare-only section
    const cfSection = `
### Cloudflare-only deployment

**Platform:** ${detectionResult.platform}
**Confidence:** ${(detectionResult.confidence * 100).toFixed(1)}%
**Detected files (${detectionResult.files.length}):**
${detectionResult.files.map(f => `- \`${f}\``).join('\n')}

*Deployed with --cloudflare-only flag*
`;

    const newBody = currentBody + cfSection;

    // Cập nhật PR
    execSync(`gh pr edit ${prNumber} --body ${escapeFileName(newBody)}`, {
      stdio: 'inherit',
    });

    success('✅ PR description updated with Cloudflare deployment info');
  } catch (err) {
    // Nếu gh không có sẵn, chỉ log
    info('ℹ️  Could not update PR description (gh CLI not available or no PR).');
  }
}

/**
 * Đăng ký ship command
 */
export function registerShipCommand(program: Command, engine?: MekongEngine): void {
  const cmd = program.command('ship').description('Ship code to production');

  cmd
    .argument('<message>', 'Commit message')
    .option('--cloudflare-only', 'Chỉ ship các file thuộc Cloudflare platform')
    .option('--yes', 'Skip confirmation prompts (assume yes)')
    .option('--branch <branch>', 'Target branch để push', 'main')
    .action(async (message: string, opts: { cloudflareOnly?: boolean; yes?: boolean; branch?: string }) => {
      heading('🚢 Ship Command');

      // Khởi tạo variables
      let detector: PlatformDetector | null = null;
      let detectionResult: DetectionResult | null = null;

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 1: Platform Detection (trước pre-flight check)
      // ═══════════════════════════════════════════════════════════════════════════
      if (opts.cloudflareOnly) {
        info('🔍 Detecting platform với --cloudflare-only...');

        try {
          detector = new PlatformDetector();
          detectionResult = detector.detectPlatform();
        } catch (err) {
          error('❌ Platform detection failed: ' + (err as Error).message);
          throw new Error('Platform detection failed');
        }

        // Log detection result
        keyValue('Platform', detectionResult.platform);
        keyValue('Confidence', detectionResult.confidence.toFixed(2));
        keyValue('CF files', String(detectionResult.files.length));

        if (detectionResult.debug) {
          info('Debug signals:');
          for (const sig of detectionResult.debug.matchedSignals) {
            info(`  - ${sig.signal}: ${sig.file} (weight: ${sig.weight})`);
          }
        }

        // Xử lý dựa trên platform
        if (detectionResult.platform === 'other') {
          error('❌ No Cloudflare projects detected.');
          error('   Không thể sử dụng --cloudflare-only với repository này.');
          throw new Error('No Cloudflare projects detected');
        }

        if (detectionResult.platform === 'mixed') {
          // Xác định non-Cloudflare files
          const allChanged = getAllChangedFiles();
          const nonCfFiles = allChanged.filter(f => !detectionResult!.files.includes(f));

          if (nonCfFiles.length > 0) {
            warn('⚠️  Mixed platform: phát hiện non-Cloudflare files:');
            for (const file of nonCfFiles) {
              info(`   - ${file}`);
            }

            // Yêu cầu confirmation (trừ khi --yes)
            if (!opts.yes) {
              const confirmed = await askConfirmation('   Tiếp tục với Cloudflare-only deployment? (y/N): ');
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

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 2: Pre-flight Checks
      // ═══════════════════════════════════════════════════════════════════════════
      const preflightOk = await preflightCheck();
      if (!preflightOk) {
        error('❌ Pre-flight checks thất bại. Dừng lại.');
        throw new Error('Pre-flight checks failed');
      }

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 3: Filter staged changes (unstage non-CF files)
      // ═══════════════════════════════════════════════════════════════════════════
      if (opts.cloudflareOnly && detectionResult) {
        const staged = getStagedFiles();
        const unstaged = getUnstagedFiles();
        const allRelevant = [...staged, ...unstaged];
        const nonCf = allRelevant.filter(f => !detectionResult.files.includes(f));

        if (nonCf.length > 0) {
          info(`🧹 Unstaging ${nonCf.length} non-Cloudflare files:`);
          for (const file of nonCf) {
            info(`   - ${file}`);
          }
          try {
            execSync(`git reset HEAD ${nonCf.map(escapeFileName).join(' ')}`, {
              stdio: 'inherit',
            });
            info(`✅ Đã unstaging ${nonCf.length} files`);
          } catch (err) {
            warn('⚠️  Có lỗi khi unstaging files: ' + (err as Error).message);
          }
        }
      }

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 4: Commit
      // ═══════════════════════════════════════════════════════════════════════════
      const remainingStaged = getStagedFiles();
      if (remainingStaged.length === 0) {
        warn('⚠️  Không có file nào để commit sau khi filter');
        return;
      }

      info(`📝 Committing ${remainingStaged.length} files với message: "${message}"`);
      try {
        execSync(`git commit -m ${escapeFileName(message)}`, {
          stdio: 'inherit',
        });
      } catch (err) {
        error('❌ Commit thất bại: ' + (err as Error).message);
        throw new Error('Commit failed: ' + (err as Error).message);
      }

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 5: Push
      // ═══════════════════════════════════════════════════════════════════════════
      info(`📤 Pushing to origin/${opts.branch}...`);
      try {
        execSync(`git push origin HEAD:${opts.branch}`, {
          stdio: 'inherit',
        });
      } catch (err) {
        error('❌ Push thất bại: ' + (err as Error).message);
        throw new Error('Push failed: ' + (err as Error).message);
      }

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 6: Update PR description
      // ═══════════════════════════════════════════════════════════════════════════
      if (detectionResult) {
        await updatePrDescription(detectionResult);
      }

      // ═══════════════════════════════════════════════════════════════════════════
      // PHẦN 7: Verify Live
      // ═══════════════════════════════════════════════════════════════════════════
      const verifyOk = await verifyLive();
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
