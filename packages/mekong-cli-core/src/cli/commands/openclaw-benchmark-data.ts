/**
 * openclaw-benchmark-data.ts — Benchmark history data, formatting helpers, and leaderboard/export views.
 */
import { success, info, warn, heading, keyValue, divider } from '../ui/output.js';

export type BenchSuite = 'basic' | 'full';
export type ExportFormat = 'json' | 'csv' | 'md';

export interface BenchRun {
  id: string;
  date: string;
  suite: BenchSuite;
  scores: { reasoning: number; codeGen: number; planning: number; memory: number };
  total: number;
  durationSec: number;
}

export const BENCH_HISTORY: BenchRun[] = [
  { id: 'run_5', date: '2026-03-22 08:00', suite: 'full', scores: { reasoning: 91, codeGen: 88, planning: 84, memory: 79 }, total: 86, durationSec: 312 },
  { id: 'run_4', date: '2026-03-21 20:00', suite: 'full', scores: { reasoning: 89, codeGen: 85, planning: 82, memory: 76 }, total: 83, durationSec: 318 },
  { id: 'run_3', date: '2026-03-20 08:00', suite: 'full', scores: { reasoning: 88, codeGen: 87, planning: 80, memory: 74 }, total: 82, durationSec: 325 },
  { id: 'run_2', date: '2026-03-19 08:00', suite: 'basic', scores: { reasoning: 85, codeGen: 83, planning: 78, memory: 71 }, total: 79, durationSec: 148 },
  { id: 'run_1', date: '2026-03-18 08:00', suite: 'basic', scores: { reasoning: 82, codeGen: 80, planning: 75, memory: 68 }, total: 76, durationSec: 152 },
];

export const BENCH_CATEGORIES = [
  { name: 'reasoning', goal: 'Analyze and explain the business model' },
  { name: 'code-gen', goal: 'Generate a TypeScript utility function' },
  { name: 'planning', goal: 'Create a deployment plan and then execute it' },
  { name: 'memory', goal: 'Recall previous mission context' },
] as const;

export function trend(prev: number, curr: number): string {
  if (curr > prev) return '↑';
  if (curr < prev) return '↓';
  return '→';
}

export function scoreLabel(score: number): (text: string) => void {
  if (score >= 85) return success;
  if (score >= 70) return info;
  return warn;
}

export function printScoreRow(label: string, score: number, prev?: number): void {
  const bar = '█'.repeat(Math.round(score / 10)) + '░'.repeat(10 - Math.round(score / 10));
  const trendStr = prev !== undefined ? ` ${trend(prev, score)}` : '';
  const line = `  ${label.padEnd(14)} ${String(score).padStart(3)}/100  [${bar}]${trendStr}`;
  scoreLabel(score)(line);
}

export function renderLeaderboardView(): void {
  heading('Benchmark Leaderboard — Last 5 Runs');
  divider();

  info('Run ID   Date                 Suite   Reasoning  Code-gen  Planning  Memory  Total');
  info('─'.repeat(88));
  for (let i = 0; i < BENCH_HISTORY.length; i++) {
    const r = BENCH_HISTORY[i];
    const prev = BENCH_HISTORY[i + 1];
    const totalTrend = prev ? trend(prev.total, r.total) : ' ';
    const line = [
      r.id.padEnd(8),
      r.date.padEnd(21),
      r.suite.padEnd(8),
      String(r.scores.reasoning).padStart(9),
      String(r.scores.codeGen).padStart(10),
      String(r.scores.planning).padStart(9),
      String(r.scores.memory).padStart(8),
      `${String(r.total).padStart(6)} ${totalTrend}`,
    ].join('');
    scoreLabel(r.total)(line);
  }

  divider();
  const best = Math.max(...BENCH_HISTORY.map(r => r.total));
  const latest = BENCH_HISTORY[0].total;
  keyValue('Best score', `${best}/100`);
  keyValue('Latest score', `${latest}/100`);
  if (latest === best) success('Current run is the all-time best!');
  else info(`Gap to best: ${best - latest} points`);
  info('');
}

export function renderExportView(opts: { format: string }): void {
  const fmt = ['json', 'csv', 'md'].includes(opts.format) ? (opts.format as ExportFormat) : 'json';
  const filename = `openclaw-benchmarks-${Date.now()}.${fmt}`;

  heading('Export Benchmark Data');
  keyValue('Format', fmt);
  keyValue('Runs exported', `${BENCH_HISTORY.length}`);
  keyValue('Output file', filename);
  divider();

  if (fmt === 'json') {
    info('Sample output:');
    info('  { "runs": [ { "id": "run_5", "total": 86, ... } ] }');
  } else if (fmt === 'csv') {
    info('Sample output:');
    info('  id,date,suite,reasoning,code_gen,planning,memory,total');
    info('  run_5,2026-03-22 08:00,full,91,88,84,79,86');
  } else {
    info('Sample output:');
    info('  | Run   | Date       | Total |');
    info('  | run_5 | 2026-03-22 | 86    |');
  }

  divider();
  success(`Benchmark data exported to: ./${filename}`);
  info('');
}
