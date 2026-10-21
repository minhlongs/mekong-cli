import { existsSync, statSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';
import {
  MAX_CONFIDENCE_SCORE,
  scoreChangedFiles,
  type MatchedSignal,
} from './platform-signals.js';

export interface DetectionResult {
  platform: 'cloudflare' | 'mixed' | 'other';
  confidence: number;
  files: string[];
  debug?: {
    totalWeight: number;
    maxPossibleWeight: number;
    matchedSignals: MatchedSignal[];
  };
}

interface CacheEntry {
  mtime: number;
  result: DetectionResult;
}

/** PlatformDetector - Phát hiện Cloudflare-only mode bằng weighted scoring */
export class PlatformDetector {
  private cache: CacheEntry | null = null;
  private cacheKey: string;
  private readonly projectRoot: string;
  private threshold = 0.7;

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
    this.cacheKey = this.computeCacheKey();
  }

  private execGit(cmd: string): string {
    return execSync(cmd, { cwd: this.projectRoot, encoding: 'utf-8' });
  }

  private getCurrentBranch(): string {
    try {
      return this.execGit('git rev-parse --abbrev-ref HEAD').trim();
    } catch {
      return '';
    }
  }

  private computeCacheKey(): string {
    try {
      const staged = this.execGit('git diff --cached --name-only').split('\n').filter(Boolean).sort().join('|');
      const unstaged = this.execGit('git diff --name-only').split('\n').filter(Boolean).sort().join('|');
      const head = this.execGit('git rev-parse HEAD').trim();
      return `${head}:${staged}:${unstaged}`;
    } catch {
      return `no-git:${this.projectRoot}`;
    }
  }

  private isCacheValid(): boolean {
    return Boolean(this.cache && this.computeCacheKey() === this.cacheKey);
  }

  private getChangedFiles(): string[] {
    try {
      const staged = this.execGit('git diff --cached --name-only');
      const unstaged = this.execGit('git diff --name-only');
      const files = new Set<string>();
      staged.split('\n').filter(Boolean).forEach(f => files.add(f));
      unstaged.split('\n').filter(Boolean).forEach(f => files.add(f));
      return Array.from(files);
    } catch {
      return this.scanAllFiles();
    }
  }

  private scanAllFiles(): string[] {
    try {
      return this.execGit('git ls-files').split('\n').filter(Boolean);
    } catch {
      return [];
    }
  }

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
        // File may have been deleted
      }
    }
    return maxMtime;
  }

  detectPlatform(): DetectionResult {
    if (this.cache && this.isCacheValid()) return this.cache.result;

    const changedFiles = this.getChangedFiles();
    const { totalWeight, matchedSignals } = scoreChangedFiles(
      this.projectRoot,
      changedFiles,
      this.getCurrentBranch(),
    );

    const confidence = Math.min(1, totalWeight / MAX_CONFIDENCE_SCORE);
    const platform: 'cloudflare' | 'mixed' | 'other' =
      confidence >= this.threshold ? 'cloudflare' : confidence >= 0.3 ? 'mixed' : 'other';

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

    this.cache = { mtime: this.getMaxMtime(matchedSignals.map(m => m.file)), result };
    this.cacheKey = this.computeCacheKey();
    return result;
  }

  refresh(): DetectionResult {
    this.cache = null;
    return this.detectPlatform();
  }

  clearCache(): void {
    this.cache = null;
  }

  isCloudflareOnly(): boolean {
    return this.detectPlatform().platform === 'cloudflare';
  }

  getThreshold(): number {
    return this.threshold;
  }

  setThreshold(threshold: number): void {
    if (threshold < 0 || threshold > 1) {
      throw new Error('Threshold phải nằm trong khoảng [0, 1]');
    }
    this.threshold = threshold;
  }
}

export default PlatformDetector;
