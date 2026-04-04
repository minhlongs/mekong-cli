/**
 * billing-logger.ts — Persistent billing ledger for mekong-raas plugin.
 * Appends usage records to data/billing/<YYYY-MM>.jsonl (JSON Lines format).
 * Each line is a self-contained BillingLedgerEntry JSON object.
 */

import { appendFileSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { BillingLedgerEntry, DispatchContext } from './types.js';

/** Portable __dirname for ESM and CJS */
function currentDir(): string {
  if (typeof __dirname !== 'undefined') return __dirname;
  // ESM: derive from import.meta.url
  return dirname(fileURLToPath(import.meta.url));
}

/** Ledger directory relative to repo root. Override via MEKONG_BILLING_DIR env var. */
function getLedgerDir(): string {
  const envDir = process.env['MEKONG_BILLING_DIR'];
  if (envDir) return resolve(envDir);
  // Default: data/billing/ under the repo root (two levels up from plugins/mekong-raas/)
  return resolve(join(currentDir(), '../../data/billing'));
}

/**
 * Get the ledger file path for the current month.
 * File name format: `YYYY-MM.jsonl`
 */
function getLedgerPath(dir: string): string {
  const now = new Date();
  const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  return join(dir, `${month}.jsonl`);
}

/**
 * Ensure the ledger directory exists.
 * Uses mkdirSync with recursive to avoid race conditions.
 */
function ensureDir(dir: string): void {
  try {
    mkdirSync(dir, { recursive: true });
  } catch (err) {
    // Directory already exists or creation failed — surface in log call
    if ((err as NodeJS.ErrnoException).code !== 'EEXIST') throw err;
  }
}

/**
 * Append a billing ledger entry to the current month's JSONL file.
 * Entries are newline-delimited JSON (JSON Lines spec).
 *
 * @param entry - The billing record to persist
 */
export function appendBillingEntry(entry: BillingLedgerEntry): void {
  const dir = getLedgerDir();
  ensureDir(dir);
  const filePath = getLedgerPath(dir);
  const line = JSON.stringify(entry) + '\n';
  try {
    appendFileSync(filePath, line, 'utf8');
  } catch (err) {
    // Non-fatal: log to stderr but never crash the dispatch pipeline
    process.stderr.write(`[mekong-raas] billing write failed: ${String(err)}\n`);
  }
}

/**
 * Build a BillingLedgerEntry from dispatch context and outcome data.
 * Call this in after_dispatch once we know success/duration.
 */
export function buildLedgerEntry(
  context: DispatchContext,
  durationMs: number,
  success: boolean,
  remainingCredits: number,
): BillingLedgerEntry {
  return {
    ts: new Date().toISOString(),
    tenantId: context.tenant?.tenantId ?? 'local',
    command: context.command,
    layer: context.layer ?? 'unknown',
    creditsUsed: success ? context.creditsRequired : 0,
    durationMs,
    success,
    remainingCredits,
  };
}

/**
 * Log a completed billing event. Combines build + append.
 * Safe to call for both tenant and local (no-op on local: logs 0 credits).
 */
export function logBillingEvent(
  context: DispatchContext,
  durationMs: number,
  success: boolean,
  remainingCredits: number,
): void {
  // Always log so ops team can audit local usage patterns too
  const entry = buildLedgerEntry(context, durationMs, success, remainingCredits);
  appendBillingEntry(entry);
}
