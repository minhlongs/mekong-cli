import { existsSync, statSync, readFileSync } from 'fs';
import { join, extname, dirname } from 'path';
import { execSync } from 'child_process';

/**
 * Các signals để phát hiện Cloudflare-only mode với weight tương ứng
 * Confidence được tính bằng totalWeight / MAX_CONFIDENCE_SCORE (5.0)
 */
const SIGNALS = {
  WRANGLER_TOML: { weight: 2.0, pattern: 'wrangler.toml' },
  WORKER_FILE: { weight: 1.0, pattern: /(^|\/)(worker|index)\.(ts|js)$/ },
  CLOUDFLARE_PKG: { weight: 1.0, pattern: /^@cloudflare\// },
  CLOUDFLARE_DIR: { weight: 0.5, pattern: /^cloudflare\// },
  CLOUDFLARE_PAGES: { weight: 4.0, pattern: /^pages\// }, // Strong signal for Pages
  PAGES_BUILD_DIR: { weight: 1.0, pattern: 'pages_build_output_dir' },
  CF_BRANCH: { weight: 0.5, pattern: /^cf\// },
} as const;

/**
 * Max confidence score for normalization (5.0 = 100%)
 */
const MAX_CONFIDENCE_SCORE = 5.0;

/**
 * Branch name boost normalized (+0.15)
 */
const BRANCH_BOOST = 0.15 * MAX_CONFIDENCE_SCORE; // 0.75

/**
 * Multiple wrangler.toml boost normalized (+0.2)
 */
const MULTIPLE_WRANGLER_BOOST = 0.2 * MAX_CONFIDENCE_SCORE; // 1.0

/**
 * Kết quả detection
 */
export interface DetectionResult {
  /** Platform được phát hiện */
  platform: 'cloudflare' | 'mixed' | 'other';
  /** Điểm tin cậy từ 0 đến 1 */
  confidence: number;
  /** Danh sách file trigger signals */
  files: string[];
  /** Debug info */
  debug?: {
    totalWeight: number;
    maxPossibleWeight: number;
    matchedSignals: Array<{ file: string; signal: string; weight: number }>;
  };
}

/**
 * Cache entry structure
 */
interface CacheEntry {
  mtime: number;
  result: DetectionResult;
}

/**
 * PlatformDetector - Phát hiện Cloudflare-only mode bằng weighted scoring
 *
 * Algorithm:
 * 1. Lấy danh sách file thay đổi từ git diff (staged + unstaged)
 * 2. Check mỗi file contrare các signals
 * 3. Sum weights, normalize bởi max possible weight
 * 4. Return confidence score và platform classification
 *
 * Thresholds:
 * - confidence >= 0.7: cloudflare
 * - 0.3 <= confidence < 0.7: mixed
 * - confidence < 0.3: other
 */
export class PlatformDetector {
  private cache: CacheEntry | null = null;
  private cacheKey: string;
  private readonly projectRoot: string;
  private readonly threshold = 0.7;

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
    this.cacheKey = this.computeCacheKey();
  }

  /**
   * Get current git branch name
   */
  private getCurrentBranch(): string {
    try {
      return execSync('git rev-parse --abbrev-ref HEAD', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      }).trim();
    } catch {
      return '';
    }
  }

  /**
   * Compute cache key dựa trên git HEAD commit + index state
   */
  private computeCacheKey(): string {
    try {
      const staged = execSync('git diff --cached --name-only', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      }).split('\n').filter(Boolean).sort().join('|');
      const unstaged = execSync('git diff --name-only', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      }).split('\n').filter(Boolean).sort().join('|');
      const head = execSync('git rev-parse HEAD', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      }).trim();
      return `${head}:${staged}:${unstaged}`;
    } catch {
      // Nếu không có git, dựa vào project root
      return `no-git:${this.projectRoot}`;
    }
  }

  /**
   * Kiểm tra cache có hợp lệ không
   */
  private isCacheValid(): boolean {
    if (!this.cache) return false;

    // Check nếu git state thay đổi
    const currentKey = this.computeCacheKey();
    return currentKey === this.cacheKey;
  }

  /**
   * Lấy danh sách file từ git diff (staged + unstaged)
   */
  private getChangedFiles(): string[] {
    try {
      const staged = execSync('git diff --cached --name-only', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      });
      const unstaged = execSync('git diff --name-only', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      });

      const files = new Set<string>();
      staged.split('\n').filter(Boolean).forEach(f => files.add(f));
      unstaged.split('\n').filter(Boolean).forEach(f => files.add(f));

      return Array.from(files);
    } catch {
      // Fallback: quét toàn bộ project nếu không có git
      return this.scanAllFiles();
    }
  }

  /**
   * Scan tất cả file trong project (fallback)
   */
  private scanAllFiles(): string[] {
    const files: string[] = [];
    try {
      const allFiles = execSync('git ls-files', {
        cwd: this.projectRoot,
        encoding: 'utf-8',
      });
      allFiles.split('\n').filter(Boolean).forEach(f => files.push(f));
    } catch {
      // Manual scan if not git repo
      this.scanDirectory(this.projectRoot, files);
    }
    return files;
  }

  /**
   * Scan directory recursively
   */
  private scanDirectory(dir: string, files: string[]): void {
    try {
      const entries = readFileSync(dir, 'utf-8');
      // Simplified - would need full implementation
    } catch {
      // Ignore unreadable directories
    }
  }

  /**
   * Check file contrare một signal cụ thể
   */
  private checkSignal(filePath: string, signal: typeof SIGNALS[keyof typeof SIGNALS]): boolean {
    const fileName = filePath.split('/').pop() || '';
    const dirPath = dirname(filePath);

    if (signal.pattern instanceof RegExp) {
      // Check against full path
      return signal.pattern.test(filePath) || signal.pattern.test(fileName);
    }

    // String pattern - exact match cho filename
    return fileName === signal.pattern;
  }

  /**
   * Tính mtime lớn nhất của tất cả files được tham chiếu
   */
  private getMaxMtime(files: string[]): number {
    let maxMtime = 0;
    for (const file of files) {
      try {
        const fullPath = join(this.projectRoot, file);
        if (existsSync(fullPath)) {
          const mtime = statSync(fullPath).mtimeMs;
          if (mtime > maxMtime) maxMtime = mtime;
        }
      } catch {
        // File có thể đã bị xóa
      }
    }
    return maxMtime;
  }

  /**
   * Main detection algorithm
   */
  detectPlatform(): DetectionResult {
    // Check cache first
    if (this.cache && this.isCacheValid()) {
      return this.cache.result;
    }

    const changedFiles = this.getChangedFiles();
    const matchedSignals: Array<{ file: string; signal: string; weight: number }> = [];
    let totalWeight = 0;

    // Count wrangler.toml occurrences for boost calculation
    const wranglerFiles = changedFiles.filter(f => f.includes('wrangler.toml'));
    const hasMultipleWrangler = wranglerFiles.length > 1;

    // Score each file
    for (const file of changedFiles) {
      // Check standard signals
      for (const [signalName, signal] of Object.entries(SIGNALS)) {
        if (this.checkSignal(file, signal)) {
          // Tránh double-counting cùng một signal trên cùng file
          const alreadyMatched = matchedSignals.some(
            m => m.file === file && m.signal === signalName
          );
          if (!alreadyMatched) {
            totalWeight += signal.weight;
            matchedSignals.push({ file, signal: signalName, weight: signal.weight });
          }
        }
      }

      // Special handling: check wrangler.toml content for pages_build_output_dir
      if (file.endsWith('wrangler.toml')) {
        try {
          const fullPath = join(this.projectRoot, file);
          const content = readFileSync(fullPath, 'utf-8');
          if (content.includes('pages_build_output_dir')) {
            const alreadyHasPagesSignal = matchedSignals.some(m => m.signal === 'PAGES_BUILD_DIR');
            if (!alreadyHasPagesSignal) {
              totalWeight += SIGNALS.PAGES_BUILD_DIR.weight;
              matchedSignals.push({ file, signal: 'PAGES_BUILD_DIR', weight: SIGNALS.PAGES_BUILD_DIR.weight });
            }
          }
        } catch {
          // Ignore read errors
        }
      }

      // Special handling: check package.json for @cloudflare/workers
      if (file.endsWith('package.json')) {
        try {
          const fullPath = join(this.projectRoot, file);
          const content = readFileSync(fullPath, 'utf-8');
          if (content.includes('@cloudflare/workers') || content.includes('"@cloudflare/workers"')) {
            const alreadyHasPkgSignal = matchedSignals.some(m => m.signal === 'CLOUDFLARE_PKG');
            if (!alreadyHasPkgSignal) {
              totalWeight += SIGNALS.CLOUDFLARE_PKG.weight;
              matchedSignals.push({ file, signal: 'CLOUDFLARE_PKG', weight: SIGNALS.CLOUDFLARE_PKG.weight });
            }
          }
        } catch {
          // Ignore read errors
        }
      }
    }

    // Apply multiple wrangler.toml boost
    if (hasMultipleWrangler) {
      totalWeight += MULTIPLE_WRANGLER_BOOST;
      matchedSignals.push({
        file: wranglerFiles.join(', '),
        signal: 'MULTIPLE_WRANGLER_BOOST',
        weight: MULTIPLE_WRANGLER_BOOST,
      });
    }

    // Check branch name for boost
    const currentBranch = this.getCurrentBranch();
    if (currentBranch.startsWith('cf/') || currentBranch.includes('cloudflare')) {
      totalWeight += BRANCH_BOOST;
      matchedSignals.push({
        file: 'git branch',
        signal: 'BRANCH_NAME_BOOST',
        weight: BRANCH_BOOST,
      });
    }

    // Normalize confidence using fixed max score
    const confidence = Math.min(1, totalWeight / MAX_CONFIDENCE_SCORE);

    // Classify platform
    let platform: 'cloudflare' | 'mixed' | 'other';
    if (confidence >= this.threshold) {
      platform = 'cloudflare';
    } else if (confidence >= 0.3) {
      platform = 'mixed';
    } else {
      platform = 'other';
    }

    const result: DetectionResult = {
      platform,
      confidence: Math.max(0, confidence),
      files: matchedSignals.map(m => m.file),
      debug: {
        totalWeight,
        maxPossibleWeight: MAX_CONFIDENCE_SCORE,
        matchedSignals,
      },
    };

    // Update cache
    this.cache = {
      mtime: this.getMaxMtime(matchedSignals.map(m => m.file)),
      result,
    };
    this.cacheKey = this.computeCacheKey();

    return result;
  }

  /**
   * Force refresh detection bỏ qua cache
   */
  refresh(): DetectionResult {
    this.cache = null;
    return this.detectPlatform();
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache = null;
  }

  /**
   * Check nếu project hiện tại là Cloudflare-only
   */
  isCloudflareOnly(): boolean {
    return this.detectPlatform().platform === 'cloudflare';
  }

  /**
   * Get confidence threshold hiện tại
   */
  getThreshold(): number {
    return this.threshold;
  }

  /**
   * Set custom threshold (1-0)
   */
  setThreshold(threshold: number): void {
    if (threshold < 0 || threshold > 1) {
      throw new Error('Threshold phải nằm trong khoảng [0, 1]');
    }
    // @ts-expect-error - dynamic threshold adjustment
    this.threshold = threshold;
  }
}

export default PlatformDetector;
