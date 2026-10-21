import { readFileSync } from 'fs';
import { join } from 'path';

/**
 * Signals to detect Cloudflare-only mode with corresponding weights.
 * Confidence is computed as totalWeight / MAX_CONFIDENCE_SCORE (5.0).
 */
export const SIGNALS = {
  WRANGLER_TOML: { weight: 2.0, pattern: 'wrangler.toml' },
  WORKER_FILE: { weight: 1.0, pattern: /(^|\/)(worker|index)\.(ts|js)$/ },
  CLOUDFLARE_PKG: { weight: 1.0, pattern: /^@cloudflare\// },
  CLOUDFLARE_DIR: { weight: 0.5, pattern: /^cloudflare\// },
  CLOUDFLARE_PAGES: { weight: 4.0, pattern: /^pages\// },
  PAGES_BUILD_DIR: { weight: 1.0, pattern: 'pages_build_output_dir' },
  CF_BRANCH: { weight: 0.5, pattern: /^cf\// },
} as const;

export const MAX_CONFIDENCE_SCORE = 5.0;
export const BRANCH_BOOST = 0.15 * MAX_CONFIDENCE_SCORE;
export const MULTIPLE_WRANGLER_BOOST = 0.2 * MAX_CONFIDENCE_SCORE;

export interface MatchedSignal {
  file: string;
  signal: string;
  weight: number;
}

export function checkFileSignal(
  filePath: string,
  signal: (typeof SIGNALS)[keyof typeof SIGNALS],
): boolean {
  const fileName = filePath.split('/').pop() || '';
  if (signal.pattern instanceof RegExp) {
    return signal.pattern.test(filePath) || signal.pattern.test(fileName);
  }
  return fileName === signal.pattern;
}

export function scoreChangedFiles(
  projectRoot: string,
  changedFiles: string[],
  currentBranch: string,
): { totalWeight: number; matchedSignals: MatchedSignal[] } {
  const matchedSignals: MatchedSignal[] = [];
  let totalWeight = 0;

  const wranglerFiles = changedFiles.filter(f => f.includes('wrangler.toml'));
  const hasMultipleWrangler = wranglerFiles.length > 1;

  for (const file of changedFiles) {
    for (const [signalName, signal] of Object.entries(SIGNALS)) {
      if (checkFileSignal(file, signal)) {
        const alreadyMatched = matchedSignals.some(
          m => m.file === file && m.signal === signalName,
        );
        if (!alreadyMatched) {
          totalWeight += signal.weight;
          matchedSignals.push({ file, signal: signalName, weight: signal.weight });
        }
      }
    }

    if (file.endsWith('wrangler.toml')) {
      try {
        const content = readFileSync(join(projectRoot, file), 'utf-8');
        if (content.includes('pages_build_output_dir')) {
          if (!matchedSignals.some(m => m.signal === 'PAGES_BUILD_DIR')) {
            totalWeight += SIGNALS.PAGES_BUILD_DIR.weight;
            matchedSignals.push({ file, signal: 'PAGES_BUILD_DIR', weight: SIGNALS.PAGES_BUILD_DIR.weight });
          }
        }
      } catch {
        // Ignore read errors
      }
    }

    if (file.endsWith('package.json')) {
      try {
        const content = readFileSync(join(projectRoot, file), 'utf-8');
        if (content.includes('@cloudflare/workers') || content.includes('"@cloudflare/workers"')) {
          if (!matchedSignals.some(m => m.signal === 'CLOUDFLARE_PKG')) {
            totalWeight += SIGNALS.CLOUDFLARE_PKG.weight;
            matchedSignals.push({ file, signal: 'CLOUDFLARE_PKG', weight: SIGNALS.CLOUDFLARE_PKG.weight });
          }
        }
      } catch {
        // Ignore read errors
      }
    }
  }

  if (hasMultipleWrangler) {
    totalWeight += MULTIPLE_WRANGLER_BOOST;
    matchedSignals.push({
      file: wranglerFiles.join(', '),
      signal: 'MULTIPLE_WRANGLER_BOOST',
      weight: MULTIPLE_WRANGLER_BOOST,
    });
  }

  if (currentBranch.startsWith('cf/') || currentBranch.includes('cloudflare')) {
    totalWeight += BRANCH_BOOST;
    matchedSignals.push({
      file: 'git branch',
      signal: 'BRANCH_NAME_BOOST',
      weight: BRANCH_BOOST,
    });
  }

  return { totalWeight, matchedSignals };
}
