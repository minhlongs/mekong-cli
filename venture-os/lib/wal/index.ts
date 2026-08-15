/**
 * VentureOS Write-Ahead Log — Public API
 *
 * The WAL is the append-only event log for a venture.
 * Every state change (decision, workflow run, gate check, event) is recorded here.
 * Never truncate, never reorder, never delete.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');

// ─── Event Types (source-of-truth schema) ────────────────────────────────────

export interface WALEvent {
  ts: string;           // ISO-8601 timestamp (UTC, replace ':' → '-')
  type: string;         // event type: workflow_run, decision, gate_check, etc.
  payload: Record<string, unknown>;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Append a single event to the WAL file for a venture.
 * Creates the wal/ directory if it doesn't exist.
 *
 * @param ventureId — e.g. `saas-2026-ai-chatbot-platform`
 * @param event — event to append
 */
export function append(ventureId: string, event: Omit<WALEvent, 'ts'>): void {
  const walDir = join(ROOT, 'ventures', ventureId, 'wal');
  const walPath = join(walDir, 'current.jsonl');
  if (!existsSync(walDir)) mkdirSync(walDir, { recursive: true });

  const fullEvent: WALEvent = {
    ...event,
    ts: new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_'),
  };

  writeFileSync(walPath, JSON.stringify(fullEvent) + '\n', { flag: 'a' });
}

/**
 * Read all events from the WAL.
 * Returns events in chronological order (append-only).
 */
export function read(ventureId: string): WALEvent[] {
  const walPath = join(ROOT, 'ventures', ventureId, 'wal', 'current.jsonl');
  if (!existsSync(walPath)) return [];

  const content = readFileSync(walPath, 'utf-8');
  const events: WALEvent[] = [];
  for (const line of content.split('\n').filter(l => l.trim())) {
    try {
      events.push(JSON.parse(line) as WALEvent);
    } catch {
      // skip malformed lines (should never happen in append-only WAL)
    }
  }
  return events;
}

/**
 * Replay the WAL to reconstruct venture state.
 * Returns events with a derived `index` field for ordering.
 * This is the recovery mechanism — if state.json is corrupted,
 * replay the WAL to rebuild.
 */
export function replay(ventureId: string): Array<WALEvent & { index: number }> {
  const events = read(ventureId);
  return events.map((e, i) => ({ ...e, index: i }));
}

/**
 * Event counts by type — used for state.json counters.
 */
export function countByType(ventureId: string): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const e of read(ventureId)) {
    counts[e.type] = (counts[e.type] || 0) + 1;
  }
  return counts;
}

/**
 * Total event count — mirrors WAL line count.
 */
export function totalEvents(ventureId: string): number {
  return read(ventureId).length;
}

/**
 * WAL file info for monitoring/management.
 */
export function info(ventureId: string): { path: string; exists: boolean; lineCount: number; sizeBytes: number } {
  const walPath = join(ROOT, 'ventures', ventureId, 'wal', 'current.jsonl');
  if (!existsSync(walPath)) {
    return { path: walPath, exists: false, lineCount: 0, sizeBytes: 0 };
  }
  const content = readFileSync(walPath, 'utf-8');
  return {
    path: walPath,
    exists: true,
    lineCount: content.split('\n').filter(l => l.trim()).length,
    sizeBytes: Buffer.byteLength(content, 'utf-8'),
  };
}
