/** In-memory event bus for live dashboard updates. Bounded history (max 1000 events). */

export type EventHandler = (data: unknown) => void;

export interface EventRecord {
  event: string;
  data: unknown;
  timestamp: number;
}

const MAX_HISTORY = 1000;

/** Known dashboard event names. */
export type DashboardEvent =
  | "pane:status"
  | "task:created"
  | "task:completed"
  | "raas:credit"
  | "agi:evolved";

/** Pub/sub event bus with bounded in-memory history. Thread-safe for single-process use. */
export class DashboardEventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private history: EventRecord[] = [];

  /** Subscribe to an event. */
  on(event: string, handler: EventHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
  }

  /** Unsubscribe a handler. No-op if not registered. */
  off(event: string, handler: EventHandler): void {
    this.handlers.get(event)?.delete(handler);
  }

  /** Emit an event, synchronously invoking all registered handlers. */
  emit(event: string, data: unknown): void {
    const record: EventRecord = { event, data, timestamp: Date.now() };

    // Evict oldest when at capacity
    if (this.history.length >= MAX_HISTORY) {
      this.history.shift();
    }
    this.history.push(record);

    const handlers = this.handlers.get(event);
    if (handlers) {
      for (const handler of handlers) {
        try {
          handler(data);
        } catch {
          // Isolate handler errors — one bad subscriber must not break others
        }
      }
    }
  }

  /**
   * Retrieve event history.
   * @param event - Filter to a specific event type; omit for all events.
   * @param limit - Maximum number of records to return (most recent first).
   */
  getHistory(event?: string, limit?: number): EventRecord[] {
    let records = event
      ? this.history.filter((r) => r.event === event)
      : [...this.history];

    // Most recent first
    records = records.reverse();

    return limit !== undefined ? records.slice(0, limit) : records;
  }

  /** Remove all handlers and clear history. */
  clear(): void {
    this.handlers.clear();
    this.history = [];
  }

  /** Number of events stored in history. */
  get historySize(): number {
    return this.history.length;
  }
}
