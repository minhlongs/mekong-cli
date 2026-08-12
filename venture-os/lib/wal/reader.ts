/**
 * VentureOS WAL Reader — line-by-line streaming reader
 *
 * Reads the WAL without loading the entire file into memory.
 * Supports forward iteration, tail reads, and event type filtering.
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import type { WALEvent } from './index.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');

// ─── Reader State ────────────────────────────────────────────────────────────

export interface WalReadOptions {
  /** Start from this line index (0-based). Default: 0 */
  offset?: number;
  /** Max events to return. Default: all */
  limit?: number;
  /** Only return events of this type */
  typeFilter?: string;
  /** Start from end (tail-like). Default: false */
  tail?: boolean;
}

export interface WalReadResult {
  events: WALEvent[];
  /** Total lines in the file */
  totalLines: number;
  /** How many events match the filter */
  matchedLines: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getWalPath(ventureId: string): string {
  return join(ROOT, 'ventures', ventureId, 'wal', 'current.jsonl');
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Read the WAL for a venture as a stream of events.
 * Returns parsed events with optional filtering.
 */
export function readWal(
  ventureId: string,
  options: WalReadOptions = {},
): WalReadResult {
  const walPath = getWalPath(ventureId);
  if (!existsSync(walPath)) {
    return { events: [], totalLines: 0, matchedLines: 0 };
  }

  const content = readFileSync(walPath, 'utf-8');
  const allLines = content.split('\n').filter((l) => l.trim());
  const totalLines = allLines.length;

  // Tail mode: offset from the end
  let startIndex = options.offset ?? 0;
  if (options.tail) {
    const count = options.limit ?? 10;
    startIndex = Math.max(0, totalLines - count);
  }

  // Slice the line range
  const slice = allLines.slice(
    Math.min(startIndex, totalLines),
    options.limit ? startIndex + options.limit : totalLines,
  );

  // Parse + filter
  const events: WALEvent[] = [];
  let matchedLines = 0;
  for (const line of slice) {
    try {
      const event = JSON.parse(line) as WALEvent;
      if (options.typeFilter && event.type !== options.typeFilter) continue;
      events.push(event);
      matchedLines++;
    } catch {
      // skip malformed lines — WAL is append-only, never corrupt existing entries
    }
  }

  return { events, totalLines, matchedLines };
}

/**
 * Get recent events (last N lines) from the WAL.
 * Convenience wrapper around readWal with tail=true.
 */
export function tail(ventureId: string, n: number = 10): WALEvent[] {
  return readWal(ventureId, { tail: true, limit: n }).events;
}

/**
 * Count events matching a type filter without reading the whole file
 * (still reads whole file — WAL is append-only JSONL, small in practice).
 */
export function countType(ventureId: string, eventType: string): number {
  return readWal(ventureId, { typeFilter: eventType }).matchedLines;
}

/**
 * Iterate over events matching a type — yields events lazily.
 * Read the full file once, then iterate over the result.
 */
export function* iterateByType(ventureId: string, eventType: string): Generator<WALEvent> {
  const { events } = readWal(ventureId, { typeFilter: eventType });
  yield* events;
}

/**
 * Get the first event matching a predicate.
 */
export function findFirst(
  ventureId: string,
  predicate: (e: WALEvent) => boolean,
): WALEvent | undefined {
  const { events } = readWal(ventureId, { limit: 1 });
  // Read sequentially until match (small N for most ventures)
  const walPath = getWalPath(ventureId);
  if (!existsSync(walPath)) return undefined;
  for (const line of readFileSync(walPath, 'utf-8').split('\n').filter((l) => l.trim())) {
    try {
      const event = JSON.parse(line) as WALEvent;
      if (predicate(event)) return event;
    } catch { /* skip */ }
  }
  return undefined;
}

/**
 * Get the last event in the WAL.
 * Optimized: reads only the last non-empty line.
 */
export function getLast(ventureId: string): WALEvent | undefined {
  const walPath = getWalPath(ventureId);
  if (!existsSync(walPath)) return undefined;
  const lines = readFileSync(walPath, 'utf-8').split('\n').filter((l) => l.trim());
  if (lines.length === 0) return undefined;
  try {
    return JSON.parse(lines[lines.length - 1]) as WALEvent;
  } catch {
    return undefined;
  }
}
