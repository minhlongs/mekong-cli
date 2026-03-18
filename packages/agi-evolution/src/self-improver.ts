import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';
import { execSync } from 'node:child_process';

export interface CodebaseAnalysis {
  rootDir: string;
  totalFiles: number;
  totalLines: number;
  filesOver200Loc: string[];
  anyTypeCount: number;
  todoFixmeCount: number;
  consoleLogCount: number;
  scannedAt: Date;
}

export interface RefactoringProposal {
  file: string;
  issue: string;
  suggestion: string;
  priority: 'high' | 'medium' | 'low';
}

function collectTsJsFiles(dir: string, results: string[] = []): string[] {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return results;
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === 'dist' || entry.startsWith('.')) continue;
    const full = join(dir, entry);
    let stat;
    try { stat = statSync(full); } catch { continue; }
    if (stat.isDirectory()) {
      collectTsJsFiles(full, results);
    } else if (['.ts', '.js', '.tsx', '.jsx'].includes(extname(entry))) {
      results.push(full);
    }
  }
  return results;
}

function countOccurrences(filePath: string, pattern: RegExp): number {
  try {
    const content = readFileSync(filePath, 'utf-8');
    return (content.match(pattern) ?? []).length;
  } catch {
    return 0;
  }
}

function countLines(filePath: string): number {
  try {
    const content = readFileSync(filePath, 'utf-8');
    return content.split('\n').length;
  } catch {
    return 0;
  }
}

export function analyzeCodebase(rootDir: string): CodebaseAnalysis {
  const files = collectTsJsFiles(rootDir);
  const filesOver200Loc: string[] = [];
  let totalLines = 0;
  let anyTypeCount = 0;
  let todoFixmeCount = 0;
  let consoleLogCount = 0;

  for (const file of files) {
    const lines = countLines(file);
    totalLines += lines;
    if (lines > 200) filesOver200Loc.push(file);
    anyTypeCount += countOccurrences(file, /:\s*any\b/g);
    todoFixmeCount += countOccurrences(file, /\b(TODO|FIXME)\b/g);
    consoleLogCount += countOccurrences(file, /console\.(log|warn|error|info)\(/g);
  }

  return {
    rootDir,
    totalFiles: files.length,
    totalLines,
    filesOver200Loc,
    anyTypeCount,
    todoFixmeCount,
    consoleLogCount,
    scannedAt: new Date(),
  };
}

export function generateRefactoringProposals(analysis: CodebaseAnalysis): RefactoringProposal[] {
  const proposals: RefactoringProposal[] = [];

  for (const file of analysis.filesOver200Loc) {
    proposals.push({
      file,
      issue: 'File exceeds 200 LOC anti-pattern threshold',
      suggestion: 'Split into smaller focused modules. Extract utility functions and dedicated service classes.',
      priority: 'high',
    });
  }

  if (analysis.anyTypeCount > 0) {
    proposals.push({
      file: analysis.rootDir,
      issue: `${analysis.anyTypeCount} usage(s) of \`any\` type detected`,
      suggestion: 'Replace `any` with proper interfaces or generics. Enable strict null checks.',
      priority: 'high',
    });
  }

  if (analysis.consoleLogCount > 0) {
    proposals.push({
      file: analysis.rootDir,
      issue: `${analysis.consoleLogCount} console.log/warn/error statement(s) found`,
      suggestion: 'Remove all console statements. Use a structured logger instead.',
      priority: 'medium',
    });
  }

  if (analysis.todoFixmeCount > 0) {
    proposals.push({
      file: analysis.rootDir,
      issue: `${analysis.todoFixmeCount} TODO/FIXME comment(s) remain`,
      suggestion: 'Resolve all TODO and FIXME comments or convert to tracked issues.',
      priority: 'low',
    });
  }

  return proposals;
}

export function getQualityScore(analysis: CodebaseAnalysis): number {
  let score = 100;
  if (analysis.totalFiles === 0) return 0;

  const overLocRatio = analysis.filesOver200Loc.length / analysis.totalFiles;
  score -= Math.min(30, Math.round(overLocRatio * 100));
  score -= Math.min(25, analysis.anyTypeCount * 2);
  score -= Math.min(20, analysis.consoleLogCount);
  score -= Math.min(10, analysis.todoFixmeCount);

  return Math.max(0, score);
}
