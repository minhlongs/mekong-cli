/**
 * Shared webhook handling utilities
 * Provides replay attack prevention, timestamp validation, and event tracking
 */

import { handleDb, createError } from '../types/error'

/**
 * D1Database type for webhook operations
 */
export interface WebhookDatabase {
  exec: (sql: string) => Promise<unknown>
  prepare: (query: string) => {
    bind: (...params: unknown[]) => {
      first: () => Promise<unknown>
      run: () => Promise<unknown>
      all: () => Promise<{ results: unknown[] }>
    }
  }
}

/**
 * Ensure webhook_events table exists (idempotent)
 */
export async function ensureWebhookEventsTable(db: WebhookDatabase) {
  await db.exec(`
    CREATE TABLE IF NOT EXISTS webhook_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider TEXT NOT NULL,
      event_id TEXT NOT NULL,
      event_type TEXT,
      received_at INTEGER DEFAULT (unixepoch()),
      UNIQUE(provider, event_id)
    )
  `)
}

/**
 * Check if webhook event already processed (replay attack detection)
 */
export async function isDuplicateWebhookEvent(
  db: WebhookDatabase,
  provider: string,
  eventId: string
): Promise<boolean> {
  const result = await handleDb(
    () => db.prepare(
      'SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?'
    ).bind(provider, eventId).first(),
    'DATABASE_ERROR',
    'Failed to check for duplicate webhook event'
  )
  return !!result
}

/**
 * Record webhook event for replay attack tracking
 */
export async function recordWebhookEvent(
  db: WebhookDatabase,
  provider: string,
  eventId: string,
  type: string
) {
  await handleDb(
    () => db.prepare(
      'INSERT OR IGNORE INTO webhook_events (provider, event_id, event_type) VALUES (?, ?, ?)'
    ).bind(provider, eventId, type).run(),
    'DATABASE_ERROR',
    'Failed to record webhook event'
  )
}

/**
 * Validate webhook timestamp (prevent old replay attacks)
 * Returns true if timestamp is within allowed window
 */
export function isTimestampValid(
  timestamp: number | string,
  windowMs: number = 5 * 60 * 1000 // 5 minutes default
): boolean {
  const eventTime = typeof timestamp === 'string'
    ? Date.parse(timestamp)
    : timestamp
  const now = Date.now()
  const age = Math.abs(now - eventTime)
  return age <= windowMs
}
