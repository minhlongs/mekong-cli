/**
 * NOWPaymentsClient — NOWPayments API client using native fetch.
 * Supports checkSubscription, listProducts with retry + backoff.
 * Migrated from Polar.sh to NOWPayments.
 */
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { PolarProduct, PolarSubscription } from './types.js';

const NOWPAYMENTS_API_BASE = 'https://api.nowpayments.io';
const DEFAULT_TIMEOUT_MS = 10_000;
const MAX_RETRIES = 3;
const BASE_BACKOFF_MS = 500;

export interface PolarClientOptions {
  apiKey: string;
  baseUrl?: string;
  timeoutMs?: number;
  maxRetries?: number;
}

export interface SubscriptionCheckResult {
  customerId: string;
  active: boolean;
  subscription?: PolarSubscription;
}

export class PolarClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;

  constructor(opts: PolarClientOptions) {
    this.apiKey = opts.apiKey;
    this.baseUrl = opts.baseUrl ?? NOWPAYMENTS_API_BASE;
    this.timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.maxRetries = opts.maxRetries ?? MAX_RETRIES;
  }

  /** Check if a customer has an active subscription */
  async checkSubscription(customerId: string): Promise<Result<SubscriptionCheckResult, Error>> {
    const result = await this.fetchWithRetry<{ data: PolarSubscription[]; total: number }>(
      `/v1/subscriptions?customer_id=${encodeURIComponent(customerId)}&status=active`,
    );
    if (!result.ok) return result;

    const items = result.value.data ?? [];
    const active = items.filter((s) => s.status === 'active');

    return ok({
      customerId,
      active: active.length > 0,
      subscription: active[0],
    });
  }

  /** List all products */
  async listProducts(): Promise<Result<PolarProduct[], Error>> {
    const result = await this.fetchWithRetry<{ data: PolarProduct[] }>(
      '/v1/currencies',
    );
    if (!result.ok) return result;
    return ok(result.value.data ?? []);
  }

  /**
   * Get a specific payment by ID.
   * @param subscriptionId - NOWPayments payment ID
   */
  async getSubscription(subscriptionId: string): Promise<Result<PolarSubscription, Error>> {
    return this.fetchWithRetry<PolarSubscription>(
      `/v1/payment/${encodeURIComponent(subscriptionId)}`,
    );
  }

  // ── Internal fetch with retry ──────────────────────────────────────────────

  private async fetchWithRetry<T>(path: string, attempt = 0): Promise<Result<T, Error>> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        headers: {
          'x-api-key': this.apiKey,
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timer);

      // Rate limit — retry with backoff
      if (response.status === 429 && attempt < this.maxRetries) {
        const retryAfter = parseInt(response.headers.get('retry-after') ?? '1', 10);
        const delayMs = Math.max(retryAfter * 1000, BASE_BACKOFF_MS * 2 ** attempt);
        await sleep(delayMs);
        return this.fetchWithRetry<T>(path, attempt + 1);
      }

      if (!response.ok) {
        const body = await response.text().catch(() => '');
        return err(new Error(`NOWPayments API error ${response.status}: ${body}`));
      }

      const data = (await response.json()) as T;
      return ok(data);
    } catch (e) {
      clearTimeout(timer);
      const isAbort = e instanceof Error && e.name === 'AbortError';
      if (!isAbort && attempt < this.maxRetries) {
        const delayMs = BASE_BACKOFF_MS * 2 ** attempt;
        await sleep(delayMs);
        return this.fetchWithRetry<T>(path, attempt + 1);
      }
      return err(new Error(`NOWPayments API request failed: ${String(e)}`));
    }
  }
}

/**
 * Create a PolarClient (NOWPayments backend) from environment variables.
 * @returns error if `NOWPAYMENTS_API_KEY` is not set
 */
export function createPolarClientFromEnv(baseUrl?: string): Result<PolarClient, Error> {
  const apiKey = process.env['NOWPAYMENTS_API_KEY'];
  if (!apiKey) {
    return err(new Error('NOWPAYMENTS_API_KEY environment variable not set'));
  }
  return ok(new PolarClient({ apiKey, baseUrl }));
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
