/**
 * ReceiptStore — JSONL storage for payment receipts/events.
 * Idempotent: dedup by event ID.
 * Phase 4 of v0.6 Payment Webhook.
 */
import { appendFile, readFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { WebhookEvent } from './types.js';

export class ReceiptStore {
  /** @param storePath - path to the JSONL receipts file */
  constructor(private readonly storePath: string) {}

  /** Append a webhook event to the receipt log. */
  async append(event: WebhookEvent): Promise<Result<void, Error>> {
    try {
      await mkdir(dirname(this.storePath), { recursive: true });
      await appendFile(this.storePath, JSON.stringify(event) + '\n');
      return ok(undefined);
    } catch (e) {
      return err(new Error(`Failed to write receipt: ${String(e)}`));
    }
  }

  /** Read all persisted webhook events from disk. */
  async readAll(): Promise<Result<WebhookEvent[], Error>> {
    try {
      const content = await readFile(this.storePath, 'utf-8');
      const events = content
        .trim()
        .split('\n')
        .filter((l) => l.trim())
        .map((l) => JSON.parse(l) as WebhookEvent);
      return ok(events);
    } catch (e: unknown) {
      if ((e as NodeJS.ErrnoException).code === 'ENOENT') return ok([]);
      return err(new Error(`Failed to read receipts: ${String(e)}`));
    }
  }

  /** Check if event ID was already processed (idempotency) */
  async hasEvent(eventId: string): Promise<boolean> {
    const result = await this.readAll();
    if (!result.ok) return false;
    return result.value.some((e) => e.id === eventId);
  }

  /**
   * Query events by customer ID.
   * @param customerId - Polar customer ID or email
   */
  async findByCustomer(customerId: string): Promise<Result<WebhookEvent[], Error>> {
    const all = await this.readAll();
    if (!all.ok) return all;
    return ok(all.value.filter((e) => e.customerId === customerId));
  }

  /** Query events within a date range (ISO strings) */
  async findByDateRange(from: string, to: string): Promise<Result<WebhookEvent[], Error>> {
    const all = await this.readAll();
    if (!all.ok) return all;
    const fromMs = new Date(from).getTime();
    const toMs = new Date(to).getTime();
    return ok(
      all.value.filter((e) => {
        const t = new Date(e.receivedAt).getTime();
        return t >= fromMs && t <= toMs;
      }),
    );
  }

  /** Query events by type */
  async findByType(type: WebhookEvent['type']): Promise<Result<WebhookEvent[], Error>> {
    const all = await this.readAll();
    if (!all.ok) return all;
    return ok(all.value.filter((e) => e.type === type));
  }
}
