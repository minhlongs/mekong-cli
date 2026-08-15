/**
 * MeteringCollector — buffer usage events and flush to store.
 * Flushes at 50 events or every 30 seconds (whichever comes first).
 */
import { randomUUID } from 'node:crypto';
import { MeteringStore } from './store.js';
import type { UsageEvent, UsageCategory } from './types.js';

const FLUSH_THRESHOLD = 50;
const FLUSH_INTERVAL_MS = 30_000;

export class MeteringCollector {
  private buffer: UsageEvent[] = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private flushing = false;

  constructor(private readonly store: MeteringStore) {}

  /** Record an arbitrary usage event */
  record(event: Omit<UsageEvent, 'id' | 'timestamp'> & { timestamp?: string }): void {
    const full: UsageEvent = {
      id: randomUUID(),
      timestamp: event.timestamp ?? new Date().toISOString(),
      ...event,
    };
    this.buffer.push(full);
    this.scheduleFlush();
    if (this.buffer.length >= FLUSH_THRESHOLD) {
      void this.flush();
    }
  }

  /** Convenience: record an LLM call */
  recordLlmCall(opts: {
    provider: string;
    model: string;
    inputTokens: number;
    outputTokens: number;
    durationMs?: number;
    estimatedCost?: number;
  }): void {
    this.record({
      category: 'llm_call',
      provider: opts.provider,
      model: opts.model,
      inputTokens: opts.inputTokens,
      outputTokens: opts.outputTokens,
      durationMs: opts.durationMs,
      estimatedCost: opts.estimatedCost,
    });
  }

  /** Convenience: record a tool execution */
  recordToolRun(opts: {
    name: string;
    durationMs?: number;
    success?: boolean;
  }): void {
    this.record({
      category: 'tool_run',
      resourceName: opts.name,
      durationMs: opts.durationMs,
      metadata: opts.success !== undefined ? { success: opts.success } : undefined,
    });
  }

  /** Convenience: record a SOP execution */
  recordSopRun(opts: {
    name: string;
    durationMs?: number;
    success?: boolean;
  }): void {
    this.record({
      category: 'sop_run',
      resourceName: opts.name,
      durationMs: opts.durationMs,
      metadata: opts.success !== undefined ? { success: opts.success } : undefined,
    });
  }

  /** Flush all buffered events to the store */
  async flush(): Promise<void> {
    if (this.flushing || this.buffer.length === 0) return;
    this.flushing = true;
    const batch = this.buffer.splice(0, this.buffer.length);
    try {
      await this.store.appendBatch(batch);
    } finally {
      this.flushing = false;
    }
  }

  /** Stop the background timer and flush remaining events */
  async shutdown(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    await this.flush();
  }

  /** Current buffer size (for testing) */
  get bufferSize(): number {
    return this.buffer.length;
  }

  /** Count events by category in buffer (for testing) */
  countByCategory(category: UsageCategory): number {
    let count = 0;
    for (const e of this.buffer) {
      if (e.category === category) count++;
    }
    return count;
  }

  private scheduleFlush(): void {
    if (this.timer) return;
    this.timer = setTimeout(() => {
      this.timer = null;
      void this.flush();
    }, FLUSH_INTERVAL_MS);
    // Don't block Node exit
    if (this.timer.unref) this.timer.unref();
  }
}
