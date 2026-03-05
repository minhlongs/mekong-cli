/**
 * Idempotency Middleware for Webhook Events
 *
 * Prevents duplicate webhook processing using event_id deduplication.
 * In-memory store (Phase 2) → Redis-backed (Phase 3)
 *
 * OWASP A08:2021 Data Integrity
 */

export interface IdempotencyRecord {
  eventId: string;
  processedAt: number;
  result?: unknown;
}

export class IdempotencyStore {
  private readonly store = new Map<string, IdempotencyRecord>();
  private readonly ttlMs: number;

  constructor(ttlMs: number = 24 * 60 * 60 * 1000) { // 24 hours default
    this.ttlMs = ttlMs;
  }

  /**
   * Check if event_id was already processed
   * Returns existing result if duplicate, null if first time
   */
  async check(eventId: string): Promise<unknown | null> {
    const record = this.store.get(eventId);

    if (!record) {
      return null;
    }

    // Check TTL
    if (Date.now() - record.processedAt > this.ttlMs) {
      this.store.delete(eventId);
      return null;
    }

    return record.result;
  }

  /**
   * Mark event as processed with result
   */
  async markProcessed(eventId: string, result?: unknown): Promise<void> {
    this.store.set(eventId, {
      eventId,
      processedAt: Date.now(),
      result,
    });
  }

  /**
   * Remove expired entries (call periodically)
   */
  cleanup(): number {
    const now = Date.now();
    let removed = 0;

    for (const [key, record] of this.store.entries()) {
      if (now - record.processedAt > this.ttlMs) {
        this.store.delete(key);
        removed++;
      }
    }

    return removed;
  }

  /**
   * Clear all records (for tests)
   */
  clear(): void {
    this.store.clear();
  }

  /**
   * Get store size (for monitoring)
   */
  size(): number {
    return this.store.size;
  }
}

/**
 * Middleware factory for idempotency check
 * Usage: fastify.addHook('preHandler', idempotencyMiddleware(store))
 */
export function idempotencyMiddleware(store: IdempotencyStore) {
  return async function idempotencyCheck(request: any, reply: any) {
    // Only apply to webhook route
    if (!request.url.includes('/webhook')) {
      return;
    }

    const eventId = request.body?.event_id;

    if (!eventId) {
      // No event_id — allow through (logging only)
      request.log?.warn({ url: request.url }, 'Webhook missing event_id');
      return;
    }

    // Check if already processed
    const existingResult = await store.check(eventId);

    if (existingResult !== null) {
      request.log?.info({ eventId }, 'Duplicate webhook event — returning cached result');
      return reply.send(existingResult);
    }

    // Mark as "processing" to prevent race condition
    await store.markProcessed(eventId, { success: true, message: 'Processing...' });
  };
}

/**
 * Response interceptor to cache actual result
 */
export function createIdempotencyResponseHandler(store: IdempotencyStore) {
  return async function cacheResult(request: any, _reply: any, payload: any) {
    if (!request.url.includes('/webhook')) {
      return payload;
    }

    const eventId = request.body?.event_id;

    if (eventId && payload) {
      await store.markProcessed(eventId, payload);
    }

    return payload;
  };
}

// Singleton instance for application-wide use
let defaultIdempotencyStore: IdempotencyStore | null = null;

export function getDefaultIdempotencyStore(ttlMs?: number): IdempotencyStore {
  if (!defaultIdempotencyStore) {
    defaultIdempotencyStore = new IdempotencyStore(ttlMs);
  }
  return defaultIdempotencyStore;
}
