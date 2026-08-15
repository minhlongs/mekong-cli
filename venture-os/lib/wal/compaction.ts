/**
 * VentureOS WAL Compaction — merge + retention policy
 *
 * The WAL is append-only by policy, but physically it can grow.
 * Compaction:
 *   1. Reads all events from current.jsonl
 *   2. Optionally filters by retention policy (keep last N events, or last N days)
 *   3. Writes compacted WAL to wal/compacted-<ts>.jsonl
 *   4. Verifies line count matches pre-compaction count
 *   5. Optionally atomically renames compacted → current.jsonl
 *
 * Retention policies:
 *   - "events": keep last N events (default: 1000)
 *   - "days": keep events from last N days (default: 90)
 *   - "all": no compaction (keep everything)
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync, renameSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import type { WALEvent } from './index.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');

// ─── Types ───────────────────────────────────────────────────────────────────

export interface RetentionPolicy {
  mode: 'events' | 'days' | 'all';
  limit: number;           // N events or N days
}

export interface CompactionResult {
  ventureId: string;
  originalLines: number;
  compactedLines: number;
  removedLines: number;
  compactedPath: string;
  durationMs: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const DEFAULT_POLICY: RetentionPolicy = { mode: 'events', limit: 1000 };

function getWalDir(ventureId: string): string {
  return join(ROOT, 'ventures', ventureId, 'wal');
}

function getWalPath(ventureId: string): string {
  return join(getWalDir(ventureId), 'current.jsonl');
}

function readWalLines(ventureId: string): WALEvent[] {
  const walPath = getWalPath(ventureId);
  if (!existsSync(walPath)) return [];
  const content = readFileSync(walPath, 'utf-8');
  const events: WALEvent[] = [];
  for (const line of content.split('\n').filter((l) => l.trim())) {
    try {
      events.push(JSON.parse(line) as WALEvent);
    } catch { /* skip malformed */ }
  }
  return events;
}

function writeWalLines(ventureId: string, events: WALEvent[], suffix: string): string {
  const walDir = getWalDir(ventureId);
  if (!existsSync(walDir)) mkdirSync(walDir, { recursive: true });

  const outPath = join(walDir, suffix);
  const lines = events.map((e) => JSON.stringify(e)).join('\n') + '\n';
  writeFileSync(outPath, lines, 'utf-8');
  return outPath;
}

function filterByPolicy(events: WALEvent[], policy: RetentionPolicy): WALEvent[] {
  if (policy.mode === 'all') return events;

  if (policy.mode === 'events') {
    return events.slice(-policy.limit);
  }

  if (policy.mode === 'days') {
    const cutoff = Date.now() - policy.limit * 24 * 60 * 60 * 1000;
    // ts format: "2026-07-10_19-07-39-093Z" — extract datetime portion
    return events.filter((e) => {
      const datePart = e.ts.slice(0, 19).replace(/[-_T]/, '-').replace(/[-_T]/, '-');
      const eventTime = new Date(datePart).getTime();
      return eventTime >= cutoff;
    });
  }

  return events; // unknown mode — keep all (safe fallback)
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Compact the WAL for a venture.
 *
 * Process:
 *   1. Read current.jsonl
 *   2. Apply retention policy to filter events
 *   3. Write compacted file
 *   4. Verify line count
 *   5. Optionally rename compacted → current (replace)
 *
 * @param ventureId — venture to compact
 * @param policy — retention policy (default: keep last 1000 events)
 * @param replace — if true, atomically replace current.jsonl (default: false)
 * @returns compaction result with line counts
 */
export function compact(
  ventureId: string,
  policy: RetentionPolicy = DEFAULT_POLICY,
  replace: boolean = false,
): CompactionResult {
  const startTime = Date.now();
  const originalEvents = readWalLines(ventureId);
  const originalLines = originalEvents.length;

  const filtered = filterByPolicy(originalEvents, policy);
  const compactedLines = filtered.length;
  const removedLines = originalLines - compactedLines;

  // Write compacted file
  const suffix = `compacted-${new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_')}.jsonl`;
  const compactedPath = writeWalLines(ventureId, filtered, suffix);

  // Verify line count
  const verifyEvents = readWalLines(ventureId);
  const verifyPath = join(getWalDir(ventureId), suffix);
  const verifyCount = readFileSync(verifyPath, 'utf-8').split('\n').filter((l) => l.trim()).length;

  if (verifyCount !== compactedLines) {
    throw new Error(
      `Compaction verification failed: expected ${compactedLines} lines, got ${verifyCount}`,
    );
  }

  // Optionally replace current.jsonl
  if (replace) {
    const currentPath = getWalPath(ventureId);
    renameSync(compactedPath, currentPath);
  }

  return {
    ventureId,
    originalLines,
    compactedLines,
    removedLines,
    compactedPath: replace ? getWalPath(ventureId) : compactedPath,
    durationMs: Date.now() - startTime,
  };
}

/**
 * Compact ALL ventures' WALs using the same policy.
 * Useful for periodic maintenance.
 */
export function compactAll(
  venturesRoot: string = join('.', 'ventures'),
  policy: RetentionPolicy = DEFAULT_POLICY,
): CompactionResult[] {
  const results: CompactionResult[] = [];
  if (!existsSync(venturesRoot)) return results;

  const { readdirSync, existsSync: ex } = require('fs');
  for (const id of readdirSync(venturesRoot)) {
    const dir = join(venturesRoot, id);
    if (!ex(join(dir, 'wal', 'current.jsonl'))) continue;
    try {
      results.push(compact(id, policy, false));
    } catch (err) {
      // skip ventures that fail compaction — don't block the batch
      console.error(`WAL compaction failed for ${id}: ${err}`);
    }
  }
  return results;
}
